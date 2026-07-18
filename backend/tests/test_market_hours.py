from datetime import datetime

from app.services import market_hours

CALENDAR = [
    {"date": "2026-07-06", "open": "09:30", "close": "16:00"},
    {"date": "2026-07-07", "open": "09:30", "close": "16:00"},
]


def _et(hour: int, minute: int, day: int = 6) -> datetime:
    return datetime(2026, 7, day, hour, minute, tzinfo=market_hours.ET)


def test_pre_market_window():
    # 06:00 ET is inside pre-market (04:00 -> 09:30).
    info = market_hours.compute_session_info(_et(6, 0), CALENDAR)
    assert info.session == market_hours.PRE


def test_before_pre_market_open_is_closed():
    # 03:00 ET is before pre-market opens.
    info = market_hours.compute_session_info(_et(3, 0), CALENDAR)
    assert info.session == market_hours.CLOSED


def test_regular_session_window():
    info = market_hours.compute_session_info(_et(12, 0), CALENDAR)
    assert info.session == market_hours.REGULAR


def test_after_hours_window():
    # 18:00 ET is inside after-hours (16:00 -> 20:00).
    info = market_hours.compute_session_info(_et(18, 0), CALENDAR)
    assert info.session == market_hours.POST


def test_after_20_00_is_closed():
    info = market_hours.compute_session_info(_et(21, 0), CALENDAR)
    assert info.session == market_hours.CLOSED


def test_boundary_at_exactly_regular_open_is_regular():
    info = market_hours.compute_session_info(_et(9, 30), CALENDAR)
    assert info.session == market_hours.REGULAR


def test_boundary_at_exactly_regular_close_is_post():
    # 16:00 ET (regular close) opens the after-hours window.
    info = market_hours.compute_session_info(_et(16, 0), CALENDAR)
    assert info.session == market_hours.POST


def test_per_leg_tradability():
    # Regular (SESJA) leg trades only REGULAR; extended (POZA SESJĄ) only PRE/POST.
    assert market_hours.is_tradable_for("alpaca", market_hours.REGULAR) is True
    assert market_hours.is_tradable_for("alpaca", market_hours.POST) is False
    assert market_hours.is_tradable_for("extended", market_hours.PRE) is True
    assert market_hours.is_tradable_for("extended", market_hours.POST) is True
    assert market_hours.is_tradable_for("extended", market_hours.REGULAR) is False
    assert market_hours.is_tradable_for("extended", market_hours.CLOSED) is False


def test_weekend_with_no_calendar_entry_surfaces_next_trading_day():
    # "today" (7/6) has no calendar entry (assume it's a Sunday) -- only 7/7 does.
    weekend_calendar = [{"date": "2026-07-07", "open": "09:30", "close": "16:00"}]
    info = market_hours.compute_session_info(_et(10, 0), weekend_calendar)

    assert info.session == market_hours.CLOSED
    assert info.regular_open.date().isoformat() == "2026-07-07"
    assert info.regular_open.hour == 9 and info.regular_open.minute == 30


def test_no_upcoming_trading_day_at_all_returns_all_none():
    info = market_hours.compute_session_info(_et(10, 0), [])
    assert info.session == market_hours.CLOSED
    assert info.regular_open is None
    assert info.regular_close is None


def test_is_tradable_session_regular_true():
    assert market_hours.is_tradable_session(market_hours.REGULAR) is True


def test_is_tradable_session_closed_false():
    assert market_hours.is_tradable_session(market_hours.CLOSED) is False


def test_get_session_info_caches_and_serves_stale_on_error(monkeypatch):
    market_hours._cache = None
    market_hours._cache_computed_at = None

    calls = {"n": 0}

    class FakeBroker:
        def get_calendar(self, start, end):
            calls["n"] += 1
            return CALENDAR

    broker = FakeBroker()
    first = market_hours.get_session_info(broker)
    second = market_hours.get_session_info(broker)
    assert calls["n"] == 1  # second call served from cache
    assert first.session == second.session

    class FailingBroker:
        def get_calendar(self, start, end):
            raise RuntimeError("network down")

    stale = market_hours.get_session_info(FailingBroker(), force_refresh=True)
    assert stale is second  # served the stale cache instead of raising
