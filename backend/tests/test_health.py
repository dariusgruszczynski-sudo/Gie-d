from datetime import datetime, timedelta, timezone

import pytest

from app.services import health, risk_manager


def test_age_minutes_handles_naive_and_aware():
    assert health._age_minutes(None) is None
    aware = datetime.now(timezone.utc) - timedelta(minutes=10)
    assert 9 < health._age_minutes(aware) < 11
    naive = datetime.utcnow() - timedelta(minutes=5)  # treated as UTC
    assert 4 < health._age_minutes(naive) < 6


def test_run_reset_unknown_action_raises():
    with pytest.raises(KeyError):
        health.run_reset("nope", db=None, settings=None)


def test_reset_budget_meter_zeroes_spend(db_session, settings):
    state = risk_manager.get_state(db_session)
    state.claude_spend_usd_this_month = 12.34
    db_session.commit()

    out = health.run_reset("reset_budget_meter", db_session, settings)

    assert "wyzerowany" in out["message"]
    assert risk_manager.get_state(db_session).claude_spend_usd_this_month == 0.0


def test_reset_resume_alpaca_clears_halt(db_session, settings):
    state = risk_manager.get_state(db_session)
    state.is_halted = True
    state.halted_reason = "test"
    state.is_paused = True
    db_session.commit()

    health.run_reset("clear_halt", db_session, settings)

    refreshed = risk_manager.get_state(db_session)
    assert refreshed.is_halted is False
    assert refreshed.is_paused is False


def test_rebaseline_pnl_is_registered_and_graceful_without_data(db_session, settings):
    # No snapshots in a fresh test DB -> _account_view returns None, so the
    # reset degrades to a message instead of crashing.
    assert "rebaseline_pnl" in health.RESET_ACTIONS
    out = health.run_reset("rebaseline_pnl", db_session, settings)
    assert "P&L" in out["message"] or "Brak danych" in out["message"]


def test_every_probe_action_has_a_reset_handler():
    """Guard against a probe emitting an `action` string that no RESET_ACTIONS
    entry handles (a typo would render a dead button)."""
    emitted = {
        "reset_budget_meter", "refresh_snapshots", "restart_scheduler",
        "clear_halt", "resume_alpaca", "resume_extended",
    }
    assert emitted <= set(health.RESET_ACTIONS)
