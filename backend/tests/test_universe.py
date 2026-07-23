"""Dynamiczne uniwersum (whitelista zbędna): trzymane + seed zawsze w środku,
trendujące z newsów DOKŁADANE tylko po walidacji tradowalności, blacklist i cap
respektowane, a każdy błąd degraduje do samego seedu (discovery tylko DODAJE)."""

from app.config import Settings
from app.services import trading_engine


def _settings(**over):
    base = dict(
        anthropic_api_key="x",
        alpaca_api_key="k",
        alpaca_api_secret="s",
        quote_currency="USD",
        trading_whitelist="SPY,QQQ",
        dynamic_universe_enabled=True,
        universe_max_symbols=5,
        symbol_blacklist="TQQQ,SQQQ",
    )
    base.update(over)
    return Settings(**base)


class FakeBroker:
    def __init__(self, balances, tradable):
        self._bal = balances
        self._tradable = set(tradable)

    def get_account_balances(self):
        return dict(self._bal)

    def is_tradable(self, symbol):
        return symbol in self._tradable


class FakeNews:
    def __init__(self, trending, raises=False):
        self._t = trending
        self._raises = raises

    def get_trending_symbols(self, limit=20):
        if self._raises:
            raise RuntimeError("news down")
        return self._t[:limit]


def test_universe_includes_held_seed_and_validated_trending():
    broker = FakeBroker(
        balances={"USD": 1000.0, "MSTR": 0.5},  # trzymane MSTR (spoza seedu)
        tradable={"NVDA", "AAPL"},               # tylko te trendujące są tradable
    )
    news = FakeNews(["NVDA", "TQQQ", "TSLA", "AAPL"])  # TQQQ blacklist, TSLA nietradowalne
    universe = trading_engine.build_alpaca_universe(None, _settings(), broker, news)

    assert "MSTR" in universe          # trzymana pozycja nigdy nie wypada
    assert "SPY" in universe and "QQQ" in universe  # seed zawsze
    assert "NVDA" in universe and "AAPL" in universe  # trendujące + tradowalne
    assert "TQQQ" not in universe      # blacklist (lewar)
    assert "TSLA" not in universe      # nietradowalne odfiltrowane
    assert len(universe) == 5          # cap respektowany


def test_universe_disabled_is_seed_plus_held_only():
    broker = FakeBroker(balances={"USD": 1000.0, "MSTR": 0.5}, tradable={"NVDA"})
    news = FakeNews(["NVDA"])
    universe = trading_engine.build_alpaca_universe(None, _settings(dynamic_universe_enabled=False), broker, news)

    assert set(universe) == {"MSTR", "SPY", "QQQ"}  # bez discovery


def test_universe_degrades_to_seed_when_discovery_fails():
    broker = FakeBroker(balances={"USD": 1000.0}, tradable={"NVDA"})
    news = FakeNews([], raises=True)  # fetch trendujących wybucha
    universe = trading_engine.build_alpaca_universe(None, _settings(), broker, news)

    assert set(universe) == {"SPY", "QQQ"}  # discovery nie psuje bazy


def test_alpaca_is_tradable_reads_asset_status(monkeypatch):
    from app.services.alpaca_client import AlpacaClient

    client = AlpacaClient.__new__(AlpacaClient)  # bez realnego __init__/sieci
    client._trading = object()

    def fake_request(c, method, path, **kw):
        return {"AAPL": {"tradable": True, "status": "active"},
                "WXYZ": {"tradable": False, "status": "inactive"}}[path.rsplit("/", 1)[-1]]

    monkeypatch.setattr(client, "_request", fake_request)
    assert client.is_tradable("AAPL") is True
    assert client.is_tradable("WXYZ") is False
