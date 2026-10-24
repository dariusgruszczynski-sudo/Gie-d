"""Skaner rynku 24/7: ranking po sile vs BTC, filtr płynności, trzymane zawsze w
uniwersum, fallback gdy wyłączony/brak danych."""

from app.config import Settings
from app.services.market_scanner import scan_universe


def _rows(start: float, end: float, n: int, vol: float) -> list[list]:
    """n dziennych świec od start do end (liniowo); [t,o,h,l,c,v]."""
    out = []
    for i in range(n):
        c = start + (end - start) * i / (n - 1)
        out.append([i, c, c, c, c, vol])
    return out


class FakeScanBroker:
    def __init__(self, series: dict, held: dict | None = None):
        self.series = series          # sym -> (start, end, vol)
        self._held = held or {}

    def list_crypto_symbols(self):
        return list(self.series.keys())

    def get_klines(self, symbol, interval="1h", limit=24):
        s = self.series.get(symbol)
        if s is None:
            return []
        start, end, vol = s
        return _rows(start, end, 35, vol)

    def get_account_balances(self):
        return dict(self._held)


def _settings(**over):
    base = dict(
        crypto_scanner_enabled=True, crypto_scanner_top_k=2, crypto_scanner_max_scan=40,
        crypto_scanner_momentum_days=30, crypto_scanner_min_dollar_vol_usd=5_000_000.0,
        crypto_scanner_rs_vs_btc=True, crypto_scanner_cache_min=0.0,  # logika: bez cache
        crypto_universe="BTC/USD,ETH/USD",
    )
    base.update(over)
    return Settings(**base)


def test_ranks_strongest_vs_btc():
    # BTC płasko, STRONG +50%, WEAK -20%; płynne (duży wolumen).
    broker = FakeScanBroker({
        "BTC/USD": (100, 100, 100_000),
        "STRONG/USD": (100, 150, 100_000),
        "WEAK/USD": (100, 80, 100_000),
        "MID/USD": (100, 110, 100_000),
    })
    uni = scan_universe(broker, _settings())
    assert "STRONG/USD" in uni            # najsilniejszy wchodzi
    assert uni.index("STRONG/USD") < uni.index("MID/USD") if "MID/USD" in uni else True
    assert "WEAK/USD" not in uni[:2]      # słaby nie w TOP-2


def test_liquidity_filter_drops_thin():
    # THIN ma mocny momentum, ale obrót < próg -> odpada (nie trzymany).
    broker = FakeScanBroker({
        "BTC/USD": (100, 100, 100_000),
        "THIN/USD": (100, 300, 1),        # ogromny wzrost, ale wolumen 1 => obrót ~100$/dzień
        "LIQ/USD": (100, 130, 100_000),
    })
    uni = scan_universe(broker, _settings())
    assert "THIN/USD" not in uni
    assert "LIQ/USD" in uni


def test_held_always_included_even_if_weak():
    broker = FakeScanBroker(
        {"BTC/USD": (100, 100, 100_000), "DOG/USD": (100, 60, 100_000), "STRONG/USD": (100, 150, 100_000)},
        held={"DOG/USD": 123.0},
    )
    uni = scan_universe(broker, _settings())
    assert "DOG/USD" in uni               # trzymany zostaje, mimo słabości (żeby dało się wyjść)


def test_disabled_returns_fixed_universe():
    broker = FakeScanBroker({"BTC/USD": (100, 120, 100_000)})
    uni = scan_universe(broker, _settings(crypto_scanner_enabled=False))
    assert uni == ["BTC/USD", "ETH/USD"]  # statyczne crypto_symbols


def test_empty_pool_falls_back():
    class EmptyBroker(FakeScanBroker):
        def list_crypto_symbols(self):
            return []
    broker = EmptyBroker({"BTC/USD": (100, 120, 100_000)})
    uni = scan_universe(broker, _settings())
    assert uni  # nie pusto — fallback/zawartość


def test_report_exposes_diagnostics():
    """Obserwowalność (audyt): report pokazuje ile par dał broker, ile zrankowano
    i czy to realne poszerzenie, czy fallback na statyczną listę."""
    from app.services.market_scanner import scan_universe_report
    broker = FakeScanBroker({
        "BTC/USD": (100, 100, 100_000), "STRONG/USD": (100, 150, 100_000), "MID/USD": (100, 110, 100_000),
    })
    rep = scan_universe_report(broker, _settings())
    assert rep["pool_size"] == 3 and rep["scored"] >= 2
    assert rep["fell_back"] is False and rep["reason"] == "ok"
    assert "STRONG/USD" in rep["universe"]


def test_report_flags_effective_static_when_ranking_empty():
    """Gdy ranking nic nie dołożył ponad trzymane+BTC (brak płynnych par z danymi),
    report oznacza to jako fallback — sygnał „skaner efektywnie na statycznej 7-tce"."""
    from app.services.market_scanner import scan_universe_report
    # Wszystkie poza BTC za cienkie (wolumen 1 -> obrót poniżej progu 5M) i nie trzymane.
    broker = FakeScanBroker({"BTC/USD": (100, 100, 1), "THIN/USD": (100, 300, 1)})
    rep = scan_universe_report(broker, _settings())
    assert rep["top"] == []
    assert rep["fell_back"] is True and "ranking pusty" in rep["reason"]
    # Diagnostyka wskazuje PRZYCZYNĘ: obie pary odpadły na płynności (obrót ~$100/d < 5M).
    assert rep["skips"]["illiquid"] == 2
    assert rep["skips"]["too_few_bars"] == 0
    # Rozkład obrotów policzony dla WSZYSTKICH par z danymi (do dobrania progu).
    assert rep["liquidity"]["count"] == 2
    assert {s for s, _ in rep["liquidity"]["top"]} == {"BTC/USD", "THIN/USD"}
    assert rep["liquidity"]["max_usd"] >= rep["liquidity"]["min_usd"]


def test_stablecoins_excluded_from_ranking():
    """Stablecoiny (peg ~$1) są wykluczone — momentum peg-a to szum, a na obrót
    venue potrafią wejść na szczyt listy i zaśmiecać ranking."""
    from app.services.market_scanner import scan_universe_report
    broker = FakeScanBroker({
        "BTC/USD": (100, 100, 100_000), "USDC/USD": (1, 1, 10_000_000), "SOL/USD": (100, 150, 100_000),
    })
    rep = scan_universe_report(broker, _settings())
    assert rep["skips"]["stablecoin"] == 1
    assert "USDC/USD" not in rep["universe"] and "USDC/USD" not in rep["top"]
    assert "SOL/USD" in rep["universe"]


def test_report_flags_broker_exception_fallback():
    from app.services.market_scanner import scan_universe_report

    class BoomBroker(FakeScanBroker):
        def list_crypto_symbols(self):
            raise RuntimeError("API down")
    rep = scan_universe_report(BoomBroker({"BTC/USD": (100, 120, 100_000)}), _settings())
    assert rep["fell_back"] is True and "błąd" in rep["reason"]
    assert rep["universe"] == ["BTC/USD", "ETH/USD"]  # statyczny fallback


def test_cache_reuses_ranking_but_refreshes_held():
    """Audyt (efektywność): w obrębie cache_min ranking nie jest przeliczany
    (mniej fetchy), ale TRZYMANE pozycje domykane są świeżo w każdym wywołaniu."""
    from app.services import market_scanner
    market_scanner._reset_cache()

    class CountingBroker(FakeScanBroker):
        def __init__(self, series, held=None):
            super().__init__(series, held)
            self.kline_calls = 0

        def get_klines(self, symbol, interval="1h", limit=24):
            self.kline_calls += 1
            return super().get_klines(symbol, interval, limit)

    s = _settings(crypto_scanner_cache_min=60.0)
    broker = CountingBroker({
        "BTC/USD": (100, 100, 100_000), "STRONG/USD": (100, 150, 100_000), "MID/USD": (100, 110, 100_000),
    })
    uni1 = scan_universe(broker, s)
    after_first = broker.kline_calls
    assert after_first > 0 and "STRONG/USD" in uni1

    # Drugie wywołanie w oknie cache: ranking z cache -> ZERO nowych fetchy klines.
    uni2 = scan_universe(broker, s)
    assert broker.kline_calls == after_first          # nie pobrał świec ponownie
    assert uni2 == uni1

    # Nowo trzymana pozycja MUSI wejść do uniwersum mimo cache (świeży held).
    broker._held = {"MID/USD": 5.0}
    uni3 = scan_universe(broker, s)
    assert "MID/USD" in uni3
    assert broker.kline_calls == after_first          # wciąż bez nowych fetchy
    market_scanner._reset_cache()
