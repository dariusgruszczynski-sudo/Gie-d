"""Kontrakt typów front<->back (lekki zamiennik codegenu).

Frontend ma RĘCZNIE przepisany interfejs StatusResponse (TypeScript). Jeśli
backend usunie/zmieni nazwę pola w /api/status, UI po cichu dostanie undefined i
kafle się rozjadą — bez żadnego błędu kompilacji. Ten test pilnuje, że KAŻDE
pole, którego oczekuje frontend, realnie wychodzi z get_status(). Pełny codegen
byłby cięższy (build step, generowane pliki); ta bramka łapie ten sam realny
dryf minimalnym kosztem. Gdy świadomie dodajesz/zmieniasz pole, zaktualizuj tu
listę i interfejs w client.ts w tym samym commicie."""

from app.api.routes_dashboard import get_status

# Pola oczekiwane przez interfejs StatusResponse we frontend/src/api/client.ts
# (bez push_mode, które jest opcjonalne: `push_mode?`).
_REQUIRED_STATUS_KEYS = {
    "mode", "quote_currency", "is_paused", "extended_paused", "is_halted",
    "halted_reason", "day_pnl_pct", "week_pnl_pct", "daily_loss_limit_pct",
    "weekly_loss_limit_pct", "max_drawdown_halt_pct", "peak_account_value",
    "max_position_pct", "whitelist", "poll_interval_minutes", "extended_enabled",
    "extended_whitelist", "market_session", "session_bounds", "market_regime",
    "extended_market_regime", "claude_budget", "account", "trading_pnl",
    "alpha_vs_spy", "share_enabled", "stats_epoch", "plan", "widget_metric",
    "exit_overrides", "realized_pnl_usd", "net_result_usd", "profiles",
    "build_sha", "build_time",
    "claude_monthly_budget_usd", "claude_spend_usd_this_month",
    "claude_budget_remaining_usd", "claude_budget_pct_used", "claude_budget_alert",
    "claude_input_tokens_this_month", "claude_output_tokens_this_month",
    "claude_total_tokens_this_month",
}

# Pola zagnieżdżone, na które UI liczy wprost.
_REQUIRED_PROFILE_KEYS = {
    "signal_timeframe", "poll_interval_minutes", "risk_per_trade_pct",
    "min_buy_confidence", "max_new_positions_per_day", "max_concurrent_positions",
    "min_hold_minutes", "hard_take_profit_pct", "max_position_pct",
    "conviction_sizing_enabled", "conviction_size_max_mult",
    "conviction_max_risk_per_trade_pct",
}


def test_status_response_has_all_frontend_fields(db_session, settings):
    body = get_status(db=db_session, settings=settings)
    missing = _REQUIRED_STATUS_KEYS - set(body.keys())
    assert not missing, f"/api/status nie zwraca pól, których oczekuje frontend: {sorted(missing)}"


def test_status_profiles_have_all_frontend_fields(db_session, settings):
    body = get_status(db=db_session, settings=settings)
    for venue in ("alpaca", "extended"):
        prof = body["profiles"][venue]
        missing = _REQUIRED_PROFILE_KEYS - set(prof.keys())
        assert not missing, f"profiles.{venue} nie ma pól oczekiwanych przez frontend: {sorted(missing)}"
