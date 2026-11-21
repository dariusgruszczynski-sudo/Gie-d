"""Parser feedu katalizatorów (DeFiLlama hacki -> CryptoEvent)."""
from app.services.crypto_event_feed import (
    _severity_from_amount,
    fetch_recent_hacks,
    parse_defillama_hacks,
)

NOW = 1_800_000_000.0  # stały „teraz" do testów
DAY = 86400
UNIVERSE = ["BTC/USD", "ETH/USD", "SOL/USD", "LINK/USD", "AVAX/USD", "LTC/USD", "DOGE/USD"]


def _rec(name, amount, chain, days_ago):
    return {"name": name, "amount": amount, "chain": chain,
            "classification": "Exploit", "date": NOW - days_ago * DAY}


def test_severity_scales_with_amount():
    assert _severity_from_amount(200_000_000) == 0.95
    assert _severity_from_amount(50_000_000) == 0.8
    assert _severity_from_amount(5_000_000) == 0.65
    assert _severity_from_amount(100_000) == 0.5
    assert _severity_from_amount(0) == 0.4


def test_parse_filters_by_lookback():
    raw = [_rec("Old Hack", 5e6, "Ethereum", days_ago=30),   # za stary
           _rec("Fresh Hack", 5e6, "Ethereum", days_ago=1)]   # świeży
    out = parse_defillama_hacks(raw, UNIVERSE, now_ts=NOW, lookback_days=7)
    assert len(out) == 1 and out[0].headline.startswith("Fresh Hack")


def test_chain_maps_to_universe_coin():
    raw = [_rec("Some Solana DeFi", 20e6, ["Solana"], days_ago=1)]
    out = parse_defillama_hacks(raw, UNIVERSE, now_ts=NOW, lookback_days=7)
    assert out[0].symbol == "SOL" and out[0].severity == 0.8 and out[0].kind == "hack"


def test_unmapped_chain_is_market_wide_none():
    raw = [_rec("Obscure L2 bridge", 3e6, ["SomeRandomChain"], days_ago=1)]
    out = parse_defillama_hacks(raw, UNIVERSE, now_ts=NOW, lookback_days=7)
    assert out[0].symbol is None   # brak mapowania -> news całorynkowy, nie zagrożenie monety


def test_future_dated_record_skipped():
    raw = [_rec("Bad date", 5e6, "Ethereum", days_ago=-5)]  # 5 dni w przyszłości
    assert parse_defillama_hacks(raw, UNIVERSE, now_ts=NOW, lookback_days=7) == []


def test_fetch_wrapper_handles_network_error():
    def boom(_url): raise RuntimeError("sieć padła")
    assert fetch_recent_hacks(boom, UNIVERSE, now_ts=NOW) == []


def test_fetch_wrapper_parses_injected():
    raw = [_rec("Eth Protocol", 150e6, ["Ethereum"], days_ago=0.5)]
    out = fetch_recent_hacks(lambda _u: raw, UNIVERSE, now_ts=NOW)
    assert len(out) == 1 and out[0].symbol == "ETH" and out[0].severity == 0.95
