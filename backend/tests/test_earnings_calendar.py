from datetime import date

from app.services import earnings_calendar


def test_compute_days_until_earnings_finds_nearest(monkeypatch):
    today = date(2026, 7, 6)  # Monday

    def fake_fetch(day):
        # NVDA reports in 3 days, AAPL in 5; SPY never.
        schedule = {
            date(2026, 7, 9): {"NVDA"},
            date(2026, 7, 13): {"AAPL", "NVDA"},  # NVDA also later, but nearer wins
        }
        return schedule.get(day, set())

    monkeypatch.setattr(earnings_calendar, "_fetch_earnings_symbols_for_date", fake_fetch)

    result = earnings_calendar._compute_days_until_earnings(["SPY", "AAPL", "NVDA"], today)

    assert result == {"NVDA": 3, "AAPL": 7}
    assert "SPY" not in result


def test_compute_days_until_earnings_skips_weekends_and_failures(monkeypatch):
    today = date(2026, 7, 6)

    def flaky_fetch(day):
        if day == date(2026, 7, 8):
            raise RuntimeError("nasdaq 503")
        if day == date(2026, 7, 9):
            return {"MSTR"}
        return set()

    monkeypatch.setattr(earnings_calendar, "_fetch_earnings_symbols_for_date", flaky_fetch)

    result = earnings_calendar._compute_days_until_earnings(["MSTR"], today)

    # The 7/8 failure is skipped, 7/9 still found; weekend days never queried.
    assert result == {"MSTR": 3}


def test_get_days_until_earnings_never_raises(monkeypatch):
    earnings_calendar._cache = None
    earnings_calendar._cache_computed_at = None
    earnings_calendar._cache_key = None

    def boom(tickers, today):
        raise RuntimeError("total failure")

    monkeypatch.setattr(earnings_calendar, "_compute_days_until_earnings", boom)

    # Must degrade to {} instead of propagating -- a scraper outage can't halt trading.
    assert earnings_calendar.get_days_until_earnings(["SPY"]) == {}
