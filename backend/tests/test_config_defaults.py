"""Pin KRYTYCZNYCH domyślnych wartości konfiguracji handlu na żywej kasie.

Ten test istnieje po to, by refaktor config.py (rozbicie na sekcje) NIE mógł po
cichu zmienić żadnej domyślnej wartości sterującej realnym ryzykiem/strategią —
brak pola wyłapie każdy inny test (AttributeError), ale zmianę `6.0` na `60.0`
wyłapie już tylko jawny pin jak poniżej. Gdy świadomie zmieniasz domyślną,
zaktualizuj tu wartość w tym samym commicie — to celowa bramka.
"""

from app.config import Settings

# Instancja bez .env (czyste domyślne z kodu). env_file wskazuje ../.env, który w
# CI/testach nie istnieje, więc i tak dostajemy defaulty — ale wymuszamy to jawnie.
_S = Settings(_env_file=None)


def test_risk_and_exit_defaults():
    assert _S.stop_loss_pct == 2.0
    assert _S.stop_loss_min_pct == 3.0
    assert _S.stop_loss_max_pct == 12.0
    assert _S.stop_loss_vol_mult == 6.0
    assert _S.take_profit_pct == 3.0
    assert _S.hard_take_profit_pct == 6.0
    assert _S.trailing_stop_enabled is True
    assert _S.reward_risk_ratio == 2.0
    assert _S.max_drawdown_halt_pct == 45.0
    assert _S.daily_loss_limit_pct == 20.0
    assert _S.weekly_loss_limit_pct == 25.0
    assert _S.max_position_pct == 90.0
    assert _S.risk_per_trade_pct == 3.0


def test_sizing_and_entry_defaults():
    assert _S.conviction_sizing_enabled is True
    assert _S.conviction_size_max_mult == 2.0
    assert _S.conviction_max_risk_per_trade_pct == 6.0
    assert _S.conviction_edge_adaptive_enabled is True
    assert _S.conviction_edge_min_payoff == 2.0
    assert _S.conviction_edge_full_payoff == 4.0
    assert _S.min_buy_confidence == 0.60
    assert _S.progressive_confidence_step == 0.03
    assert _S.progressive_confidence_cap == 0.9
    assert _S.max_new_positions_per_day == 8
    assert _S.max_concurrent_positions == 12
    assert _S.min_hold_minutes == 2880
    assert _S.min_hold_profit_bypass_pct == 3.0
    assert _S.entry_filter_enabled is True
    assert _S.entry_min_score == 1


def test_cadence_and_universe_defaults():
    assert _S.signal_timeframe == "1d"
    assert _S.poll_interval_minutes == 30
    assert _S.price_move_trigger_pct == 3.0
    assert _S.full_analysis_every_minutes == 0
    assert _S.claude_min_reanalysis_minutes == 20
    assert _S.dynamic_universe_enabled is False
    assert _S.universe_max_symbols == 24
    assert _S.extended_enabled is False


def test_ai_and_security_defaults():
    assert _S.claude_model == "claude-opus-4-8"
    assert _S.claude_model_fast == "claude-sonnet-5"
    assert _S.claude_escalation_enabled is False
    assert _S.claude_monthly_budget_usd == 150.0
    assert _S.dashboard_users == ""
    assert _S.security_alert_enabled is True
    assert _S.security_alert_failed_logins == 5
    assert _S.db_backup_enabled is True
    assert _S.db_backup_keep == 14
    assert _S.stats_epoch_default == "2026-08-10T20:11:29+00:00"


def test_properties_still_resolve():
    s = Settings(_env_file=None, trading_whitelist="SPY, qqq ,AAPL", symbol_blacklist="TQQQ,sqqq")
    assert s.whitelist_symbols == ["SPY", "QQQ", "AAPL"]
    assert s.symbol_blacklist_set == {"TQQQ", "SQQQ"}
    assert s.dashboard_credentials == {}
    assert Settings(_env_file=None, dashboard_users="a:b,c:d").dashboard_credentials == {"a": "b", "c": "d"}
