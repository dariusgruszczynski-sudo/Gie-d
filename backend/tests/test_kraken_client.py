"""Klient Kraken (read-side): mapowanie, podpis, parsowanie, metody przez fake transport."""
from app.services.kraken_client import (
    KrakenClient,
    from_kraken_asset,
    parse_balances,
    parse_ohlc,
    parse_ticker_price,
    parse_ticker_quote,
    sign,
    to_kraken_pair,
)


def test_pair_mapping():
    assert to_kraken_pair("BTC/USD") == "XXBTZEUR"
    assert to_kraken_pair("DOGE") == "XDGEUR"
    assert to_kraken_pair("SOL/EUR") == "SOLEUR"
    assert to_kraken_pair("UNKNOWN") is None


def test_asset_mapping():
    assert from_kraken_asset("ZEUR") == "EUR"
    assert from_kraken_asset("XXBT") == "BTC"
    assert from_kraken_asset("XXDG") == "DOGE"
    assert from_kraken_asset("SOL") == "SOL"
    assert from_kraken_asset("ZUSD") == "USD"  # heurystyka X/Z


def test_sign_is_deterministic_and_base64():
    import base64
    secret = base64.b64encode(b"test-secret-key-bytes").decode()
    data = {"nonce": "1700000000000", "pair": "XXBTZEUR"}
    s1 = sign("/0/private/Balance", data, secret)
    s2 = sign("/0/private/Balance", data, secret)
    assert s1 == s2                      # deterministyczny dla tych samych wejść
    assert base64.b64decode(s1)          # poprawny base64
    # inny nonce -> inny podpis
    assert sign("/0/private/Balance", {**data, "nonce": "1700000000001"}, secret) != s1


def test_parse_ohlc_shape_and_order():
    res = {"XXBTZEUR": [
        [1700003600, "91.0", "92.0", "90.0", "91.5", "91.2", "10.0", 5],
        [1700000000, "90.0", "91.0", "89.0", "90.5", "90.2", "12.0", 7],
    ], "last": 1700003600}
    rows = parse_ohlc(res)
    assert rows[0][0] == 1700000000 and rows[-1][0] == 1700003600   # najstarsze pierwsze
    assert rows[0][4] == 90.5                                        # close = indeks 4
    assert rows[0][5] == 12.0                                        # volume z Kraken[6]
    assert len(rows[0]) == 6


def test_parse_balances_filters_zero_and_maps():
    res = {"ZEUR": "23.81", "XXBT": "0.0010", "XETH": "0.00000000", "SOL": "0"}
    b = parse_balances(res)
    assert b == {"EUR": 23.81, "BTC": 0.001}


def test_parse_ticker_price():
    assert parse_ticker_price({"XXBTZEUR": {"c": ["91234.5", "0.01"]}}) == 91234.5
    assert parse_ticker_price({}) is None


def _fake_transport(responses):
    calls = []
    def t(method, url, headers, body):
        calls.append((method, url))
        for frag, resp in responses.items():
            if frag in url:
                return resp
        return {"error": ["EGeneral:Unknown"]}
    t.calls = calls
    return t


def test_get_klines_via_fake_transport():
    resp = {"result": {"XXBTZEUR": [[1700000000, "90", "91", "89", "90.5", "90", "12", 7]], "last": 1700000000}}
    c = KrakenClient(transport=_fake_transport({"/0/public/OHLC": resp}))
    rows = c.get_klines("BTC/USD", "1h", 10)
    assert rows[0][4] == 90.5


def test_get_price_via_fake_transport():
    resp = {"result": {"XXBTZEUR": {"c": ["91000.0", "0.1"]}}}
    c = KrakenClient(transport=_fake_transport({"/0/public/Ticker": resp}))
    assert c.get_price("BTC") == 91000.0


def test_parse_ticker_quote():
    # mech#5: bid/ask -> para; zły/zerowy/odwrócony => None (fail-open wyżej)
    assert parse_ticker_quote({"XXBTZEUR": {"a": ["91010.0", "1"], "b": ["90990.0", "1"]}}) == (90990.0, 91010.0)
    assert parse_ticker_quote({}) is None
    assert parse_ticker_quote({"X": {"a": ["0", "1"], "b": ["0", "1"]}}) is None
    assert parse_ticker_quote({"X": {"c": ["1"]}}) is None


def test_get_quote_via_fake_transport():
    resp = {"result": {"XXBTZEUR": {"a": ["91010.0", "1"], "b": ["90990.0", "1"], "c": ["91000.0", "0.1"]}}}
    c = KrakenClient(transport=_fake_transport({"/0/public/Ticker": resp}))
    assert c.get_quote("BTC") == (90990.0, 91010.0)


def test_balances_requires_key():
    import pytest

    from app.services.kraken_client import KrakenError
    c = KrakenClient(key="", secret="", transport=_fake_transport({}))
    with pytest.raises(KrakenError):
        c.get_account_balances()


def test_account_summary_parses_equity():
    resp = {"result": {"eb": "23.81", "tb": "23.80", "mf": "23.80"}}
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=_fake_transport({"/0/private/TradeBalance": resp}))
    assert c.get_account_summary() == {"EUR": 23.81}


def _capture_transport(resp):
    sent = {}
    def t(method, url, headers, body):
        sent["method"] = method; sent["url"] = url; sent["body"] = body
        return resp
    t.sent = sent
    return t


def test_place_order_defaults_to_validate_dry_run():
    t = _capture_transport({"result": {"descr": {"order": "buy 0.001 XXBTZEUR @ market"}}})
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=t)
    c.place_market_order_quantity("BTC/USD", "buy", 0.001)
    assert "validate=true" in t.sent["body"]        # domyślnie dry-run
    assert "pair=XXBTZEUR" in t.sent["body"]
    assert "ordertype=market" in t.sent["body"]


def test_place_order_live_has_no_validate():
    t = _capture_transport({"result": {"txid": ["OXXXXX"]}})
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=t)
    c.place_market_order_quantity("ETH", "sell", 0.5, validate=False)
    assert "validate" not in t.sent["body"]         # realne zlecenie tylko jawnie


def test_eur_amount_converts_to_quantity():
    t = _capture_transport({"result": {"descr": {}}})
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=t)
    c.place_market_order_eur_amount("BTC", "buy", eur_amount=55.0, price=55000.0)
    # 55 EUR / 55000 = 0.001 BTC
    assert "volume=0.001" in t.sent["body"]


def test_fmt_num_no_scientific_notation():
    from app.services.kraken_client import _fmt_num
    assert _fmt_num(0.00006) == "0.00006"           # nie 6e-05
    assert _fmt_num(1234.5) == "1234.5"
    assert _fmt_num(0) == "0"


def test_is_tradable_and_universe():
    c = KrakenClient(transport=lambda *a: {"result": {}})
    assert c.is_tradable("BTC/USD") is True
    assert c.is_tradable("WIFI/USD") is False
    syms = c.list_crypto_symbols()
    assert "BTC/EUR" in syms and "DOGE/EUR" in syms and len(syms) == 7


def test_place_order_for_session_dry_run_synthetic_fill():
    def t(method, url, headers, body):
        if "Ticker" in url:
            return {"result": {"XXBTZEUR": {"c": ["50000.0", "0.1"]}}}
        return {"result": {"descr": {"order": "buy ..."}}}  # AddOrder validate
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=t)
    r = c.place_order_for_session("BTC/USD", "buy", usdt_amount=50.0)  # 50 EUR
    assert r.order_id == "dry-run"
    assert abs(r.quantity - 0.001) < 1e-9       # 50/50000
    assert r.price == 50000.0 and abs(r.usdt_value - 50.0) < 1e-6


def test_pair_ordermin_and_min_order_notional():
    import app.services.kraken_client as kc
    kc._DYN_PAIR_MIN = {"QNT": 0.02, "BTC": 0.0001}
    try:
        assert kc.pair_ordermin("QNT/EUR") == 0.02
        c = KrakenClient(transport=lambda *a: {"result": {}})
        # min notional = ordermin * cena: 0.02 QNT * €136.9 = €2.738
        assert abs(c.min_order_notional("QNT/EUR", 136.9) - 2.738) < 1e-6
        assert c.min_order_notional("WIF/EUR", 1.0) is None   # nieznany ordermin
        assert c.min_order_notional("QNT/EUR", 0) is None      # brak ceny
    finally:
        kc._DYN_PAIR_MIN = {}


def test_round_price_uses_pair_decimals():
    import app.services.kraken_client as kc
    kc._DYN_PAIR_DEC = {"BTC": 1, "NIGHT": 5}
    try:
        assert kc.round_price("BTC/EUR", 50000.123) == 50000.1
        assert kc.round_price("NIGHT/EUR", 0.0441234) == 0.04412
        assert kc.round_price("WIF/EUR", 1.23) is None   # nieznana para -> None (market)
    finally:
        kc._DYN_PAIR_DEC = {}


def test_marketable_limit_entry_uses_limit_with_buffer():
    import app.services.kraken_client as kc
    kc._DYN_PAIR_DEC = {"BTC": 1}
    try:
        t = _capture_transport({"result": {"txid": ["OZZZ"]}})
        # Ticker dla ceny + AddOrder; _capture zwraca to samo, ale body łapiemy z AddOrder.
        def t2(method, url, headers, body):
            if "Ticker" in url:
                return {"result": {"XXBTZEUR": {"c": ["50000.0", "0.1"]}}}
            t.sent = {"method": method, "url": url, "headers": headers, "body": body}
            return {"result": {"txid": ["OZZZ"]}}
        c = KrakenClient(key="k", secret="c2VjcmV0", transport=t2, live_trading=True)
        r = c.place_order_for_session("BTC/EUR", "buy", usdt_amount=50.0, prefer_limit=True, limit_buffer_pct=0.5)
        assert "ordertype=limit" in t.sent["body"]
        # BUY: limit = 50000 * 1.005 = 50250.0, zaokrąglone do 1 miejsca (_fmt_num bez .0).
        assert "price=50250" in t.sent["body"]
        assert r.price == 50250.0
    finally:
        kc._DYN_PAIR_DEC = {}


def test_marketable_limit_falls_back_to_market_when_precision_unknown():
    import app.services.kraken_client as kc
    kc._DYN_PAIR_DEC = {}  # brak precyzji -> market
    sent = {}
    def t2(method, url, headers, body):
        if "Ticker" in url:
            return {"result": {"XXBTZEUR": {"c": ["50000.0", "0.1"]}}}
        sent["body"] = body
        return {"result": {"txid": ["OZZZ"]}}
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=t2, live_trading=True)
    c.place_order_for_session("BTC/EUR", "buy", usdt_amount=50.0, prefer_limit=True, limit_buffer_pct=0.5)
    assert "ordertype=market" in sent["body"]   # nieznana precyzja -> bezpieczny market
    assert "price=" not in sent["body"]


def test_live_trading_flag_controls_dry_run():
    # Gdy silnik woła bez validate: not-live -> dry-run; live -> realne.
    bodies = []
    def t(method, url, headers, body):
        if "Ticker" in url:
            return {"result": {"XXBTZEUR": {"c": ["50000", "0.1"]}}}
        bodies.append(body)
        return {"result": {"descr": {}, "txid": ["OX"]}}
    paper = KrakenClient(key="k", secret="c2VjcmV0", transport=t, live_trading=False)
    paper.place_order_for_session("BTC/EUR", "buy", usdt_amount=50.0)
    assert "validate=true" in bodies[-1]        # paper = dry-run

    live = KrakenClient(key="k", secret="c2VjcmV0", transport=t, live_trading=True)
    live.place_order_for_session("BTC/EUR", "buy", usdt_amount=50.0)
    assert "validate" not in bodies[-1]         # live = realne zlecenie


def test_place_order_for_session_conforms_shape():
    from app.services.kraken_client import KrakenOrderResult
    def t(method, url, headers, body):
        if "Ticker" in url:
            return {"result": {"XETHZEUR": {"c": ["1500.0", "0.1"]}}}
        return {"result": {"txid": ["OZZZ"]}}
    c = KrakenClient(key="k", secret="c2VjcmV0", transport=t)
    r = c.place_order_for_session("ETH", "sell", quantity=0.02, validate=False)
    assert isinstance(r, KrakenOrderResult)
    assert r.order_id == "OZZZ" and r.quantity == 0.02
