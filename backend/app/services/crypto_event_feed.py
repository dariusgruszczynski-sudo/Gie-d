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


# --- mech#6: czysty, OCHRONNY filtr blokady wejścia (nigdy nie wymusza wyjścia) ---
_BLOCK_CACHE: dict = {"at": 0.0, "symbols": set()}


def _default_http_get(url: str):
    """urllib + systemowy CA (działa na serwerze), proxy gdy ustawione. Best-effort."""
    import json as _json
    import os as _os
    import ssl as _ssl
    import urllib.request as _ur

    ctx = _ssl.create_default_context()
    try:
        ctx = _ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
    except Exception:  # noqa: BLE001
        pass
    proxy = _os.getenv("HTTPS_PROXY") or _os.getenv("https_proxy")
    handlers = [_ur.HTTPSHandler(context=ctx)]
    if proxy:
        handlers.append(_ur.ProxyHandler({"https": proxy, "http": proxy}))
    req = _ur.Request(url, headers={"User-Agent": "gieldarek"})
    with _ur.build_opener(*handlers).open(req, timeout=20) as r:
        return _json.load(r)


def blocked_symbols_for_entry(universe, settings, *, now_ts: float, ttl_sec: float = 1800.0,
                              http_get: Callable | None = None) -> set[str]:
    """Zbiór BAZ (np. 'ETH') do ZABLOKOWANIA nowego wejścia z powodu świeżego, poważnego
    katalizatora (hack / zdarzenie podażowe). Czysto OCHRONNE — NIGDY nie wymusza
    sprzedaży trzymanej pozycji (to zostaje w shadow na żywej kasie). Fail-safe: błąd
    feedu / master OFF -> pusty zbiór (nie blokujemy nic). Cache TTL, żeby nie bić
    feedu co cykl. Niezależne od trybu act/alert (to tylko filtr wejścia)."""
    import time as _t

    from app.services.crypto_events import AVOID_KINDS, EXIT_KINDS

    if not bool(getattr(settings, "crypto_event_response_enabled", False)):
        return set()
    now = _t.time()
    if _BLOCK_CACHE["symbols"] is not None and (now - _BLOCK_CACHE["at"]) < ttl_sec:
        return set(_BLOCK_CACHE["symbols"])
    out: set[str] = set()
    try:
        lookback = float(getattr(settings, "crypto_event_lookback_days", 7.0) or 7.0)
        exit_min = float(getattr(settings, "crypto_event_exit_min_severity", 0.6))
        alert_min = float(getattr(settings, "crypto_event_alert_min_severity", 0.3))
        events = fetch_recent_hacks(http_get or _default_http_get, universe, now_ts=now_ts, lookback_days=lookback)
        for ev in events:
            if not ev.symbol:
                continue
            sev = max(0.0, min(1.0, float(ev.severity or 0.0)))
            base = ev.symbol.upper().split("/")[0]
            if ev.kind in EXIT_KINDS and sev >= exit_min:
                out.add(base)
            elif ev.kind in AVOID_KINDS and sev >= alert_min:
                out.add(base)
    except Exception:  # noqa: BLE001 — feed best-effort, nigdy nie wywala cyklu
        return set()
    _BLOCK_CACHE["at"] = now
    _BLOCK_CACHE["symbols"] = out
    return set(out)
