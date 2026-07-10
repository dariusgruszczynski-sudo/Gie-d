import pytest

from app.services.etoro_client import EToroClient, EToroAPIError


@pytest.fixture
def etoro_settings(settings):
    return settings.model_copy(update={"etoro_api_key": "pub", "etoro_user_key": "priv", "etoro_paper": False})


def test_instrument_id_uses_known_ids_without_catalogue(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)

    def fail(*a, **k):
        raise AssertionError("should not hit the catalogue for a known symbol")

    monkeypatch.setattr(client, "_request", fail)
    assert client.instrument_id("BTC") == 100000
    assert client.instrument_id("eth") == 100001  # case-insensitive
    assert client.instrument_id("EURUSD") == 1


def test_instrument_id_resolves_unknown_via_catalogue(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)

    def fake_request(method, path, **kwargs):
        assert path == "/api/v1/market-data/instruments"
        return {"instrumentDisplayDatas": [{"instrumentID": 100002, "instrumentDisplayName": "Bitcoin Cash"}]}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.instrument_id("BCH") == 100002


def test_get_price_returns_mid_of_ask_bid(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)

    def fake_request(method, path, **kwargs):
        assert path == "/api/v1/market-data/instruments/rates"
        assert kwargs["params"] == {"instrumentIds": 100000}
        return {"rates": [{"instrumentID": 100000, "ask": 62208.0, "bid": 62207.0}]}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.get_price("BTC") == 62207.5


def test_get_account_balances_parses_credit_and_positions(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)

    def fake_request(method, path, **kwargs):
        return {
            "clientPortfolio": {
                "credit": 250.75,
                "positions": [
                    {"instrumentID": 100000, "units": 0.001},
                    {"instrumentID": 100000, "units": 0.0005},  # same instrument -> summed
                    {"instrumentID": 1, "amount": 40.0},        # falls back to amount
                ],
            }
        }

    monkeypatch.setattr(client, "_request", fake_request)
    balances = client.get_account_balances()

    assert balances["USD"] == 250.75
    assert balances["BTC"] == pytest.approx(0.0015)
    assert balances["EURUSD"] == 40.0


def test_get_klines_delegates_to_market_data(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)
    monkeypatch.setattr(
        "app.services.etoro_client.etoro_market_data.get_candles",
        lambda symbol, interval, limit: [[1, 2, 3, 4, 5, 6]],
    )
    assert client.get_klines("BTC", "1h", 200) == [[1, 2, 3, 4, 5, 6]]


def test_place_order_builds_notional_body(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)
    captured = {}

    def fake_request(method, path, **kwargs):
        if path == "/api/v1/market-data/instruments/rates":
            return {"rates": [{"ask": 100.0, "bid": 100.0}]}
        if method == "POST":
            captured["path"] = path
            captured["body"] = kwargs["json"]
            return {"orderId": "abc123"}
        raise AssertionError(f"unexpected {method} {path}")

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.place_order_for_session("BTC", "BUY", usdt_amount=50.0)

    assert captured["body"]["instrumentId"] == 100000
    assert captured["body"]["isBuy"] is True
    assert captured["body"]["amount"] == 50.0
    assert captured["body"]["leverage"] == 1
    assert result.order_id == "abc123"
    assert result.quantity == pytest.approx(0.5)  # 50 USD / 100 price


def test_place_order_rejects_zero_amount(etoro_settings, monkeypatch):
    client = EToroClient(etoro_settings)
    monkeypatch.setattr(client, "get_price", lambda symbol: 100.0)
    with pytest.raises(EToroAPIError):
        client.place_order_for_session("BTC", "BUY", usdt_amount=0.0)


def test_place_order_rejects_buy_below_min_notional(etoro_settings, monkeypatch):
    """A thinly funded account sizes a BUY below eToro's minimum -- guard it
    client-side so we never fire a doomed REAL order every cycle."""
    client = EToroClient(etoro_settings.model_copy(update={"etoro_min_order_usd": 10.0}))
    monkeypatch.setattr(client, "get_price", lambda symbol: 100.0)
    with pytest.raises(EToroAPIError, match="poniżej minimum"):
        client.place_order_for_session("BTC", "BUY", usdt_amount=3.0)


def test_place_order_allows_sell_below_min_notional(etoro_settings, monkeypatch):
    """The min-notional guard is BUY-only: a SELL must still be able to close a
    tiny leftover position (dust) rather than being trapped in it."""
    client = EToroClient(etoro_settings.model_copy(update={"etoro_min_order_usd": 10.0}))
    captured = {}

    def fake_request(method, path, **kwargs):
        if path == "/api/v1/market-data/instruments/rates":
            return {"rates": [{"ask": 100.0, "bid": 100.0}]}
        captured["body"] = kwargs["json"]
        return {"orderId": "sell1"}

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.place_order_for_session("BTC", "SELL", quantity=0.03)  # $3 notional
    assert result.order_id == "sell1"
    assert captured["body"]["isBuy"] is False
