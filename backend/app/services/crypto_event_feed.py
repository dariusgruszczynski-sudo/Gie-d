"""Feed katalizatorów — parsery źródeł (DeFiLlama, keyless) → CryptoEvent.

Paczka 1 Filara INFORMACJA: zamienia surowe dane z darmowych feedów na
ustrukturyzowane zdarzenia, które rdzeń `crypto_events.event_action` oceni.

Tu jest TYLKO parsowanie/mapowanie (czyste, testowalne bez sieci). Pobieranie HTTP
to cienka osobna funkcja (wstrzykiwany klient), żeby testy nie dotykały rynku.
Mapowanie protokół/łańcuch → moneta jest CELOWO zgrubne i konserwatywne — rzetelne
„czy to zagraża monecie, którą handlujemy" doda klasyfikator LLM w następnej paczce.
"""

from __future__ import annotations

from collections.abc import Callable

from app.services.crypto_events import CryptoEvent

# Łańcuch DeFiLlama -> moneta bazowa (tylko tam, gdzie łańcuch MA swój tradeowalny
# token natywny). Hack „na łańcuchu X" to news ekosystemu X; severity i tak tnie amount.
_CHAIN_TO_COIN = {
    "ethereum": "ETH", "solana": "SOL", "avalanche": "AVAX", "avalanche c-chain": "AVAX",
    "dogecoin": "DOGE", "litecoin": "LTC", "bitcoin": "BTC", "chainlink": "LINK",
}


def _severity_from_amount(amount_usd: float) -> float:
    """Powaga 0..1 ze skali strat. Większy hack = większy wstrząs ceny/sentymentu."""
    a = amount_usd or 0.0
    if a >= 100_000_000:
        return 0.95
    if a >= 10_000_000:
        return 0.8
    if a >= 1_000_000:
        return 0.65
    if a > 0:
        return 0.5
    return 0.4


def _map_symbol(chains, name: str, universe: set[str]) -> str | None:
    """Zgrubne mapowanie na monetę z uniwersum. Zwraca symbol bazowy albo None
    (None = news całorynkowy/ekosystemowy, nie bezpośrednie zagrożenie monety)."""
    uni = {u.upper().split("/")[0] for u in (universe or [])}
    # 1) nazwa protokołu bywa tickerem monety (rzadko dla majorów, ale sprawdzamy)
    nm = (name or "").upper()
    for u in uni:
        if u and (u == nm or f" {u} " in f" {nm} "):
            return u
    # 2) łańcuch → natywna moneta, jeśli jest w uniwersum
    for ch in (chains or []):
        coin = _CHAIN_TO_COIN.get(str(ch).strip().lower())
        if coin and coin in uni:
            return coin
    return None


def parse_defillama_hacks(
    raw: list[dict],
    universe,
    *,
    now_ts: float,
    lookback_days: float = 7.0,
) -> list[CryptoEvent]:
    """Surowa lista z api.llama.fi/hacks -> świeże CryptoEvent (kind='hack').

    Bierze tylko hacki z ostatnich `lookback_days`. `raw` rekordy mają pola:
    date (epoch s), name, amount (USD), chain (list|str), classification, technique."""
    uni = {str(u).upper().split("/")[0] for u in (universe or [])}
    cutoff = now_ts - lookback_days * 86400
    out: list[CryptoEvent] = []
    for r in raw or []:
        try:
            ts = float(r.get("date") or 0)
        except (TypeError, ValueError):
            continue
        if ts < cutoff or ts > now_ts + 86400:   # spoza okna albo z przyszłości (błąd daty)
            continue
        chains = r.get("chain")
        if isinstance(chains, str):
            chains = [chains]
        name = r.get("name") or "?"
        amount = float(r.get("amount") or 0)
        sym = _map_symbol(chains, name, uni)
        out.append(CryptoEvent(
            kind="hack",
            symbol=sym,
            severity=_severity_from_amount(amount),
            source="defillama",
            headline=f"{name}: {r.get('classification') or 'hack'} (${amount/1e6:.1f}M)",
            ts=str(int(ts)),
            url="https://defillama.com/hacks",
        ))
    out.sort(key=lambda e: e.ts, reverse=True)
    return out


def fetch_recent_hacks(
    http_get: Callable[[str], list[dict]],
    universe,
    *,
    now_ts: float,
    lookback_days: float = 7.0,
) -> list[CryptoEvent]:
    """Cienki wrapper: pobiera (wstrzyknięty http_get) i parsuje. Błąd sieci ->
    pusto (feed jest best-effort, nigdy nie wywala cyklu)."""
    try:
        raw = http_get("https://api.llama.fi/hacks")
    except Exception:  # noqa: BLE001
        return []
    if not isinstance(raw, list):
        return []
    return parse_defillama_hacks(raw, universe, now_ts=now_ts, lookback_days=lookback_days)
