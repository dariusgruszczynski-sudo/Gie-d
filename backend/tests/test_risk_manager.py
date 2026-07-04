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


def test_whitelist_rejects_unknown_symbol(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="DOGEEUR", action="BUY", size_pct=5)
    assert result.approved is False


def test_max_position_size_rejected(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="XBTEUR", action="BUY", size_pct=50)
    assert result.approved is False


def test_valid_trade_within_limits(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="XBTEUR", action="BUY", size_pct=10)
    assert result.approved is True


def test_hold_always_approved(settings):
    result = risk_manager.validate_trade(settings=settings, symbol="XBTEUR", action="HOLD", size_pct=0)
    assert result.approved is True
