from app.services import risk_manager


def test_daily_loss_limit_trips_halt(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    state = risk_manager.update_portfolio_value(db_session, settings, 880.0)  # -12%, limit is 10%

    assert state.is_halted is True
    assert "10.0%" in (state.halted_reason or "") or "10%" in (state.halted_reason or "")

    check = risk_manager.can_trade_automated(db_session)
    assert check.approved is False


def test_no_halt_within_limit(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    state = risk_manager.update_portfolio_value(db_session, settings, 950.0)  # -5%, within 10% limit

    assert state.is_halted is False
    assert risk_manager.can_trade_automated(db_session).approved is True


def test_pause_and_resume(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.pause(db_session)
    assert risk_manager.can_trade_automated(db_session).approved is False

    risk_manager.resume(db_session)
    assert risk_manager.can_trade_automated(db_session).approved is True


def test_resume_clears_halt(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    state = risk_manager.update_portfolio_value(db_session, settings, 800.0)
    assert state.is_halted is True

    risk_manager.resume(db_session)
    assert risk_manager.can_trade_automated(db_session).approved is True


def test_drawdown_halt_trips_on_slow_bleed_below_peak(db_session, settings):
    """Catches a decline that never breaches the daily/weekly limit in any
    single window but has still eaten a real chunk of the all-time peak."""
    lenient = settings.model_copy(update={
        "daily_loss_limit_pct": 90.0, "weekly_loss_limit_pct": 90.0, "max_drawdown_halt_pct": 5.0,
    })
    risk_manager.update_portfolio_value(db_session, lenient, 1000.0)  # peak = 1000
    state = risk_manager.update_portfolio_value(db_session, lenient, 930.0)  # -7% from peak

    assert state.is_halted is True
    assert "szczytu" in (state.halted_reason or "")


def test_drawdown_no_halt_within_limit(db_session, settings):
    lenient = settings.model_copy(update={
        "daily_loss_limit_pct": 90.0, "weekly_loss_limit_pct": 90.0, "max_drawdown_halt_pct": 20.0,
    })
    risk_manager.update_portfolio_value(db_session, lenient, 1000.0)
    state = risk_manager.update_portfolio_value(db_session, lenient, 900.0)  # -10%, within 20%

    assert state.is_halted is False


def test_drawdown_peak_follows_new_highs(db_session, settings):
    lenient = settings.model_copy(update={
        "daily_loss_limit_pct": 90.0, "weekly_loss_limit_pct": 90.0, "max_drawdown_halt_pct": 5.0,
    })
    risk_manager.update_portfolio_value(db_session, lenient, 1000.0)  # peak = 1000
    risk_manager.update_portfolio_value(db_session, lenient, 1200.0)  # new peak = 1200
    state = risk_manager.update_portfolio_value(db_session, lenient, 1150.0)  # -4.2% from 1200
    assert state.is_halted is False

    state2 = risk_manager.update_portfolio_value(db_session, lenient, 1130.0)  # -5.8% from 1200
    assert state2.is_halted is True


def test_resume_rebaselines_drawdown_peak(db_session, settings):
    """A halt tripped by a real loss must not instantly re-trip on the next
    cycle after resume -- the peak re-baselines to the current value, same as
    the day/week loss baselines."""
    lenient = settings.model_copy(update={
        "daily_loss_limit_pct": 90.0, "weekly_loss_limit_pct": 90.0, "max_drawdown_halt_pct": 5.0,
    })
    risk_manager.update_portfolio_value(db_session, lenient, 1000.0)
    state = risk_manager.update_portfolio_value(db_session, lenient, 900.0)
    assert state.is_halted is True

    risk_manager.resume(db_session)
    state2 = risk_manager.update_portfolio_value(db_session, lenient, 900.0)
    assert state2.is_halted is False


def test_whitelist_rejects_unknown_symbol(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="TSLA", action="BUY", size_pct=5)
    assert result.approved is False


def test_max_position_size_rejected(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="SPY", action="BUY", size_pct=50)
    assert result.approved is False


def test_valid_trade_within_limits(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="SPY", action="BUY", size_pct=10)
    assert result.approved is True


def test_hold_always_approved(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="SPY", action="HOLD", size_pct=0)
    assert result.approved is True
