from app.services import etoro_market_data


def test_maps_our_symbols_to_yahoo():
    assert etoro_market_data.YAHOO_SYMBOL["BTC"] == "BTC-USD"
    assert etoro_market_data.YAHOO_SYMBOL["EURUSD"] == "EURUSD=X"


def test_get_candles_reshapes_and_drops_null_gaps(monkeypatch):
    payload = {
        "chart": {
            "result": [
                {
                    "timestamp": [1000, 2000, 3000],
                    "indicators": {
                        "quote": [
                            {
                                "open": [10, None, 12],   # middle bar is a Yahoo null gap
                                "high": [11, None, 13],
                                "low": [9, None, 11],
                                "close": [10.5, None, 12.5],
                                "volume": [100, None, 120],
                            }
                        ]
                    },
                }
            ]
        }
    }

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return payload

    monkeypatch.setattr(etoro_market_data.httpx, "get", lambda *a, **k: FakeResp())
    rows = etoro_market_data.get_candles("BTC", "1h", limit=200)

    assert len(rows) == 2  # null-gap bar dropped
    assert rows[0] == [1000 * 1000, 10, 11, 9, 10.5, 100]
    assert rows[-1] == [3000 * 1000, 12, 13, 11, 12.5, 120]


def test_get_candles_unknown_symbol_returns_empty():
    assert etoro_market_data.get_candles("NOPE", "1h") == []


def test_get_candles_degrades_to_empty_on_error(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(etoro_market_data.httpx, "get", boom)
    assert etoro_market_data.get_candles("BTC", "1h") == []
