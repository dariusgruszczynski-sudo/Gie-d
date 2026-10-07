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


# crypto_* override field  ->  base field it replaces for the crypto (24/7) leg.
# Krypto jest dużo bardziej zmienne niż akcje, więc profil ma szersze stopy i
# mniejsze ryzyko/transakcję (patrz config.Settings crypto_* defaults).
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
    # Trend-following: wysoki twardy TP (ride winners) nadpisuje stockowe 6%.
    "crypto_hard_take_profit_pct": "hard_take_profit_pct",
    # 5 ulepszeń strategii (wyjścia/ryzyko) — aktywne tylko dla nogi krypto.
    "crypto_breakeven_trigger_pct": "breakeven_trigger_pct",
    "crypto_ratchet_trigger_pct": "ratchet_trigger_pct",
    "crypto_ratchet_trail_mult": "ratchet_trail_mult",
    "crypto_trend_exit_ma_period": "trend_exit_ma_period",
    "crypto_trend_exit_buffer_pct": "trend_exit_buffer_pct",
    "crypto_trend_exit_confirm_bars": "trend_exit_confirm_bars",
    "crypto_fng_derisk_above": "fng_derisk_above",
    "crypto_funding_derisk_above_pct": "funding_derisk_above_pct",
    "crypto_derisk_size_mult": "derisk_size_mult",
    # 10 mechanizmów (wykonalne teraz): #1 reżim HTF, #2 cooldown, #3 vol-trailing,
    # #4 cap ekspozycji, #5 breaker serii strat, #7 pauza na przegrzaniu.
    "crypto_regime_filter_enabled": "regime_filter_enabled",
    "crypto_regime_filter_symbol": "regime_filter_symbol",
    "crypto_regime_filter_timeframe": "regime_filter_timeframe",
    "crypto_regime_filter_ma_period": "regime_filter_ma_period",
    "crypto_reentry_cooldown_min": "reentry_cooldown_min",
    "crypto_vol_trail_mult": "vol_trail_mult",
    "crypto_max_total_exposure_pct": "max_total_exposure_pct",
    "crypto_loss_streak_pause": "loss_streak_pause",
    "crypto_fng_pause_above": "fng_pause_above",
    "crypto_funding_pause_above_pct": "funding_pause_above_pct",
    "crypto_stop_loss_vol_mult": "stop_loss_vol_mult",
    "crypto_stop_loss_min_pct": "stop_loss_min_pct",
    "crypto_stop_loss_max_pct": "stop_loss_max_pct",
    "crypto_volatility_reference_pct": "volatility_reference_pct",
    "crypto_price_move_trigger_pct": "price_move_trigger_pct",
    "crypto_full_analysis_every_minutes": "full_analysis_every_minutes",
    "crypto_signal_timeframe": "signal_timeframe",
    "crypto_poll_interval_minutes": "poll_interval_minutes",
    # Tani silnik: krypto deployuje gotówkę mechanicznie (auto-deploy on), żeby
    # działać bez LLM. Wejścia i tak przechodzą filtr konfluencji (entry_min_score).
    "crypto_auto_deploy_enabled": "auto_deploy_enabled",
}


def effective_settings(settings: Settings, venue: str) -> Settings:
    """Returns the Settings the given leg's cycle should actually run with:
    the conservative extended-hours profile for venue=="extended", the 24/7
    higher-volatility profile for venue=="crypto", the base (regular-session)
    settings unchanged otherwise."""
    overrides = {"extended": _EXTENDED_OVERRIDES, "crypto": _CRYPTO_OVERRIDES}.get(venue)
    if overrides is None:
        return settings
    update = {base: getattr(settings, override) for override, base in overrides.items()}
    return settings.model_copy(update=update)
