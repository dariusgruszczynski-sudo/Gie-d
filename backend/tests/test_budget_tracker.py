from datetime import date

from app.services import budget_tracker


def test_record_usage_accumulates_tokens_and_cost(db_session, settings):
    budget_tracker.record_usage_cost(db_session, 0.01, input_tokens=1200, output_tokens=300)
    budget_tracker.record_usage_cost(db_session, 0.02, input_tokens=800, output_tokens=200)

    status = budget_tracker.get_budget_status(db_session, settings)
    assert status["claude_input_tokens_this_month"] == 2000
    assert status["claude_output_tokens_this_month"] == 500
    assert status["claude_total_tokens_this_month"] == 2500
    assert round(status["claude_spend_usd_this_month"], 4) == 0.03


def test_status_exposes_live_token_meter_fields(db_session, settings):
    """The dashboard's live token meter reads these three keys -- they must be
    present even before any usage is recorded (fresh month -> zeros)."""
    status = budget_tracker.get_budget_status(db_session, settings)
    for key in (
        "claude_input_tokens_this_month",
        "claude_output_tokens_this_month",
        "claude_total_tokens_this_month",
    ):
        assert key in status
        assert status[key] == 0


def test_token_meter_resets_on_month_rollover(db_session, settings):
    from app.services import risk_manager

    budget_tracker.record_usage_cost(db_session, 0.05, input_tokens=5000, output_tokens=1000)
    # Simulate a stale month: force the stored month key into the past so the
    # next record rolls the window over and both meters reset together.
    state = risk_manager.get_state(db_session)
    state.claude_budget_month_key = "2000-01"
    db_session.commit()

    budget_tracker.record_usage_cost(db_session, 0.01, input_tokens=100, output_tokens=20)
    status = budget_tracker.get_budget_status(db_session, settings)
    assert state.claude_budget_month_key == date.today().strftime("%Y-%m")
    assert status["claude_input_tokens_this_month"] == 100
    assert status["claude_output_tokens_this_month"] == 20
    assert status["claude_total_tokens_this_month"] == 120
