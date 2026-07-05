"""Computes which part of the US equities trading day it currently is --
closed / pre-market / regular / after-hours. Alpaca's own /v2/clock only
reports the regular session; this adds the extended-hours windows (fixed
4:00-9:30 and 16:00-20:00 ET, industry-standard across US brokers) layered
on top of Alpaca's /v2/calendar, which supplies the *actual* regular-session
open/close for each date (accounting for holidays and early closes)."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from app.services.alpaca_client import AlpacaClient

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
PRE_MARKET_START = time(4, 0)
AFTER_HOURS_END = time(20, 0)

CLOSED = "closed"
PRE_MARKET = "pre_market"
REGULAR = "regular"
AFTER_HOURS = "after_hours"

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
    session: str  # CLOSED | PRE_MARKET | REGULAR | AFTER_HOURS
    # UTC-aware boundaries for the next relevant trading day: today's, if the
    # market is open or about to open today; otherwise the next trading day
    # after a weekend/holiday. None only if Alpaca returned no upcoming
    # trading day at all within the lookahead window.
    pre_market_start: datetime | None
    regular_open: datetime | None
    regular_close: datetime | None
    after_hours_end: datetime | None


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
        pre_start = _combine_et(now_et.date(), PRE_MARKET_START)
        reg_open = _combine_et(now_et.date(), _parse_hhmm(today_entry["open"]))
        reg_close = _combine_et(now_et.date(), _parse_hhmm(today_entry["close"]))
        after_end = _combine_et(now_et.date(), AFTER_HOURS_END)

        if now_et < pre_start or now_et >= after_end:
            session = CLOSED
        elif now_et < reg_open:
            session = PRE_MARKET
        elif now_et < reg_close:
            session = REGULAR
        else:
            session = AFTER_HOURS

        return SessionInfo(session, pre_start, reg_open, reg_close, after_end)

    # Not a trading day at all (weekend/holiday) -- surface the *next* one so
    # the dashboard clock can show "next session starts at ...".
    next_entry = next((c for c in calendar if c["date"] > today_str), None)
    if next_entry is None:
        return SessionInfo(CLOSED, None, None, None, None)

    next_date = date.fromisoformat(next_entry["date"])
    return SessionInfo(
        CLOSED,
        _combine_et(next_date, PRE_MARKET_START),
        _combine_et(next_date, _parse_hhmm(next_entry["open"])),
        _combine_et(next_date, _parse_hhmm(next_entry["close"])),
        _combine_et(next_date, AFTER_HOURS_END),
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


def is_tradable_session(session: str, extended_hours_trading_enabled: bool) -> bool:
    if session == REGULAR:
        return True
    if session in (PRE_MARKET, AFTER_HOURS):
        return extended_hours_trading_enabled
    return False
