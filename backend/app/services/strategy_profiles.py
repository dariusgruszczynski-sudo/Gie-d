"""Per-venue strategy profiles -- the "two brains" split at the parameter level.

The base Settings fields are the EQUITIES profile ("medium aggressive"). The
crypto venue trades a 24/7, higher-volatility book, so it runs a distinct,
MORE AGGRESSIVE profile: the crypto_* override fields on Settings are folded
onto their base counterparts to produce an effective Settings used only for the
crypto cycle.

Doing this as a single `model_copy(update=...)` at the venue's entry points
(scheduler jobs, the manual "run now" route) means the whole engine downstream
-- sizing, concurrency caps, exit geometry, triggers -- automatically reads the
venue-appropriate values without threading `venue` through every call site. The
equities venue passes through unchanged (base == equities profile), so its live
behaviour is untouched.
"""

from app.config import Settings

# crypto_* override field  ->  base field it replaces for the crypto venue.
_CRYPTO_OVERRIDES = {
    "crypto_risk_per_trade_pct": "risk_per_trade_pct",
    "crypto_max_concurrent_positions": "max_concurrent_positions",
    "crypto_min_buy_confidence": "min_buy_confidence",
    "crypto_max_new_positions_per_day": "max_new_positions_per_day",
    "crypto_min_hold_minutes": "min_hold_minutes",
    "crypto_max_position_pct": "max_position_pct",
    "crypto_reward_risk_ratio": "reward_risk_ratio",
    "crypto_trailing_stop_frac": "trailing_stop_frac",
    "crypto_partial_take_profit_frac": "partial_take_profit_frac",
    "crypto_partial_take_profit_r": "partial_take_profit_r",
    "crypto_stop_loss_vol_mult": "stop_loss_vol_mult",
    "crypto_stop_loss_min_pct": "stop_loss_min_pct",
    "crypto_stop_loss_max_pct": "stop_loss_max_pct",
    "crypto_volatility_reference_pct": "volatility_reference_pct",
    "crypto_price_move_trigger_pct": "price_move_trigger_pct",
    "crypto_full_analysis_every_minutes": "full_analysis_every_minutes",
}


def effective_settings(settings: Settings, venue: str) -> Settings:
    """Returns the Settings the given venue's cycle should actually run with:
    the aggressive crypto profile for venue=="crypto", the base (equities)
    settings unchanged otherwise."""
    if venue != "crypto":
        return settings
    update = {base: getattr(settings, override) for override, base in _CRYPTO_OVERRIDES.items()}
    return settings.model_copy(update=update)
