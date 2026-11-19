"""Audyt bramek wejścia (#85): wykrywa ryzyko paraliżu z nakładających się filtrów."""
from app.services import config_audit


def test_entry_gate_audit_flags_paralysis_from_stacked_trend_gates(settings):
    """3 nakładające się filtry trendu BTC (regime_filter + btc_core + mtf_confirm)
    = paraliż wejść (ustawiamy jawnie, niezależnie od domyślnych knobów)."""
    eff = settings.model_copy(update={
        "regime_filter_enabled": True, "crypto_btc_core_mode": True, "mtf_confirm_enabled": True,
    })
    a = config_audit.entry_gate_audit(eff)
    assert a["trend_gates"] >= 3 and a["paralysis_risk"] is True
    names = {g["gate"] for g in a["active_gates"]}
    assert {"regime_filter", "btc_core", "mtf_confirm"} <= names
    assert "PARALIŻ" in a["note"]


def test_entry_gate_audit_ok_with_single_trend_gate(settings):
    """Jeden filtr trendu + kilka jakościowych -> bez flagi paraliżu."""
    eff = settings.model_copy(update={
        "regime_filter_enabled": True, "crypto_btc_core_mode": False,
        "mtf_confirm_enabled": False, "altseason_gate_enabled": False,
        "entry_filter_enabled": True, "min_adx": 0.0, "breakout_entry_enabled": False,
        "max_total_exposure_pct": 0.0, "loss_streak_pause": 0,
        "fng_pause_above": 0.0, "funding_pause_above_pct": 0.0,
    })
    a = config_audit.entry_gate_audit(eff)
    assert a["trend_gates"] == 1 and a["paralysis_risk"] is False


def test_idle_alert_due_logic():
    """#9/#65: alarm bezczynności — stoi i dawno nie wchodził -> True; w rynku lub
    świeże wejście -> False."""
    from datetime import UTC, datetime, timedelta

    from app.services import config_audit
    now = datetime(2026, 11, 19, tzinfo=UTC)
    assert config_audit.idle_alert_due(now - timedelta(days=5), now, in_market=False, threshold_days=2) is True
    assert config_audit.idle_alert_due(None, now, in_market=False) is True          # nigdy nie wszedł, stoi
    assert config_audit.idle_alert_due(now - timedelta(days=5), now, in_market=True) is False  # trzyma pozycję
    assert config_audit.idle_alert_due(now - timedelta(hours=6), now, in_market=False, threshold_days=2) is False  # świeże
