"""Klasyfikator LLM katalizatorów: prompt, parsowanie, batch przez fake call_model."""
from app.services.crypto_event_classifier import (
    build_user_content,
    classify_headlines,
    parse_classification,
)

UNI = ["BTC/USD", "ETH/USD", "SOL/USD"]


def test_build_user_content_lists_universe_and_indexes():
    c = build_user_content(["Hack A", "News B"], UNI)
    assert "BTC, ETH, SOL" in c
    assert "[0] Hack A" in c and "[1] News B" in c


def test_parse_clamps_and_filters():
    raw = {"events": [
        {"idx": 0, "symbol": "eth", "kind": "Exploit", "severity": 1.7},   # clamp -> 1.0
        {"idx": 1, "symbol": "", "kind": "other", "severity": -0.5},        # clamp -> 0.0, symbol None
        {"idx": 9, "symbol": "BTC", "kind": "hack", "severity": 0.5},       # idx poza zakresem -> pominięte
        {"idx": "x", "symbol": "SOL", "kind": "hack", "severity": 0.5},     # zły idx -> pominięte
    ]}
    out = parse_classification(raw, n=2)
    assert len(out) == 2
    assert out[0] == {"idx": 0, "symbol": "ETH", "kind": "exploit", "severity": 1.0}
    assert out[1]["symbol"] is None and out[1]["severity"] == 0.0


def test_classify_headlines_via_fake_call_model():
    def fake_call(model, tool, content, system, max_tokens):
        assert tool["name"] == "classify_crypto_events"
        return ({"events": [{"idx": 0, "symbol": "ETH", "kind": "hack", "severity": 0.9}]}, 0.001, 100, 20)
    out = classify_headlines(["Curve exploited, ETH DeFi hit"], UNI, fake_call)
    assert out == [{"idx": 0, "symbol": "ETH", "kind": "hack", "severity": 0.9}]


def test_classify_empty_and_llm_error_safe():
    assert classify_headlines([], UNI, lambda *a: ({"events": []},)) == []
    def boom(*a): raise RuntimeError("LLM down")
    assert classify_headlines(["x"], UNI, boom) == []   # błąd LLM -> [] (best-effort)


def test_classify_cached_reuses_within_ttl():
    from app.services.crypto_event_classifier import _CACHE, classify_cached
    _CACHE.clear()
    calls = {"n": 0}
    def counting_call(model, tool, content, system, max_tokens):
        calls["n"] += 1
        return ({"events": [{"idx": 0, "symbol": "ETH", "kind": "hack", "severity": 0.9}]},)
    r1 = classify_cached(["Curve exploited"], UNI, counting_call, ttl_sec=100, now=1000.0)
    r2 = classify_cached(["Curve exploited"], UNI, counting_call, ttl_sec=100, now=1050.0)  # w TTL
    assert r1 == r2 and calls["n"] == 1                       # drugi raz z cache
    classify_cached(["Curve exploited"], UNI, counting_call, ttl_sec=100, now=2000.0)       # po TTL
    assert calls["n"] == 2                                    # ponowna klasyfikacja
