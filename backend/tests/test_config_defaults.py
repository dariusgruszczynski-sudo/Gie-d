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


def test_meta_analysis_knobs_2026_11():
    """R12/R16/R19/R26 (meta-analiza 2026-11-09): nowe knoby i twardy hamulec budżetu."""
    from app.config import Settings
    s = Settings(anthropic_api_key="x", alpaca_api_key="x", alpaca_api_secret="x")
    assert s.claude_pause_trading_at_budget is True          # R16 hard cap on
    assert s.crypto_btc_core_mode is False                   # 2026-11-19: odblokowane alty (zgoda właściciela)
    assert s.crypto_reconciliation_halt_pct == 1.0           # R19/R26
    # 2026-11-22 go-live Kraken €120: podłoga rozjazdu zbita 2000->25 USD,
    # inaczej przy małym koncie % zawsze bił pierwszy i watchdog nie ruszał.
    assert s.crypto_reconciliation_halt_floor_usd == 25.0
    # „nie dopuść do blowoutu": twarde limity, które trzymają odblokowane alty w ryzach.
    assert s.crypto_max_order_vs_dollar_vol_mult == 0.25     # zlecenie ≤ 25% dziennego obrotu
    assert s.crypto_max_new_positions_per_day == 5           # hamulec tempa wejść (3->5, zgoda właściciela)


def test_kraken_small_account_limits_2026_11_24():
    """Go-live Kraken €120: limity sizingu przekalibrowane z konta $600k na €120, żeby
    wejścia były WYKONALNE (≥ min. zlecenia Krakena), plus wyjścia zacieśnione (mniej
    oddawania zysku). Blowout-guard dalej trzyma: cap ekspozycji + dzienny limit wejść."""
    from app.config import Settings
    s = Settings(anthropic_api_key="x", alpaca_api_key="x", alpaca_api_secret="x")
    # Sizing pod małe konto (€120):
    assert s.crypto_max_position_pct == 30.0                 # €36 sufit/parę (było €12 — za mało)
    assert s.crypto_auto_deploy_max_position_pct == 25.0     # cel €30/pozycja -> ~3-4 wykonalne
    assert s.crypto_max_total_exposure_pct == 85.0           # €102 w grze, 15% bufor (było €60 bezczynne)
    assert s.auto_deploy_min_cash_usd == 10.0                # deployuj póki mieści się realne zlecenie
    # Wyjścia zacieśnione (skarga „sprzedaje za późno / oddaje zysk"):
    assert s.crypto_reward_risk_ratio == 1.5                 # trailing uzbraja na +1.5R (było +2R)
    assert s.crypto_breakeven_trigger_r == 0.75              # breakeven na +0.75R (było +1R)
    assert s.crypto_breakeven_lock_pct == 0.5                # zamknięcie ~+0.5% (netto zero po prowizji)
    # Profit-lock (decyzja „A"): bankuj zysk po cofnięciu od szczytu (dziura +3%..+6%).
    assert s.crypto_profit_lock_min_pct == 1.0               # 2026-11-27: 3->1 (auto, backtest 76%->83% traf)
    assert s.crypto_profit_lock_giveback_pct == 1.0          # 2026-11-27: 1.5->1.0
    assert s.profit_lock_min_pct == 0.0                      # akcje: wyłączone
    # Bezpiecznik podłogi konta (#4): poniżej €100 wstrzymaj NOWE wejścia (wyjścia biegną).
    # Podłoga DYNAMICZNA: −18% od szczytu konta (skaluje się z wpłatami), nie stała kwota.
    assert s.crypto_account_floor_pct == 18.0
    assert s.crypto_account_floor_usd == 0.0                 # stała kwota OFF — dynamiczna przejmuje
    assert s.account_floor_pct == 0.0                        # akcje/baza: wyłączone
    assert s.account_floor_usd == 0.0
    # Wejście kontrariańskie (#1): WŁĄCZONE dla krypto po backteście (65% vs 51% trafności).
    assert s.crypto_contrarian_entry_enabled is True
    # Pakiet 10 propozycji (backtest 499 par): płynność to zmienna dominująca.
    assert s.crypto_scanner_min_dollar_vol_usd == 50_000.0    # 2026-11-27: 200k->50k (auto, backtest: 58 par +57% vs 27 par +42%)
    assert s.crypto_min_entry_dollar_vol_usd == 50_000.0      # #3 entry-veto płynności (zgodny z progiem skanera)
    assert s.min_entry_dollar_vol_usd == 0.0                  # akcje/baza: wyłączone
    assert s.crypto_regime_filter_enabled is True             # #8 reżim ON
    assert s.crypto_max_entry_spread_pct == 0.5               # #7 zacieśniony spread-gate
    assert s.contrarian_entry_enabled is False               # akcje/baza: bez zmian (momentum)


def test_kraken_small_account_simplifications_2026_11_24():
    """Analiza pod nowe realia (€120, fee 0.52% round-trip): wytnij mnożenie prowizji
    i martwe relikty. Partial OFF (mniej fee), korelacyjny de-risk OFF (nie ścinaj do
    dust), uniwersum-fallback /EUR (nie /USD po Alpace), bankuj mocny zysk (hard-TP 15%)."""
    from app.config import Settings
    s = Settings(anthropic_api_key="x", alpaca_api_key="x", alpaca_api_secret="x")
    assert s.crypto_partial_take_profit_enabled is False     # mniej zdarzeń prowizji na małym koncie
    assert s.crypto_correlation_sizing_enabled is False      # nie ścinaj już-malutkich pozycji poniżej min
    assert s.crypto_hard_take_profit_pct == 15.0             # bankuj mocny zysk outright (było 40 blow-off)
    assert s.crypto_universe == "BTC/EUR,ETH/EUR,SOL/EUR,LINK/EUR,AVAX/EUR,LTC/EUR,DOGE/EUR"
    # Noga akcji NIETKNIĘTA (overrides tylko krypto):
    assert s.partial_take_profit_enabled is True
    assert s.hard_take_profit_pct == 6.0


def test_backtest_slippage_default():
    """R22: model poślizgu w backteście domyślnie włączony (15 bps/strona)."""
    from app.config import Settings
    s = Settings(anthropic_api_key="x", alpaca_api_key="x", alpaca_api_secret="x")
    assert s.backtest_slippage_bps == 15.0
