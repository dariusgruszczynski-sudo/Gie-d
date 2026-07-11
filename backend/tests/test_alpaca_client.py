from app.services.alpaca_client import AlpacaAPIError, AlpacaClient, TRADING_LIVE_URL, TRADING_PAPER_URL


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

    assert captured["body"]["qty"] == "0.400000000"
    assert result.side == "SELL"
    assert result.price == 505.0


def test_place_market_order_quantity_never_rounds_above_available_balance(settings, monkeypatch):
    # Regression: Alpaca 403 "insufficient qty available" (requested
    # 0.208188, available 0.20818759) -- round(0.20818759, 6) rounds UP to
    # 0.208188, which exceeds the actual held balance on a full-position
    # SELL. Must floor instead of round.
    client = AlpacaClient(settings)
    captured = {}

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/orders":
            captured["body"] = kwargs["json"]
            return {"id": "order-5", "symbol": "IWM", "side": "sell", "status": "filled", "filled_qty": "0.20818759", "filled_avg_price": "220.0"}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "get_price", lambda symbol: 220.0)

    client.place_market_order_quantity("IWM", "SELL", 0.20818759)

    # 9 dp represents the 8-decimal balance exactly: request == available (no
    # round-up -> no 403), and the whole position sells (no dust left behind).
    assert captured["body"]["qty"] == "0.208187590"
    assert float(captured["body"]["qty"]) <= 0.20818759


def test_place_market_order_quantity_rejects_zero_quantity(settings, monkeypatch):
    client = AlpacaClient(settings)
    monkeypatch.setattr(client, "get_price", lambda symbol: 500.0)

    try:
        client.place_market_order_quantity("SPY", "SELL", 0.0000000001)  # < 1e-9 -> rounds to 0
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

    result = client._resolve_fill(order, fallback_price=499.0, symbol="SPY")

    assert result.quantity == 0.4
    assert result.price == 500.0


def test_resolve_fill_falls_back_to_estimate_when_never_filled(settings, monkeypatch):
    client = AlpacaClient(settings)
    order = {"id": "order-4", "symbol": "SPY", "side": "buy", "status": "accepted", "notional": "200.0"}

    monkeypatch.setattr(client, "_request", lambda c, m, p, **kw: {"id": "order-4", "symbol": "SPY", "side": "buy", "status": "accepted", "notional": "200.0"})
    monkeypatch.setattr("app.services.alpaca_client.time.sleep", lambda s: None)

    result = client._resolve_fill(order, fallback_price=500.0, symbol="SPY")

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


def test_place_order_for_session_uses_plain_notional_order(settings, monkeypatch):
    client = AlpacaClient(settings)
    called = {}

    def fake_notional(symbol, side, usdt_amount):
        called["args"] = (symbol, side, usdt_amount)
        return "regular-result"

    monkeypatch.setattr(client, "place_market_order_usdt_amount", fake_notional)
    result = client.place_order_for_session("SPY", "BUY", usdt_amount=200.0)

    assert result == "regular-result"
    assert called["args"] == ("SPY", "BUY", 200.0)


def test_place_order_for_session_quantity_uses_plain_qty_order(settings, monkeypatch):
    client = AlpacaClient(settings)
    called = {}

    def fake_qty(symbol, side, quantity):
        called["args"] = (symbol, side, quantity)
        return "qty-result"

    monkeypatch.setattr(client, "place_market_order_quantity", fake_qty)
    result = client.place_order_for_session("SPY", "SELL", quantity=1.5)

    assert result == "qty-result"
    assert called["args"] == ("SPY", "SELL", 1.5)


# ---- crypto asset class (same account, 24/7 book) ----


def test_crypto_get_price_hits_crypto_data_endpoint_with_pair_symbol(settings, monkeypatch):
    client = AlpacaClient(settings, asset_class="crypto")

    def fake_request(http_client, method, path, **kwargs):
        assert path == "/v1beta3/crypto/us/latest/trades"
        assert kwargs["params"] == {"symbols": "BTC/USD"}
        return {"trades": {"BTC/USD": {"p": 64000.5}}}

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.get_price("BTCUSD") == 64000.5


def test_crypto_get_klines_reshapes_nested_bars(settings, monkeypatch):
    client = AlpacaClient(settings, asset_class="crypto")
    bars = [{"t": i, "o": 100 + i, "h": 110 + i, "l": 90 + i, "c": 105 + i, "v": 1 + i} for i in range(4, -1, -1)]

    def fake_request(http_client, method, path, **kwargs):
        assert path == "/v1beta3/crypto/us/bars"
        assert kwargs["params"]["symbols"] == "ETH/USD"
        assert kwargs["params"]["sort"] == "desc"
        return {"bars": {"ETH/USD": bars}}

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.get_klines("ETHUSD", "1h", limit=3)

    assert len(result) == 3
    assert result[0] == [2, 102, 112, 92, 107, 3]  # oldest-first


def test_crypto_submit_order_uses_pair_symbol_and_gtc(settings, monkeypatch):
    """Crypto orders must use the "BTC/USD" pair format and time_in_force=gtc
    -- Alpaca rejects the equities default "day" for a 24/7 asset."""
    client = AlpacaClient(settings, asset_class="crypto")
    captured = {}

    def fake_request(http_client, method, path, **kwargs):
        assert path == "/v2/orders"
        captured["body"] = kwargs["json"]
        return {"id": "c-1", "symbol": "BTC/USD", "side": "buy", "status": "filled", "filled_qty": "0.001", "filled_avg_price": "60000.0"}

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "get_price", lambda symbol: 60000.0)

    result = client.place_market_order_usdt_amount("BTCUSD", "BUY", 60.0)

    assert captured["body"] == {"symbol": "BTC/USD", "side": "buy", "type": "market", "time_in_force": "gtc", "notional": "60.00"}
    # Our whitelist-convention symbol ("BTCUSD"), NOT the API's pair-format echo.
    assert result.symbol == "BTCUSD"


def test_crypto_buy_below_min_notional_is_rejected_client_side(settings, monkeypatch):
    """A thinly funded account sizes a BUY below the exchange's minimum --
    guard it before firing a doomed real order every cycle."""
    client = AlpacaClient(settings.model_copy(update={"crypto_min_order_usd": 5.0}), asset_class="crypto")
    monkeypatch.setattr(client, "get_price", lambda symbol: 60000.0)
    try:
        client.place_market_order_usdt_amount("BTCUSD", "BUY", 2.0)
        assert False, "expected AlpacaAPIError"
    except AlpacaAPIError as exc:
        assert "poniżej minimum" in str(exc)


def test_crypto_sell_below_min_notional_still_allowed(settings, monkeypatch):
    """The min-notional guard is BUY-only -- a SELL must still close dust."""
    client = AlpacaClient(settings.model_copy(update={"crypto_min_order_usd": 5.0}), asset_class="crypto")
    captured = {}

    def fake_request(http_client, method, path, **kwargs):
        captured["body"] = kwargs["json"]
        return {"id": "c-2", "symbol": "BTC/USD", "side": "sell", "status": "filled", "filled_qty": "0.00005", "filled_avg_price": "60000.0"}

    monkeypatch.setattr(client, "_request", fake_request)
    monkeypatch.setattr(client, "get_price", lambda symbol: 60000.0)

    # SELL only supports place_market_order_quantity in this codebase, but the
    # BUY-only guard must not accidentally fire on a SELL notional path either.
    client.place_market_order_usdt_amount("BTCUSD", "SELL", 2.0)
    assert captured["body"]["side"] == "sell"


def test_crypto_positions_already_match_our_whitelist_convention(settings, monkeypatch):
    """Alpaca reports crypto positions in the legacy no-slash format
    ("BTCUSD"), which is already our whitelist convention -- get_account_balances
    needs no crypto-specific mapping, unlike order submission."""
    client = AlpacaClient(settings, asset_class="crypto")

    def fake_request(http_client, method, path, **kwargs):
        if path == "/v2/account":
            return {"cash": "50.0"}
        if path == "/v2/positions":
            return [{"symbol": "BTCUSD", "qty": "0.001"}]
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.get_account_balances() == {"USD": 50.0, "BTCUSD": 0.001}
