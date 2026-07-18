"""Per-leg strategy profiles -- the "two brains" split at the parameter level.

The base Settings fields are the REGULAR-SESSION profile ("medium aggressive",
fractional, MARKET orders). The POZA SESJĄ (extended-hours) leg trades a thinner
book on whole-share LIMIT orders, so it runs a distinct, MORE CONSERVATIVE
profile: the extended_* override fields on Settings are folded onto their base
counterparts to produce an effective Settings used only for the extended cycle.

Doing this as a single `model_copy(update=...)` at the leg's entry points
(scheduler jobs, the manual "run now" route) means the whole engine downstream
-- sizing, concurrency caps, exit geometry, triggers -- automatically reads the
leg-appropriate values without threading `venue` through every call site. The
regular-session leg passes through unchanged (base == regular profile), so its
live behaviour is untouched.
"""

from app.config import Settings

# extended_* override field  ->  base field it replaces for the extended leg.
_EXTENDED_OVERRIDES = {
    "extended_risk_per_trade_pct": "risk_per_trade_pct",
    "extended_max_concurrent_positions": "max_concurrent_positions",
    "extended_min_buy_confidence": "min_buy_confidence",
    "extended_max_new_positions_per_day": "max_new_positions_per_day",
    "extended_min_hold_minutes": "min_hold_minutes",
    "extended_max_position_pct": "max_position_pct",
    "extended_reward_risk_ratio": "reward_risk_ratio",
    "extended_trailing_stop_frac": "trailing_stop_frac",
    "extended_partial_take_profit_frac": "partial_take_profit_frac",
    "extended_partial_take_profit_r": "partial_take_profit_r",
    "extended_stop_loss_vol_mult": "stop_loss_vol_mult",
    "extended_stop_loss_min_pct": "stop_loss_min_pct",
    "extended_stop_loss_max_pct": "stop_loss_max_pct",
    "extended_volatility_reference_pct": "volatility_reference_pct",
    "extended_price_move_trigger_pct": "price_move_trigger_pct",
    "extended_full_analysis_every_minutes": "full_analysis_every_minutes",
    "extended_signal_timeframe": "signal_timeframe",
    "extended_poll_interval_minutes": "poll_interval_minutes",
}


def effective_settings(settings: Settings, venue: str) -> Settings:
    """Returns the Settings the given leg's cycle should actually run with:
    the conservative extended-hours profile for venue=="extended", the base
    (regular-session) settings unchanged otherwise."""
    if venue != "extended":
        return settings
    update = {base: getattr(settings, override) for override, base in _EXTENDED_OVERRIDES.items()}
    return settings.model_copy(update=update)
