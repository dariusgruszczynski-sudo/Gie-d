"""Computes which US-equities session is currently live. Alpaca's /v2/calendar
supplies the *actual* regular-session open/close for each date (accounting for
holidays and early closes); on top of that this models the extended-hours
windows so the two trading legs can be gated correctly:

  PRE     pre-market   04:00 ET -> regular open
  REGULAR regular      regular open -> regular close   (SESJA leg)
  POST    after-hours  regular close -> 20:00 ET       (POZA SESJĄ leg)
  CLOSED  everything else (overnight, weekends, holidays)
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

CLOSED = "closed"
REGULAR = "regular"
PRE = "pre"
POST = "post"

# Extended-hours wall-clock bounds (ET). Alpaca accepts extended-hours LIMIT
# orders from 04:00 to 09:30 (pre) and 16:00 to 20:00 (post).
PRE_MARKET_OPEN = time(4, 0)
AFTER_HOURS_CLOSE = time(20, 0)

# The calendar rarely changes and this is polled by the dashboard every ~15s
# -- cache it so a hot status endpoint doesn't hammer Alpaca for something
# that only moves a few times a day. Scheduled trading cycles share the same
# cache, so it's also refreshed naturally every poll_interval_minutes.
CACHE_TTL_SECONDS = 300
CALENDAR_LOOKAHEAD_DAYS = 7

_cache: "SessionInfo | None" = None
_cache_computed_at: datetime | None = None


@dataclass
class SessionInfo:
    session: str  # CLOSED | PRE | REGULAR | POST
    # UTC-aware boundaries for the next relevant trading day: today's, if the
    # market is open or about to open today; otherwise the next trading day
    # after a weekend/holiday. None only if Alpaca returned no upcoming
    # trading day at all within the lookahead window.
    regular_open: datetime | None
    regular_close: datetime | None


def _parse_hhmm(value: str) -> time:
    hh, mm = value.split(":")[:2]
    return time(int(hh), int(mm))


def _combine_et(day: date, wall_time: time) -> datetime:
    return datetime.combine(day, wall_time, tzinfo=ET)


def compute_session_info(now_et: datetime, calendar: list[dict]) -> SessionInfo:
    """`calendar` is Alpaca's /v2/calendar response: a list of {"date":
    "YYYY-MM-DD", "open": "HH:MM", "close": "HH:MM"} for trading days,
    covering today through some days ahead. Pure function, no I/O, so it's
    directly unit-testable without hitting Alpaca."""
    today_str = now_et.date().isoformat()
    today_entry = next((c for c in calendar if c["date"] == today_str), None)

    if today_entry is not None:
        reg_open = _combine_et(now_et.date(), _parse_hhmm(today_entry["open"]))
        reg_close = _combine_et(now_et.date(), _parse_hhmm(today_entry["close"]))
        pre_open = _combine_et(now_et.date(), PRE_MARKET_OPEN)
        post_close = _combine_et(now_et.date(), AFTER_HOURS_CLOSE)
        if reg_open <= now_et < reg_close:
            session = REGULAR
        elif pre_open <= now_et < reg_open:
            session = PRE
        elif reg_close <= now_et < post_close:
            session = POST
        else:
            session = CLOSED
        return SessionInfo(session, reg_open, reg_close)

    # Not a trading day at all (weekend/holiday) -- surface the *next* one so
    # the dashboard clock can show "next session starts at ...".
    next_entry = next((c for c in calendar if c["date"] > today_str), None)
    if next_entry is None:
        return SessionInfo(CLOSED, None, None)

    next_date = date.fromisoformat(next_entry["date"])
    return SessionInfo(
        CLOSED,
        _combine_et(next_date, _parse_hhmm(next_entry["open"])),
        _combine_et(next_date, _parse_hhmm(next_entry["close"])),
    )


def cached_session_info() -> SessionInfo | None:
    """Zwraca OSTATNIO policzoną sesję z cache BEZ wywołania brokera -- albo None,
    jeśli cache jest jeszcze pusty (świeży start). Do użycia na gorących,
    często-odpytywanych ścieżkach (np. /api/status polls co 15s przez każdą
    zakładkę), które NIE MOGĄ blokować się na (do 15s) wywołaniu Alpaca. Cache
    grzeje w tle scheduler/prime przez get_session_info()."""
    return _cache


def get_session_info(broker: AlpacaClient, *, force_refresh: bool = False) -> SessionInfo:
    global _cache, _cache_computed_at
    now = datetime.now(timezone.utc)
    cache_is_fresh = (
        not force_refresh
        and _cache is not None
        and _cache_computed_at is not None
        and (now - _cache_computed_at).total_seconds() < CACHE_TTL_SECONDS
    )
    if cache_is_fresh:
        return _cache

    try:
        now_et = datetime.now(ET)
        calendar = broker.get_calendar(
            now_et.date().isoformat(),
            (now_et.date() + timedelta(days=CALENDAR_LOOKAHEAD_DAYS)).isoformat(),
        )
        info = compute_session_info(now_et, calendar)
    except Exception:
        if _cache is not None:
            logger.warning("Failed to refresh market session info, serving stale cache", exc_info=True)
            return _cache
        raise

    _cache = info
    _cache_computed_at = now
    return info


def is_tradable_session(session: str) -> bool:
    """Regular-session (SESJA) leg: trades only during regular hours."""
    return session == REGULAR


def is_extended_session(session: str) -> bool:
    """POZA SESJĄ leg: trades only in pre-market / after-hours."""
    return session in (PRE, POST)


def is_tradable_for(venue: str, session: str) -> bool:
    """Per-leg session gate: the extended leg trades PRE/POST, the regular
    (default) leg trades REGULAR."""
    return is_extended_session(session) if venue == "extended" else is_tradable_session(session)
