"""Realne zużycie z Anthropic Admin API: sumowanie kosztu (centy->USD) i tokenów
month-to-date, bez sieci (mock _paged)."""

from app.services import anthropic_usage as au


def test_month_to_date_sums_cost_and_tokens(monkeypatch):
    def fake_paged(path, params, key):
        if "cost_report" in path:
            return [{"results": [{"amount": "12345"}, {"amount": "5000"}]}]  # centy
        return [{"results": [{
            "uncached_input_tokens": 1000,
            "output_tokens": 500,
            "cache_read_input_tokens": 200,
            "cache_creation": {"ephemeral_1h_input_tokens": 100, "ephemeral_5m_input_tokens": 50},
        }]}]

    monkeypatch.setattr(au, "_paged", fake_paged)
    au._cache.update(at=0.0, key="", data=None)  # zbij cache

    r = au.month_to_date("sk-ant-admin-test")
    assert r["cost_usd"] == round((12345 + 5000) / 100.0, 2)  # 173.45 USD
    assert r["input_tokens"] == 1000
    assert r["output_tokens"] == 500
    assert r["cached_tokens"] == 350  # 200 + 100 + 50


def test_month_to_date_no_key_returns_none():
    assert au.month_to_date("") is None
