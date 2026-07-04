from app.db import seed_stopped_state
from app.services import risk_manager


def test_fresh_deploy_starts_stopped(db_session):
    """Live-money safety: a brand-new deployment must NOT trade until the human
    presses START. Seeding a fresh DB leaves the automat stopped."""
    seed_stopped_state(db_session)

    state = risk_manager.get_state(db_session)
    assert state.is_paused is True
    assert risk_manager.can_trade_automated(db_session).approved is False


def test_seed_does_not_override_a_running_bot_on_restart(db_session):
    """A restart must never silently re-pause a bot the user already started."""
    # Simulate: user already pressed START (resume clears pause).
    risk_manager.get_state(db_session)
    risk_manager.resume(db_session)
    assert risk_manager.can_trade_automated(db_session).approved is True

    # A subsequent restart calls the seed again -- it must be a no-op now.
    seed_stopped_state(db_session)
    assert risk_manager.can_trade_automated(db_session).approved is True


def test_start_button_begins_trading(db_session):
    """Pressing START (resume) on a freshly-stopped deploy enables trading."""
    seed_stopped_state(db_session)
    assert risk_manager.can_trade_automated(db_session).approved is False

    risk_manager.resume(db_session)  # the START button
    assert risk_manager.can_trade_automated(db_session).approved is True
