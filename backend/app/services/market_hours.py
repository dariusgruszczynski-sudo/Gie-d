"""Computes whether the US equities regular session is currently open or
closed. Alpaca's /v2/calendar supplies the *actual* regular-session open/close
for each date (accounting for holidays and early closes); this reduces it to a
simple REGULAR/CLOSED state. Pre-market and after-hours are not modeled here
yet -- the POZA SESJĄ (extended-hours) leg's PRE/POST session gating lands in a
later package; for now this is regular-session-only."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")

CLOSED = "closed"
REGULAR = "regular"

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
    session: str  # CLOSED | REGULAR
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
        session = REGULAR if reg_open <= now_et < reg_close else CLOSED
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
    return session == REGULAR
