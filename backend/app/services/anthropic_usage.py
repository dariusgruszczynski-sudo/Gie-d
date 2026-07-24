"""Realne (autorytatywne) zużycie z Anthropic Admin API -- koszt i liczba
tokenów month-to-date PROSTO OD ANTHROPIC (Cost Report + Messages Usage Report),
nie lokalny szacunek. To jest odpowiedź na 'sprawdzaj na żywo ile tokenów': nie
da się zalogować do web-konsoli programowo, ale Admin API zwraca dokładnie te
liczby, które widać w konsoli.

Wymaga Admin API key (sk-ant-admin..., Console -> Settings -> Admin keys) w
settings.anthropic_admin_api_key. Best-effort: brak klucza / błąd -> None, a UI
spada na lokalny szacunek budget_tracker (też live, liczony z realnego usage).

Wynik jest cache'owany na krótko (żeby otwieranie Pulsu nie waliło w Admin API
przy każdym odświeżeniu)."""

import logging
import time
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

ADMIN_BASE = "https://api.anthropic.com"
_TIMEOUT = 15.0
_TTL_S = 60.0
_cache: dict = {"at": 0.0, "key": "", "data": None}


def _headers(key: str) -> dict:
    # Admin API keys uwierzytelniają się przez x-api-key (jak zwykłe klucze,
    # ale muszą być kluczem ADMIN). anthropic-version wymagane.
    return {"x-api-key": key, "anthropic-version": "2023-06-01"}


def _month_start_iso() -> str:
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start.isoformat().replace("+00:00", "Z")


def _paged(path: str, params: dict, key: str) -> list:
    """Zwraca połączone `data` ze wszystkich stron (bezpiecznik na 40 stron)."""
    out: list = []
    page: str | None = None
    for _ in range(40):
        p = dict(params)
        if page:
            p["page"] = page
        resp = httpx.get(f"{ADMIN_BASE}{path}", params=p, headers=_headers(key), timeout=_TIMEOUT)
        resp.raise_for_status()
        j = resp.json()
        out.extend(j.get("data") or [])
        if not j.get("has_more"):
            break
        page = j.get("next_page")
        if not page:
            break
    return out


def month_to_date(key: str) -> dict | None:
    """Realny koszt (USD) i liczba tokenów od początku bieżącego miesiąca (UTC).
    None gdy brak klucza lub Admin API niedostępne."""
    if not key:
        return None
    now = time.monotonic()
    if _cache["data"] is not None and _cache["key"] == key and now - _cache["at"] < _TTL_S:
        return _cache["data"]
    try:
        start = _month_start_iso()
        # Cost Report -- amount jest w NAJMNIEJSZYCH jednostkach (centy) -> /100.
        cost_cents = 0.0
        for b in _paged("/v1/organizations/cost_report", {"starting_at": start, "bucket_width": "1d", "limit": 31}, key):
            for r in (b.get("results") or []):
                try:
                    cost_cents += float(r.get("amount") or 0)
                except (TypeError, ValueError):
                    pass
        # Usage Report -- surowe liczby tokenów.
        inp = out = cached = 0
        for b in _paged("/v1/organizations/usage_report/messages", {"starting_at": start, "bucket_width": "1d", "limit": 31}, key):
            for r in (b.get("results") or []):
                inp += int(r.get("uncached_input_tokens") or 0)
                out += int(r.get("output_tokens") or 0)
                cc = r.get("cache_creation") or {}
                cached += (
                    int(r.get("cache_read_input_tokens") or 0)
                    + int(cc.get("ephemeral_1h_input_tokens") or 0)
                    + int(cc.get("ephemeral_5m_input_tokens") or 0)
                )
        data = {
            "cost_usd": round(cost_cents / 100.0, 2),
            "input_tokens": inp,
            "output_tokens": out,
            "cached_tokens": cached,
            "since": start,
        }
        _cache.update(at=now, key=key, data=data)
        return data
    except Exception:
        logger.warning("Anthropic Admin usage fetch failed", exc_info=True)
        return None
