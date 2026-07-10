import time

from app.services import historical_data


class FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _payload(timestamps, closes):
    return {
        "chart": {
            "result": [
                {
                    "timestamp": timestamps,
                    "indicators": {
                        "quote": [
                            {
                                "open": closes,
                                "high": closes,
                                "low": closes,
                                "close": closes,
                                "volume": [1000] * len(closes),
                            }
                        ]
                    },
                }
            ]
        }
    }


def test_get_daily_history_filters_to_requested_window(monkeypatch):
    now = time.time()
    day = 86400
    # One bar 25 years ago (must be dropped for a 20y window), one bar recent.
    timestamps = [int(now - 25 * 365 * day), int(now - day)]
    closes = [50.0, 100.0]
    monkeypatch.setattr(historical_data.httpx, "get", lambda *a, **k: FakeResp(_payload(timestamps, closes)))

    rows = historical_data.get_daily_history("SPY", years=20)

    assert len(rows) == 1
    assert rows[0][4] == 100.0  # close


def test_get_daily_history_drops_null_gaps(monkeypatch):
    now = time.time()
    day = 86400
    timestamps = [int(now - 3 * day), int(now - 2 * day), int(now - day)]
    monkeypatch.setattr(
        historical_data.httpx,
        "get",
        lambda *a, **k: FakeResp(_payload(timestamps, [10.0, None, 12.0])),
    )

    rows = historical_data.get_daily_history("SPY", years=5)

    assert len(rows) == 2  # the None-gap bar is dropped
    assert rows[0][4] == 10.0
    assert rows[1][4] == 12.0


def test_crypto_and_forex_symbols_map_to_yahoo_symbols(monkeypatch):
    """The eToro whitelist can only be backtested if crypto/forex tickers are
    rewritten to their Yahoo chart symbols -- otherwise 'BTC' is sent verbatim
    and Yahoo returns nothing, so the venue is silently un-backtestable."""
    captured = {}
    now = time.time()

    def fake_get(url, params=None, **kwargs):
        captured["url"] = url
        return FakeResp(_payload([int(now - 86400)], [42.0]))

    monkeypatch.setattr(historical_data.httpx, "get", fake_get)

    historical_data.get_daily_history("BTC", years=10)
    assert "BTC-USD" in captured["url"]
    historical_data.get_daily_history("EURUSD", years=10)
    assert "EURUSD=X" in captured["url"]
    # A plain equity ticker is not in the map -> passes through unchanged.
    historical_data.get_daily_history("SPY", years=10)
    assert captured["url"].endswith("/SPY")


def test_get_daily_history_degrades_to_empty_on_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(historical_data.httpx, "get", boom)
    assert historical_data.get_daily_history("SPY", years=20) == []


def test_get_history_for_symbols_skips_failed_symbols_and_batches(monkeypatch):
    now = time.time()
    day = 86400
    timestamps = [int(now - day)]

    def fake_get(url, params=None, **kwargs):
        if "BAD" in url:
            raise RuntimeError("boom")
        return FakeResp(_payload(timestamps, [42.0]))

    monkeypatch.setattr(historical_data.httpx, "get", fake_get)
    out = historical_data.get_history_for_symbols(["SPY", "BAD", "QQQ"], years=20, delay=0)

    assert set(out.keys()) == {"SPY", "QQQ"}
    assert out["SPY"][0][4] == 42.0
