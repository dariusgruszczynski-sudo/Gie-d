from app.services.alpaca_client import AlpacaClient, TRADING_LIVE_URL, TRADING_PAPER_URL


def test_paper_setting_selects_paper_trading_url(settings):
    settings.alpaca_paper = True
    client = AlpacaClient(settings)
    assert str(client._trading.base_url) == TRADING_PAPER_URL
    assert client.mode == "paper"


def test_live_setting_selects_live_trading_url(settings):
    settings.alpaca_paper = False
    client = AlpacaClient(settings)
    assert str(client._trading.base_url) == TRADING_LIVE_URL
    assert client.mode == "live"


def test_auth_headers_sent_on_both_clients(settings):
    client = AlpacaClient(settings)
    for http_client in (client._trading, client._data):
        assert http_client.headers["apca-api-key-id"] == settings.alpaca_api_key
        assert http_client.headers["apca-api-secret-key"] == settings.alpaca_api_secret


def test_get_price_reads_latest_trade(settings, monkeypatch):
    client = AlpacaClient(settings)

    def fake_request(http_client, method, path, **kwargs):
        assert path == "/v2/stocks/SPY/trades/latest"
        assert kwargs["params"] == {"feed": "iex"}
        return {"trade": {"p": 512.34}}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.get_price("SPY") == 512.34


def test_get_klines_reshapes_bars_and_respects_limit(settings, monkeypatch):
    client = AlpacaClient(settings)
    # API returns newest-first (sort=desc).
    bars = [{"t": i, "o": 100 + i, "h": 110 + i, "l": 90 + i, "c": 105 + i, "v": 42 + i} for i in range(9, -1, -1)]

    def fake_request(http_client, method, path, **kwargs):
        assert path == "/v2/stocks/QQQ/bars"
        assert kwargs["params"]["timeframe"] == "1Hour"
        # Regression: without an explicit start Alpaca only returns the
        # current day's bars (indicators never had enough history), and
        # without sort=desc start+limit returns the OLDEST bars in the window.
        assert "start" in kwargs["params"]
        assert kwargs["params"]["sort"] == "desc"
        return {"bars": bars}

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.get_klines("QQQ", "1h", limit=3)

    assert len(result) == 3
    # Oldest-first for the indicators: [open_time, open, high, low, close, volume]
    assert result[0] == [7, 107, 117, 97, 112, 49]
    assert result[-1] == [9, 109, 119, 99, 114, 51]


def test_get_account_balances_includes_cash_and_drops_zero_positions(settings, monkeypatch):
    client = AlpacaClient(settings)

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/account":
            return {"cash": "184.20"}
        if path == "/v2/positions":
            return [{"symbol": "SPY", "qty": "0.5"}, {"symbol": "QQQ", "qty": "0.0"}]
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)
    balances = client.get_account_balances()

    assert balances == {"USD": 184.20, "SPY": 0.5}  # QQQ dropped, zero qty


def test_place_market_order_usdt_amount_submits_notional_order(settings, monkeypatch):
    client = AlpacaClient(settings)
    captured = {}

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/orders":
            captured["body"] = kwargs["json"]
            return {"id": "order-1", "symbol": "SPY", "side": "buy", "status": "filled", "filled_qty": "0.4", "filled_avg_price": "500.0"}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "get_price", lambda symbol: 500.0)

    result = client.place_market_order_usdt_amount("SPY", "BUY", 200.0)

    assert captured["body"] == {"symbol": "SPY", "side": "buy", "type": "market", "time_in_force": "day", "notional": "200.00"}
    assert result.quantity == 0.4
    assert result.price == 500.0
    assert result.usdt_value == 0.4 * 500.0


def test_place_market_order_quantity_submits_qty_order(settings, monkeypatch):
    client = AlpacaClient(settings)
    captured = {}

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/orders":
            captured["body"] = kwargs["json"]
            return {"id": "order-2", "symbol": "SPY", "side": "sell", "status": "filled", "filled_qty": "0.4", "filled_avg_price": "505.0"}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "get_price", lambda symbol: 505.0)

    result = client.place_market_order_quantity("SPY", "SELL", 0.4)

    assert captured["body"]["qty"] == "0.400000"
    assert result.side == "SELL"
    assert result.price == 505.0


def test_place_market_order_quantity_rejects_zero_quantity(settings, monkeypatch):
    client = AlpacaClient(settings)
    monkeypatch.setattr(client, "get_price", lambda symbol: 500.0)

    try:
        client.place_market_order_quantity("SPY", "SELL", 0.0000001)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_resolve_fill_polls_until_filled(settings, monkeypatch):
    client = AlpacaClient(settings)
    order = {"id": "order-3", "symbol": "SPY", "side": "buy", "status": "accepted"}
    poll_responses = iter(
        [
            {"id": "order-3", "symbol": "SPY", "side": "buy", "status": "accepted"},
            {"id": "order-3", "symbol": "SPY", "side": "buy", "status": "filled", "filled_qty": "0.4", "filled_avg_price": "500.0"},
        ]
    )

    monkeypatch.setattr(client, "_request", lambda c, m, p, **kw: next(poll_responses))
    monkeypatch.setattr("app.services.alpaca_client.time.sleep", lambda s: None)

    result = client._resolve_fill(order, fallback_price=499.0)

    assert result.quantity == 0.4
    assert result.price == 500.0


def test_resolve_fill_falls_back_to_estimate_when_never_filled(settings, monkeypatch):
    client = AlpacaClient(settings)
    order = {"id": "order-4", "symbol": "SPY", "side": "buy", "status": "accepted", "notional": "200.0"}

    monkeypatch.setattr(client, "_request", lambda c, m, p, **kw: {"id": "order-4", "symbol": "SPY", "side": "buy", "status": "accepted", "notional": "200.0"})
    monkeypatch.setattr("app.services.alpaca_client.time.sleep", lambda s: None)

    result = client._resolve_fill(order, fallback_price=500.0)

    assert result.price == 500.0
    assert result.quantity == 200.0 / 500.0


def test_get_calendar_hits_calendar_endpoint_with_date_range(settings, monkeypatch):
    client = AlpacaClient(settings)

    def fake_request(http_client, method, path, **kwargs):
        assert path == "/v2/calendar"
        assert kwargs["params"] == {"start": "2026-07-06", "end": "2026-07-13"}
        return [{"date": "2026-07-06", "open": "09:30", "close": "16:00"}]

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.get_calendar("2026-07-06", "2026-07-13")

    assert result == [{"date": "2026-07-06", "open": "09:30", "close": "16:00"}]


def test_place_order_for_session_regular_uses_plain_notional_order(settings, monkeypatch):
    client = AlpacaClient(settings)
    called = {}

    def fake_notional(symbol, side, usdt_amount):
        called["args"] = (symbol, side, usdt_amount)
        return "regular-result"

    monkeypatch.setattr(client, "place_market_order_usdt_amount", fake_notional)
    result = client.place_order_for_session("SPY", "BUY", session="regular", usdt_amount=200.0)

    assert result == "regular-result"
    assert called["args"] == ("SPY", "BUY", 200.0)


def test_place_order_for_session_extended_submits_whole_share_limit_buy(settings, monkeypatch):
    client = AlpacaClient(settings)
    captured = {}

    monkeypatch.setattr(client, "get_price", lambda symbol: 100.0)

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/orders":
            captured["body"] = kwargs["json"]
            return {"id": "o1", "symbol": "SPY", "side": "buy", "status": "filled", "filled_qty": "2", "filled_avg_price": "100.3"}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)

    # $250 at $100/share -> floor(2.5) = 2 whole shares, BUY limit slightly above price.
    result = client.place_order_for_session("SPY", "BUY", session="pre_market", usdt_amount=250.0)

    assert captured["body"]["type"] == "limit"
    assert captured["body"]["qty"] == "2.000000"
    assert captured["body"]["extended_hours"] is True
    assert captured["body"]["limit_price"] == "100.30"  # 100 * 1.003
    assert result.quantity == 2.0


def test_place_order_for_session_extended_sell_limit_below_price(settings, monkeypatch):
    client = AlpacaClient(settings)
    captured = {}

    monkeypatch.setattr(client, "get_price", lambda symbol: 100.0)

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/orders":
            captured["body"] = kwargs["json"]
            return {"id": "o2", "symbol": "SPY", "side": "sell", "status": "filled", "filled_qty": "3", "filled_avg_price": "99.7"}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)

    result = client.place_order_for_session("SPY", "SELL", session="after_hours", quantity=3.0)

    assert captured["body"]["limit_price"] == "99.70"  # 100 * 0.997
    assert result.quantity == 3.0


def test_place_order_for_session_extended_rejects_when_rounds_to_zero_shares(settings, monkeypatch):
    client = AlpacaClient(settings)
    monkeypatch.setattr(client, "get_price", lambda symbol: 900.0)  # e.g. a pricey ticker

    try:
        client.place_order_for_session("MSTR", "BUY", session="pre_market", usdt_amount=50.0)
        assert False, "expected ValueError"
    except ValueError:
        pass
