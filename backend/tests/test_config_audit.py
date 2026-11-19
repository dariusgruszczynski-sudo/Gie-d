"""Audyt bramek wejścia (#85): wykrywa ryzyko paraliżu z nakładających się filtrów."""
from app.services import config_audit
from app.services.strategy_profiles import effective_settings


def test_entry_gate_audit_flags_paralysis_from_stacked_trend_gates(settings):
    """Domyślna konfiguracja krypto ma 3 nakładające się filtry trendu BTC
    (regime_filter + btc_core + mtf_confirm) — to właśnie paraliżuje wejścia."""
    eff = effective_settings(settings, "crypto")
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
