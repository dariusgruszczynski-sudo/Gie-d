"""Upcoming-earnings awareness for the whitelist.

The mechanical stop-loss/take-profit CANNOT protect against an earnings gap:
a bad print overnight gaps the price straight through the stop before any
order can fire. So knowing which tickers report soon is genuinely protective
in a way the rest of the risk stack is not -- it lets the bot avoid opening
a full position right before a binary event.

Source is Nasdaq's public earnings calendar (keyless). Best-effort and
heavily cached (dates barely move intraday); degrades to an empty map on any
failure -- and the caller must treat "unknown" as "no known earnings" rather
than blocking trades, so a scraper outage never halts the bot."""

import logging
from datetime import date, datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)

NASDAQ_EARNINGS_URL = "https://api.nasdaq.com/api/calendar/earnings"
# Nasdaq blocks non-browser User-Agents outright.
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}
REQUEST_TIMEOUT = 8.0
LOOKAHEAD_DAYS = 10
# Earnings dates don't move intraday -- refresh a few times a day at most.
CACHE_TTL_SECONDS = 6 * 3600

_cache: dict[str, int] | None = None
_cache_computed_at: datetime | None = None
_cache_key: tuple[str, ...] | None = None


def _fetch_earnings_symbols_for_date(day: date) -> set[str]:
    resp = httpx.get(
        NASDAQ_EARNINGS_URL,
        params={"date": day.isoformat()},
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    rows = (resp.json().get("data") or {}).get("rows") or []
    return {(r.get("symbol") or "").upper() for r in rows if r.get("symbol")}


def _compute_days_until_earnings(tickers: list[str], today: date) -> dict[str, int]:
    """Walks the next LOOKAHEAD_DAYS of the Nasdaq calendar and returns, for
    each whitelisted ticker that reports within the window, how many days
    away its NEXT report is (0 = today). Tickers not reporting in the window
    are simply absent from the map. Any per-day fetch failure is skipped, so
    partial data still helps rather than failing closed."""
    wanted = {t.upper() for t in tickers}
    days_until: dict[str, int] = {}
    for offset in range(LOOKAHEAD_DAYS + 1):
        day = today + timedelta(days=offset)
        if day.weekday() >= 5:  # weekends: US market closed, no reports
            continue
        try:
            reporting = _fetch_earnings_symbols_for_date(day)
        except Exception:
            logger.warning("Failed to fetch Nasdaq earnings for %s, skipping that day", day, exc_info=True)
            continue
        for symbol in wanted & reporting:
            days_until.setdefault(symbol, offset)  # first (nearest) hit wins
    return days_until


def get_days_until_earnings(tickers: list[str]) -> dict[str, int]:
    """Cached wrapper. Returns {ticker: days_until_next_earnings} only for
    tickers reporting within LOOKAHEAD_DAYS. Never raises -- returns the last
    good cache (or {}) on failure."""
    global _cache, _cache_computed_at, _cache_key
    now = datetime.now(timezone.utc)
    key = tuple(sorted(t.upper() for t in tickers))
    cache_fresh = (
        _cache is not None
        and _cache_computed_at is not None
        and _cache_key == key
        and (now - _cache_computed_at).total_seconds() < CACHE_TTL_SECONDS
    )
    if cache_fresh:
        return _cache

    try:
        result = _compute_days_until_earnings(list(tickers), datetime.now(timezone.utc).date())
    except Exception:
        logger.warning("Earnings calendar lookup failed entirely", exc_info=True)
        return _cache if _cache is not None else {}

    _cache, _cache_computed_at, _cache_key = result, now, key
    return result
