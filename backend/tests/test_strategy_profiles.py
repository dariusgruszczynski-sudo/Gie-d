from app.services.strategy_profiles import effective_settings


def test_equities_venue_passes_settings_through_unchanged(settings):
    """The base settings ARE the equities ("medium aggressive") profile, so the
    alpaca venue must get them untouched."""
    assert effective_settings(settings, "alpaca") is settings


def test_extended_venue_folds_in_aggressive_overrides(settings):
    """The extended venue's effective settings must take the extended_* override
    values on the base fields, leaving the base object itself unmodified."""
    s = settings.model_copy(update={
        "risk_per_trade_pct": 1.25,
        "extended_risk_per_trade_pct": 2.0,
        "max_concurrent_positions": 6,
        "extended_max_concurrent_positions": 9,
        "min_buy_confidence": 0.57,
        "extended_min_buy_confidence": 0.5,
        "min_hold_minutes": 30,
        "extended_min_hold_minutes": 15,
    })
    eff = effective_settings(s, "extended")

    assert eff.risk_per_trade_pct == 2.0
    assert eff.max_concurrent_positions == 9
    assert eff.min_buy_confidence == 0.5
    assert eff.min_hold_minutes == 15
    # Base object untouched (extended profile is a copy).
    assert s.risk_per_trade_pct == 1.25
    assert s.min_hold_minutes == 30
