"""Wspólny kontrakt brokera — seam Alpaca ↔ Kraken (propozycja A1).

Silnik nie powinien znać giełdy: woła powierzchnię `BrokerAdapter`, a konkretny klient
(AlpacaClient / KrakenClient) ją spełnia. Tu jest TYLKO kontrakt + selektor venue +
sprawdzenie zgodności. WPIĘCIE do żywego cyklu to osobny krok (robiony przy właścicielu,
z nowym kluczem) — żeby nie ruszać działającej nogi Alpaca na ślepo.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

# Metody, których silnik realnie potrzebuje od brokera (read + zapis zleceń).
_REQUIRED = (
    "get_price",
    "get_klines",
    "get_account_balances",
    "get_account_summary",
    "place_market_order_quantity",
)


@runtime_checkable
class BrokerAdapter(Protocol):
    """Minimalny kontrakt brokera. KrakenClient go spełnia; AlpacaClient też
    (nazwy metod celowo zgodne). `place_market_order_*` na Kraken DOMYŚLNIE dry-run."""

    def get_price(self, symbol: str) -> float: ...
    def get_klines(self, symbol: str, interval: str = ..., limit: int = ...) -> list[list]: ...
    def get_account_balances(self) -> dict[str, float]: ...
    def get_account_summary(self) -> dict[str, float]: ...
    def place_market_order_quantity(self, symbol: str, side: str, qty: float): ...


def conforms(client: object) -> bool:
    """Czy obiekt spełnia kontrakt brokera (ma wszystkie wymagane metody)."""
    return all(callable(getattr(client, m, None)) for m in _REQUIRED)


def missing_methods(client: object) -> list[str]:
    """Których metod brakuje (do diagnostyki przy wpinaniu nowego brokera)."""
    return [m for m in _REQUIRED if not callable(getattr(client, m, None))]


def make_broker(venue: str, *, transport=None):
    """Selektor brokera po venue. 'kraken' -> KrakenClient z env; inne -> None
    (noga Alpaca pozostaje na swoim dotychczasowym torze, celowo NIE przepinamy jej
    tutaj — to osobny, świadomy krok). Zwraca klienta albo None."""
    if (venue or "").lower() == "kraken":
        from app.services.kraken_client import KrakenClient
        return KrakenClient.from_env(transport=transport)
    return None
