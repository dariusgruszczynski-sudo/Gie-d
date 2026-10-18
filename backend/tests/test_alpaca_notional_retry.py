"""Reaktywny guard limitu notional: gdy Alpaca mimo pro-aktywnego clampa zwróci
403 (40310000), _submit_order wyłuskuje jej liczby z komunikatu i ponawia RAZ,
skalując rozmiar pod limit. Bulletproof — nie zależy od naszej (bywa rozjechanej) ceny."""

import pytest

from app.config import Settings
from app.services.alpaca_client import AlpacaAPIError, AlpacaClient


def _client():
    return AlpacaClient(Settings(alpaca_api_key="k", alpaca_api_secret="s", alpaca_paper=True,
                                 max_order_notional_usd=190000.0))


def test_retries_smaller_on_notional_403(monkeypatch):
    c = _client()
    monkeypatch.setattr(c, "get_price", lambda sym: 1.0)  # qty 150k * 1 = 150k < cap -> proaktywny clamp NIE tnie
    calls = []

    def fake_request(client, method, path, **kwargs):
        body = kwargs.get("json", {})
        calls.append(dict(body))
        if len(calls) == 1:
            raise AlpacaAPIError("Alpaca POST /v2/orders: 403 {\"code\":40310000,"
                                 "\"message\":\"order notional 210000.0 exceeds max notional per order 200000\"}")
        return {"id": "x", "status": "accepted"}

    monkeypatch.setattr(c, "_request", fake_request)
    c._submit_order("SOL/USD", "sell", qty=150000.0)

    assert len(calls) == 2, "powinno ponowić dokładnie raz"
    retried_qty = float(calls[1]["qty"])
    # Przeskalowane do min(200000,190000)*0.98 = 186200 przy notionalu 210000 Alpaki.
    assert retried_qty < 150000.0
    assert retried_qty * 1.0 <= 190000.0 + 1e-6


def test_non_notional_403_not_retried(monkeypatch):
    c = _client()
    calls = []

    def fake_request(client, method, path, **kwargs):
        calls.append(1)
        raise AlpacaAPIError("Alpaca POST /v2/orders: 403 {\"code\":40010001,\"message\":\"insufficient buying power\"}")

    monkeypatch.setattr(c, "_request", fake_request)
    with pytest.raises(AlpacaAPIError):
        c._submit_order("BTC/USD", "buy", notional=5000.0)
    assert len(calls) == 1, "inny błąd nie jest ponawiany"
