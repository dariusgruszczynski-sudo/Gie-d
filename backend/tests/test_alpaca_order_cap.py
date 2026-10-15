"""Twardy sufit notional w _submit_order (chokepoint brokera): żadne zlecenie —
notional ani qty, żadna ścieżka — nie wychodzi powyżej max_order_notional_usd,
więc Alpaca nie odrzuci go 403 (code 40310000)."""

from app.config import Settings
from app.services.alpaca_client import AlpacaClient


def _client(monkeypatch):
    c = AlpacaClient(Settings(alpaca_api_key="k", alpaca_api_secret="s", alpaca_paper=True,
                              max_order_notional_usd=190000.0))
    sent = {}
    monkeypatch.setattr(c, "_request", lambda *a, **k: sent.update(k.get("json", {})) or {"id": "x", "status": "accepted"})
    return c, sent


def test_notional_order_clamped(monkeypatch):
    c, sent = _client(monkeypatch)
    c._submit_order("BTC/USD", "buy", notional=250000.0)
    assert float(sent["notional"]) <= 190000.0 + 1e-6


def test_quantity_order_clamped(monkeypatch):
    c, sent = _client(monkeypatch)
    monkeypatch.setattr(c, "get_price", lambda sym: 100.0)
    # 3000 × $100 = $300k > limit -> qty przycięte do 1900 (=$190k).
    c._submit_order("SOL/USD", "sell", qty=3000.0)
    assert float(sent["qty"]) * 100.0 <= 190000.0 + 1e-6


def test_small_order_untouched(monkeypatch):
    c, sent = _client(monkeypatch)
    c._submit_order("BTC/USD", "buy", notional=5000.0)
    assert abs(float(sent["notional"]) - 5000.0) < 1e-6
