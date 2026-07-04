from app.services.kraken_client import KrakenClient


def _client(settings) -> KrakenClient:
    return KrakenClient(settings)


def test_sign_is_deterministic_and_sensitive_to_inputs(settings):
    client = _client(settings)
    data = {"nonce": 1700000000000, "pair": "XBTEUR"}

    sig1 = client._sign("/0/private/AddOrder", data)
    sig2 = client._sign("/0/private/AddOrder", dict(data))
    assert sig1 == sig2  # deterministic for identical inputs

    different_path = client._sign("/0/private/Balance", data)
    assert different_path != sig1

    different_data = client._sign("/0/private/AddOrder", {**data, "pair": "ETHEUR"})
    assert different_data != sig1


def test_get_price_reads_ticker_last_close(settings, monkeypatch):
    client = _client(settings)
    monkeypatch.setattr(client, "_public", lambda path, params=None: {"XXBTZEUR": {"c": ["63154.01", "0.1"]}})

    assert client.get_price("XBTEUR") == 63154.01


def test_get_klines_reshapes_ohlc_rows_and_respects_limit(settings, monkeypatch):
    # Kraken OHLC row: [time, open, high, low, close, vwap, volume, count]
    rows = [[i, 100 + i, 110 + i, 90 + i, 105 + i, 0, 42 + i, 3] for i in range(10)]
    monkeypatch.setattr(client := _client(settings), "_public", lambda path, params=None: {"XETHZEUR": rows, "last": 0})

    result = client.get_klines("ETHEUR", "1h", limit=3)

    assert len(result) == 3
    # [open_time, open, high, low, close, volume] -- close read from index 4
    assert result[0] == [7, 107, 117, 97, 112, 49]


def test_get_account_balances_translates_altnames_and_drops_zero(settings, monkeypatch):
    client = _client(settings)

    def fake_public(path, params=None):
        assert path == "Assets"
        return {"XXBT": {"altname": "XBT"}, "ZEUR": {"altname": "EUR"}, "SOL": {"altname": "SOL"}}

    def fake_private(path, data=None):
        assert path == "Balance"
        return {"XXBT": "0.5", "ZEUR": "96.0000", "SOL": "0.0000"}

    monkeypatch.setattr(client, "_public", fake_public)
    monkeypatch.setattr(client, "_private", fake_private)

    balances = client.get_account_balances()

    assert balances == {"XBT": 0.5, "EUR": 96.0}  # SOL dropped, zero balance


def test_round_step_size_floors_to_lot_decimals(settings, monkeypatch):
    client = _client(settings)
    monkeypatch.setattr(client, "get_symbol_info", lambda symbol: {"lot_decimals": 4})

    assert client._round_step_size(0.123456, "XBTEUR") == 0.1234
