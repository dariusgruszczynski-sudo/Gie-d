"""Orchestrates one full decision cycle: gather data -> ask Claude (Sonnet by
default, escalating to Opus when unsure) -> risk checks -> execute -> log
everything."""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Decision, PortfolioSnapshot, Trade, TradeAction, TradeMode, TriggerType
from app.services import budget_tracker, earnings_calendar, email_reporter, market_hours, risk_manager, scorecard, signals
from app.services.alpaca_client import AlpacaAPIError, AlpacaClient
from app.services.etoro_client import EToroAPIError
from app.services.claude_advisor import ClaudeAdvisor
from app.services.market_context import MarketContextClient
from app.services.market_hours import SessionInfo
from app.services.news_client import NewsClient
from app.services.technical_indicators import compute_technical_indicators, compute_volatility_pct

logger = logging.getLogger(__name__)

# Alpaca rejects orders below ~$1 notional, so a position worth less than this
# is unsellable "dust" (e.g. a ~1e-7 share remainder left by an earlier
# rounding bug). Treat it as not-a-position instead of retrying a doomed SELL
# on every poll -- it's economically irrelevant (fractions of a cent).
MIN_SELL_NOTIONAL_USD = 1.0

# Per-venue SystemState column mapping. The Alpaca venue keeps using the
# original columns (its behaviour stays byte-for-byte identical); the eToro
# venue uses dedicated etoro_* columns so the two venues' per-cycle state
# (price anchors, trailing peaks, cooldowns, seen headlines) never collide.
_STATE_COLUMNS = {
    "anchors": {"alpaca": "last_check_prices_json", "etoro": "etoro_check_prices_json"},
    "peaks": {"alpaca": "position_peaks_json", "etoro": "etoro_position_peaks_json"},
    "cooldowns": {"alpaca": "stop_loss_cooldowns_json", "etoro": "etoro_stop_loss_cooldowns_json"},
    "seen": {"alpaca": "seen_ticker_headlines_json", "etoro": "etoro_seen_ticker_headlines_json"},
    "partial": {"alpaca": "partial_tp_taken_json", "etoro": "etoro_partial_tp_taken_json"},
    "streak": {"alpaca": "stop_loss_streak_json", "etoro": "etoro_stop_loss_streak_json"},
}


def _state_col(kind: str, venue: str) -> str:
    return _STATE_COLUMNS[kind].get(venue, _STATE_COLUMNS[kind]["alpaca"])


def _get_analysis_marks(state, venue: str) -> tuple[str, str]:
    """(last_full_analysis_date, last_analysis_at) for a venue. Alpaca uses the
    original scalar columns; eToro uses its own JSON blob."""
    if venue != "etoro":
        return state.last_full_analysis_date, state.last_analysis_at
    b = json.loads(state.etoro_analysis_state_json or "{}")
    return b.get("last_full_date", ""), b.get("last_at", "")


def _set_analysis_marks(state, venue: str, full_date: str, at: str) -> None:
    if venue != "etoro":
        state.last_full_analysis_date = full_date
        state.last_analysis_at = at
    else:
        state.etoro_analysis_state_json = json.dumps({"last_full_date": full_date, "last_at": at})


def _base_asset(symbol: str, quote_currency: str) -> str:
    return symbol.replace(quote_currency, "")


def volatility_adjusted_size(settings: Settings, requested_pct: float, ticker_vol_pct: float | None) -> float:
    """Scales a requested BUY size DOWN (never up) for tickers more volatile
    than the reference, so a wild name like MSTR takes a smaller slice than a
    steady one like SPY for the same conviction -- steadier risk-adjusted
    exposure. Bounded below by volatility_min_scale so a volatile name isn't
    sized to nothing."""
    if (
        settings.volatility_reference_pct <= 0
        or not ticker_vol_pct
        or ticker_vol_pct <= settings.volatility_reference_pct
    ):
        return requested_pct
    scale = max(settings.volatility_min_scale, settings.volatility_reference_pct / ticker_vol_pct)
    return round(requested_pct * scale, 4)


def _is_tradable_session(session_info: SessionInfo) -> bool:
    return market_hours.is_tradable_session(session_info.session)


def _session_closed_reason(session_info: SessionInfo) -> str:
    return "Rynek zamknięty -- transakcja niewykonana (spróbuj w godzinach handlu)."


def compute_portfolio(db: Session, settings: Settings, broker, *, venue: str = "alpaca", whitelist: list[str] | None = None) -> dict:
    """Generic across the whole whitelist -- works for 2 tickers or 10 without
    any schema or code change per ticker. A single symbol failing on the broker
    (network hiccup, delisted ticker, etc.) is skipped rather than aborting the
    whole cycle -- otherwise one bad symbol silently kills every scheduled
    cycle and manual "run now" indefinitely. `venue`/`whitelist` select which
    broker/portfolio this snapshot is for (defaults preserve the Alpaca path)."""
    symbols = whitelist if whitelist is not None else settings.whitelist_symbols
    balances = broker.get_account_balances()
    usdt_balance = balances.get(settings.quote_currency, 0.0)

    prices: dict[str, float] = {}
    coin_balances: dict[str, float] = {}
    failed_symbols: list[str] = []
    total_value = usdt_balance

    for symbol in symbols:
        try:
            price = broker.get_price(symbol)
        except Exception:
            logger.warning("Failed to fetch price for %s, skipping it this cycle", symbol, exc_info=True)
            failed_symbols.append(symbol)
            continue
        base = _base_asset(symbol, settings.quote_currency)
        qty = balances.get(base, 0.0)
        prices[symbol] = price
        coin_balances[base] = qty
        total_value += qty * price

    snapshot = PortfolioSnapshot(
        total_value_usdt=total_value,
        usdt_balance=usdt_balance,
        balances_json=json.dumps(coin_balances),
        prices_json=json.dumps(prices),
        failed_symbols_json=json.dumps(failed_symbols),
        venue=venue,
    )
    db.add(snapshot)
    db.commit()

    return {
        "total_value_usdt": total_value,
        "usdt_balance": usdt_balance,
        "balances": coin_balances,
        "prices": prices,
        "failed_symbols": failed_symbols,
        "venue": venue,
    }


def check_trigger(
    db: Session,
    settings: Settings,
    prices: dict[str, float],
    price_move_trigger_pct: float | None = None,
    *,
    venue: str = "alpaca",
) -> tuple[bool, TriggerType]:
    """Decides whether this poll warrants a (paid) Claude analysis.

    Price moves are measured CUMULATIVELY against anchor prices captured at
    the last triggered analysis -- NOT against the previous poll. The old
    per-poll comparison quietly starved the bot: with a 3-minute poll, a
    ticker had to move the full threshold within 3 minutes to ever trigger,
    so a slow steady trend (0.2% per poll, 2% over an hour) never woke Claude
    and the automat sat idle all session.

    A heartbeat additionally forces a full analysis every
    full_analysis_every_minutes of tradable session, so Claude periodically
    looks at the market even when nothing moved sharply -- setups aren't only
    born from spikes.

    `price_move_trigger_pct` overrides settings.price_move_trigger_pct when
    given (higher bar during extended hours -- see run_cycle)."""
    state = risk_manager.get_state(db)
    today_str = date.today().isoformat()
    threshold = settings.price_move_trigger_pct if price_move_trigger_pct is None else price_move_trigger_pct

    anchors_col = _state_col("anchors", venue)
    anchors: dict[str, float] = json.loads(getattr(state, anchors_col) or "{}")
    last_full_date, last_at_iso = _get_analysis_marks(state, venue)

    triggered = False
    reason = TriggerType.SCHEDULED_DAILY

    for symbol, current_price in prices.items():
        anchor = anchors.get(symbol, 0.0)
        if anchor > 0:
            move_pct = abs(current_price - anchor) / anchor * 100
            if move_pct >= threshold:
                triggered = True
                reason = TriggerType.PRICE_MOVE
                logger.info("Trigger: %s przesunął się %.2f%% od kotwicy (próg %.2f%%)", symbol, move_pct, threshold)
        else:
            # First sighting -- set the anchor without triggering.
            anchors[symbol] = current_price

    if last_full_date != today_str:
        triggered = True
        if reason != TriggerType.PRICE_MOVE:
            reason = TriggerType.SCHEDULED_DAILY

    # Heartbeat: force a periodic full look at the market during tradable
    # hours even without a sharp move.
    if not triggered and settings.full_analysis_every_minutes > 0 and last_at_iso:
        try:
            last_at = datetime.fromisoformat(last_at_iso)
            overdue = datetime.now(timezone.utc) - last_at >= timedelta(minutes=settings.full_analysis_every_minutes)
        except ValueError:
            overdue = True
        if overdue:
            triggered = True
            reason = TriggerType.SCHEDULED_DAILY
            logger.info(
                "Trigger: heartbeat -- ostatnia pełna analiza starsza niż %d min",
                settings.full_analysis_every_minutes,
            )

    if triggered:
        # Re-anchor everything: the analysis that follows becomes the new
        # reference point for cumulative moves.
        anchors = dict(prices)

    setattr(state, anchors_col, json.dumps(anchors))
    db.commit()
    return triggered, reason


def check_news_trigger(
    db: Session, settings: Settings, news: NewsClient, *, venue: str = "alpaca", whitelist: list[str] | None = None
) -> tuple[bool, list[dict]]:
    """Reacts to a brand-new, ticker-specific headline (earnings release,
    material single-stock news) the instant it's published, independent of
    any price move -- crucial pre-/after-market, where thin trading means the
    price often lags the news print by minutes and a pure price-move trigger
    would catch it too late. Only the cheap per-ticker feed is checked here
    (no Claude cost); the full ~30-source fetch still only happens once the
    cycle actually triggers."""
    state = risk_manager.get_state(db)
    seen_col = _state_col("seen", venue)
    symbols = whitelist if whitelist is not None else settings.whitelist_symbols
    seen: dict[str, list[str]] = json.loads(getattr(state, seen_col) or "{}")
    new_headlines, updated_seen = news.get_new_ticker_headlines(symbols, seen)
    setattr(state, seen_col, json.dumps(updated_seen))
    db.commit()
    if new_headlines:
        logger.info("Trigger: %d świeżych nagłówków per-ticker (np. %s)", len(new_headlines), new_headlines[0]["title"][:80])
    return bool(new_headlines), new_headlines


def average_cost_basis(db: Session, symbol: str, *, venue: str = "alpaca") -> float | None:
    """Weighted-average entry price of the CURRENTLY held quantity of `symbol`
    on `venue`, walked from that venue's trade history (buys add, sells remove
    proportionally). Returns None if nothing is currently held. Used by the
    take-profit/stop-loss engine to know each position's entry price without
    storing extra state."""
    trades = db.execute(
        select(Trade).where(Trade.symbol == symbol, Trade.venue == venue).order_by(Trade.timestamp.asc())
    ).scalars().all()

    qty = 0.0
    cost = 0.0  # total quote-currency cost of the currently-held quantity
    for t in trades:
        if t.side.upper() == "BUY":
            qty += t.quantity
            cost += t.usdt_value
        else:  # SELL removes at the running average cost
            if qty > 1e-12:
                avg = cost / qty
                sell_qty = min(t.quantity, qty)
                cost -= avg * sell_qty
                qty -= sell_qty
            if qty <= 1e-12:
                qty = 0.0
                cost = 0.0

    if qty <= 1e-12:
        return None
    return cost / qty


def _set_stop_loss_cooldown(db: Session, symbol: str, minutes: int, *, venue: str = "alpaca") -> None:
    if minutes <= 0:
        return
    state = risk_manager.get_state(db)
    col = _state_col("cooldowns", venue)
    cooldowns = json.loads(getattr(state, col) or "{}")
    cooldowns[symbol] = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    setattr(state, col, json.dumps(cooldowns))
    db.commit()


def stop_loss_cooldown_active(db: Session, symbol: str, *, venue: str = "alpaca") -> tuple[bool, str | None]:
    """True (with a human reason) if `symbol` is still inside its post-stop-loss
    cooldown window and must not be re-bought yet."""
    state = risk_manager.get_state(db)
    cooldowns = json.loads(getattr(state, _state_col("cooldowns", venue)) or "{}")
    until = cooldowns.get(symbol)
    if not until:
        return False, None
    until_dt = datetime.fromisoformat(until)
    now = datetime.now(timezone.utc)
    if now >= until_dt:
        return False, None
    mins_left = int((until_dt - now).total_seconds() // 60) + 1
    return True, f"Cooldown po stop-lossie: {symbol} zablokowany do odkupu jeszcze ~{mins_left} min"


def _record_stop_loss_streak_and_cooldown(db: Session, symbol: str, settings: Settings, *, venue: str = "alpaca") -> None:
    """Book a stop-loss on `symbol` and set the re-buy cooldown. If the ticker
    has stop-lossed auto_blacklist_stop_count times within
    auto_blacklist_window_hours it is QUARANTINED for auto_blacklist_hours (a
    long cooldown) instead of the normal short one -- a setup that keeps failing
    is parked rather than retried into the same loss."""
    now = datetime.now(timezone.utc)
    minutes = settings.stop_loss_cooldown_minutes
    if settings.auto_blacklist_stop_count > 0:
        state = risk_manager.get_state(db)
        col = _state_col("streak", venue)
        streaks: dict[str, list[str]] = json.loads(getattr(state, col) or "{}")
        window_start = now - timedelta(hours=settings.auto_blacklist_window_hours)
        recent = [ts for ts in streaks.get(symbol, []) if _parse_iso(ts) and _parse_iso(ts) >= window_start]
        recent.append(now.isoformat())
        streaks[symbol] = recent[-settings.auto_blacklist_stop_count:]
        setattr(state, col, json.dumps(streaks))
        db.commit()
        if len(recent) >= settings.auto_blacklist_stop_count:
            minutes = max(minutes, settings.auto_blacklist_hours * 60)
            logger.info(
                "Auto-blacklist: %s zaliczył %d stop-lossów w %dh — kwarantanna na %dh",
                symbol, len(recent), settings.auto_blacklist_window_hours, settings.auto_blacklist_hours,
            )
    _set_stop_loss_cooldown(db, symbol, minutes, venue=venue)


def _parse_iso(value: str):
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def last_entry_time(db: Session, symbol: str, *, venue: str = "alpaca") -> datetime | None:
    """Timestamp of the most recent BUY of `symbol` on `venue`, used to enforce
    a minimum holding period before a non-stop exit may fire."""
    row = db.execute(
        select(Trade)
        .where(Trade.symbol == symbol, Trade.venue == venue, Trade.side.ilike("BUY"))
        .order_by(Trade.timestamp.desc())
        .limit(1)
    ).scalars().first()
    return row.timestamp if row else None


def _within_min_hold(db: Session, symbol: str, settings: Settings, *, venue: str = "alpaca") -> bool:
    """True if `symbol` was bought too recently for a non-stop exit to fire."""
    if settings.min_hold_minutes <= 0:
        return False
    entered = last_entry_time(db, symbol, venue=venue)
    if entered is None:
        return False
    if entered.tzinfo is None:
        entered = entered.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - entered < timedelta(minutes=settings.min_hold_minutes)


def count_new_entries_today(db: Session, *, venue: str = "alpaca") -> int:
    """How many automated BUY trades this venue has executed today (UTC) --
    drives the per-day new-entry cap that curbs churn on a small account."""
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = db.execute(
        select(Trade).where(
            Trade.venue == venue,
            Trade.side.ilike("BUY"),
            Trade.is_manual.is_(False),
            Trade.timestamp >= start,
        )
    ).scalars().all()
    return len(rows)


def compute_market_regime(market_data: dict, market_context: dict, settings: Settings) -> dict:
    """Cheap risk-on / neutral / risk-off read of the broad market from signals
    we already fetch: the benchmark's own 50/200 trend, the VIX fear level, and
    today's S&P move. Fed to Claude as context every cycle; also gates BUYs to
    defensive/inverse names while risk-off (see regime_gate_enabled)."""
    reasons: list[str] = []
    score = 0

    bench = market_data.get(settings.benchmark_symbol, {})
    trend = (bench.get("technical") or {}).get("sma50_vs_sma200_1h")
    if trend == "below":
        score -= 1
        reasons.append(f"{settings.benchmark_symbol}: SMA50 < SMA200 (trend spadkowy)")
    elif trend == "above":
        score += 1
        reasons.append(f"{settings.benchmark_symbol}: SMA50 > SMA200 (trend wzrostowy)")

    vix = market_context.get("vix_level")
    if vix is not None and vix >= settings.regime_vix_risk_off:
        score -= 1
        reasons.append(f"VIX {vix} ≥ {settings.regime_vix_risk_off} (podwyższony strach)")

    sp = market_context.get("sp500_change_pct")
    if sp is not None:
        if sp <= -1.0:
            score -= 1
            reasons.append(f"S&P dziś {sp}%")
        elif sp >= 1.0:
            score += 1

    if score <= -2:
        regime = "risk_off"
    elif score >= 1:
        regime = "risk_on"
    else:
        regime = "neutral"
    return {"regime": regime, "score": score, "reasons": reasons}


def risk_based_size_cap(settings: Settings, portfolio: dict, stop_dist_pct: float) -> float:
    """Cap on a BUY's size (% of free cash) so that hitting its stop costs at
    most risk_per_trade_pct of the WHOLE account. Returns 100.0 (no cap) when
    disabled or when inputs are missing. Composed with the other size limits via
    min(), so it can only ever SHRINK a position, never grow it."""
    if settings.risk_per_trade_pct <= 0 or stop_dist_pct <= 0:
        return 100.0
    total = portfolio.get("total_value_usdt", 0.0)
    free = portfolio.get("usdt_balance", 0.0)
    if total <= 0 or free <= 0:
        return 100.0
    risk_usd = total * settings.risk_per_trade_pct / 100
    max_position_value = risk_usd / (stop_dist_pct / 100)
    return round(max_position_value / free * 100, 4)


def dynamic_stop_loss_pct(settings: Settings, vol_pct: float | None) -> float:
    """Volatility-scaled (ATR-style) hard-stop distance in %. Scales with the
    ticker's own 1h-return volatility so the stop sits OUTSIDE normal noise --
    fixing the whipsaw where a fixed 2% stop shakes you out of a routine wobble
    and you sell the dip. Falls back to the fixed stop_loss_pct when scaling is
    disabled (mult=0) or volatility is unknown (insufficient history)."""
    if settings.stop_loss_vol_mult <= 0 or not vol_pct:
        return settings.stop_loss_pct
    scaled = settings.stop_loss_vol_mult * vol_pct
    return max(settings.stop_loss_min_pct, min(settings.stop_loss_max_pct, scaled))


def _reward_levels(settings: Settings, stop_pct: float) -> tuple[float, float, float]:
    """Reward thresholds COUPLED to the (vol-scaled) stop distance so the
    risk/reward ratio stays proportional instead of inverted: take-profit ARM =
    stop * reward_risk_ratio, trailing distance = stop * trailing_stop_frac,
    partial-take level = stop * partial_take_profit_r. Falls back to the fixed
    take_profit_pct / trailing_stop_pct when coupling is off (reward_risk_ratio
    <= 0) or the stop distance is unknown (stop_pct <= 0)."""
    if settings.reward_risk_ratio > 0 and stop_pct > 0:
        tp_arm = stop_pct * settings.reward_risk_ratio
        trailing = stop_pct * settings.trailing_stop_frac
    else:
        tp_arm = settings.take_profit_pct
        trailing = settings.trailing_stop_pct
    partial_r = stop_pct * settings.partial_take_profit_r if stop_pct > 0 else settings.take_profit_pct
    return tp_arm, trailing, partial_r


def _decide_mechanical_exit(
    settings: Settings,
    base: str,
    basis: float,
    price: float,
    peak: float,
    stop_pct: float | None = None,
    *,
    partial_taken: bool = False,
) -> tuple[str | None, float, str | None]:
    """Returns (reason, sell_pct, kind) for a held position, or (None, 0.0,
    None) to hold. `kind` is one of "stop" / "trailing" / "take_profit" /
    "partial". The hard stop-loss is a floor from the entry price (`stop_pct`,
    defaulting to the fixed stop_loss_pct) and always exits 100%. The upside is
    either a trailing stop (let winners run, arm at the coupled take-profit
    level) or a fixed take-profit; plus an optional one-shot PARTIAL sell once
    the position first clears +partial_r, which locks in a realized win while
    the remainder keeps running under the trailing stop."""
    change_pct = (price - basis) / basis * 100
    stop = settings.stop_loss_pct if stop_pct is None else stop_pct
    tp_arm, trailing, partial_r = _reward_levels(settings, stop)

    if stop > 0 and change_pct <= -stop:
        return (
            f"Stop-loss: {base} {change_pct:.1f}% od wejścia (stop {stop:.1f}%, średnia {basis:.2f} → {price:.2f})",
            100.0,
            "stop",
        )

    if settings.trailing_stop_enabled:
        armed = tp_arm <= 0 or peak >= basis * (1 + tp_arm / 100)
        if armed and trailing > 0 and price <= peak * (1 - trailing / 100):
            drop = (price - peak) / peak * 100
            return (
                f"Trailing-stop: {base} spadł {drop:.1f}% od szczytu {peak:.2f} "
                f"(wejście {basis:.2f}, zysk +{change_pct:.1f}%)",
                100.0,
                "trailing",
            )
    elif tp_arm > 0 and change_pct >= tp_arm:
        return (
            f"Take-profit: {base} +{change_pct:.1f}% od wejścia (średnia {basis:.2f} → {price:.2f})",
            100.0,
            "take_profit",
        )

    # One-shot partial profit-taking: sell part of the position the first time
    # it clears +partial_r, then let the rest run under the trailing stop above.
    if (
        settings.partial_take_profit_enabled
        and not partial_taken
        and settings.partial_take_profit_frac > 0
        and partial_r > 0
        and change_pct >= partial_r
    ):
        pct = settings.partial_take_profit_frac * 100
        return (
            f"Częściowa realizacja: {base} +{change_pct:.1f}% — sprzedaż {pct:.0f}% przy +{partial_r:.1f}%, "
            f"reszta biegnie z trailingiem (wejście {basis:.2f} → {price:.2f})",
            pct,
            "partial",
        )

    return None, 0.0, None


def check_take_profit_stop_loss(
    db: Session,
    settings: Settings,
    broker,
    portfolio: dict,
    session_info: SessionInfo | None = None,
    *,
    venue: str = "alpaca",
    whitelist: list[str] | None = None,
    always_open: bool = False,
) -> list[Trade]:
    """Mechanical exits run on every poll, WITHOUT asking Claude: hard stop-loss
    from entry, plus either a trailing stop (default -- lets winners run) or a
    fixed take-profit. Respects the same stop/halt gate as any automated trade
    -- if the user pressed STOP, these don't fire either. Also skipped while the
    market is closed (unless always_open, e.g. the 24-7 crypto venue), since a
    SELL order would just be rejected. Defaults to the regular session when no
    session_info is given, for callers (and the many existing tests) that don't
    care about market-hours gating. Tracks each position's peak price for the
    trailing stop and clears it once the position is closed."""
    session = session_info.session if session_info is not None else market_hours.REGULAR
    tradable = True if always_open else market_hours.is_tradable_session(session)
    if not tradable or not risk_manager.can_trade_automated(db, venue).approved:
        return []

    symbols = whitelist if whitelist is not None else settings.whitelist_symbols
    state = risk_manager.get_state(db)
    peaks_col = _state_col("peaks", venue)
    partial_col = _state_col("partial", venue)
    peaks: dict[str, float] = json.loads(getattr(state, peaks_col) or "{}")
    partials: dict[str, bool] = json.loads(getattr(state, partial_col) or "{}")
    new_peaks: dict[str, float] = {}
    new_partials: dict[str, bool] = {}
    executed: list[Trade] = []

    for symbol in symbols:
        if symbol not in portfolio["prices"]:
            # Keep any existing peak / partial mark we can't refresh this cycle.
            if symbol in peaks:
                new_peaks[symbol] = peaks[symbol]
            if symbol in partials:
                new_partials[symbol] = partials[symbol]
            continue
        base = _base_asset(symbol, settings.quote_currency)
        qty = portfolio["balances"].get(base, 0.0)
        basis = average_cost_basis(db, symbol, venue=venue) if qty > 0 else None
        if qty <= 0 or basis is None or basis <= 0:
            continue  # not held -> drop any stale peak / partial mark

        price = portfolio["prices"][symbol]
        if qty * price < MIN_SELL_NOTIONAL_USD:
            # Unsellable dust (below Alpaca's min order) -- not a real position.
            # Drop its peak and stop trying to exit it every poll.
            continue
        peak = max(peaks.get(symbol, basis), price)
        already_partial = bool(partials.get(symbol))

        # Volatility-scaled stop distance: fetch a short 1h history for this
        # held symbol and derive a stop that sits outside its normal noise.
        vol_pct = None
        try:
            closes = [float(r[4]) for r in broker.get_klines(symbol, "1h", 30)]
            vol_pct = compute_volatility_pct(closes)
        except Exception:
            logger.warning("Volatility fetch failed for %s, using fixed stop", symbol, exc_info=True)
        stop_pct = dynamic_stop_loss_pct(settings, vol_pct)

        reason, sell_pct, kind = _decide_mechanical_exit(
            settings, base, basis, price, peak, stop_pct=stop_pct, partial_taken=already_partial
        )
        if kind is None:
            new_peaks[symbol] = peak  # still holding, remember the peak
            if already_partial:
                new_partials[symbol] = True
            continue

        # Minimum holding period: a just-opened position may only be exited by
        # the HARD stop-loss -- trailing / take-profit / partial are suppressed
        # so the bot doesn't round-trip on the spread minutes after entering.
        if kind != "stop" and _within_min_hold(db, symbol, settings, venue=venue):
            new_peaks[symbol] = peak
            if already_partial:
                new_partials[symbol] = True
            continue

        # A partial slice below the broker minimum is pointless -- skip it this
        # poll and let it fire once the position (or price) is larger.
        if kind == "partial" and qty * (sell_pct / 100) * price < MIN_SELL_NOTIONAL_USD:
            new_peaks[symbol] = peak
            continue

        decision = Decision(
            symbol=symbol,
            action=TradeAction.SELL,
            size_pct=sell_pct,
            confidence=1.0,
            reasoning=reason,
            triggered_by=TriggerType.PRICE_MOVE,
            executed=False,
            venue=venue,
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)

        try:
            trade = _execute_trade(
                db=db,
                broker=broker,
                settings=settings,
                symbol=symbol,
                action="SELL",
                size_pct=sell_pct,
                portfolio=portfolio,
                decision=decision,
                is_manual=False,
                session=session,
                venue=venue,
            )
        except (ValueError, AlpacaAPIError, EToroAPIError) as exc:
            # A SELL can still fail for other reasons (broker hiccup, a
            # rounding/qty rejection, ...), so the real exception text is
            # surfaced instead of a one-size-fits-all guess. Don't crash the
            # cycle (that would silently skip every other position's exit too
            # and kill the Claude leg) -- log it, mark the decision, keep
            # tracking the peak, and let this exit retry next cycle.
            logger.warning("Mechaniczne wyjście %s nie powiodło się, odłożone", symbol, exc_info=True)
            decision.rejection_reason = f"Wyjście niewykonalne: {exc}"
            db.commit()
            new_peaks[symbol] = peak
            if already_partial:
                new_partials[symbol] = True
            continue

        executed.append(trade)
        logger.info("Mechaniczne wyjście: %s", reason)
        if kind == "stop":
            _record_stop_loss_streak_and_cooldown(db, symbol, settings, venue=venue)
            # full exit -> peak & partial mark intentionally dropped
        elif kind == "partial":
            # position stays open on the remainder: keep the peak and remember
            # the partial is already booked so it fires only once.
            new_peaks[symbol] = peak
            new_partials[symbol] = True
        # trailing / take-profit fully close the position -> drop peak & mark

    setattr(state, peaks_col, json.dumps(new_peaks))
    setattr(state, partial_col, json.dumps(new_partials))
    db.commit()
    return executed


def _mark_analysis_done_today(db: Session, *, venue: str = "alpaca") -> None:
    """Called only after advisor.decide() actually succeeds, so a transient
    Claude/network failure doesn't burn today's scheduled-fallback trigger
    (and leaves the heartbeat overdue, retrying next poll)."""
    state = risk_manager.get_state(db)
    _set_analysis_marks(state, venue, date.today().isoformat(), datetime.now(timezone.utc).isoformat())
    db.commit()


RECENT_TRADES_FOR_LEARNING = 15


def compute_symbol_stats(db: Session, *, venue: str = "alpaca") -> dict:
    """Per-symbol realized track record on a venue, walked from trade history
    (running average cost, P&L booked on each SELL): closed trades, wins,
    losses, win rate, realized P&L. Turns the learning loop QUANTITATIVE --
    Claude sees 'my MSTR breakouts are 1/6' instead of a vague memory -- and
    drives auto-demotion of chronically losing setups."""
    from collections import defaultdict

    trades = db.execute(
        select(Trade).where(Trade.venue == venue).order_by(Trade.timestamp.asc())
    ).scalars().all()
    qty: dict[str, float] = defaultdict(float)
    cost: dict[str, float] = defaultdict(float)
    acc: dict[str, dict] = defaultdict(lambda: {"closed": 0, "wins": 0, "losses": 0, "realized_pnl": 0.0})
    for t in trades:
        s = t.symbol
        if t.side.upper() == "BUY":
            qty[s] += t.quantity
            cost[s] += t.usdt_value
        else:
            held = qty[s]
            if held <= 1e-12:
                continue
            avg = cost[s] / held
            sell_qty = min(t.quantity, held)
            pnl = (t.price - avg) * sell_qty
            a = acc[s]
            a["closed"] += 1
            a["realized_pnl"] += pnl
            a["wins" if pnl >= 0 else "losses"] += 1
            cost[s] -= avg * sell_qty
            qty[s] -= sell_qty
            if qty[s] <= 1e-12:
                qty[s] = 0.0
                cost[s] = 0.0
    return {
        s: {
            "closed": a["closed"],
            "wins": a["wins"],
            "losses": a["losses"],
            "win_rate": round(a["wins"] / a["closed"] * 100, 1) if a["closed"] else None,
            "realized_pnl": round(a["realized_pnl"], 2),
        }
        for s, a in acc.items()
    }


def count_open_positions(portfolio: dict, settings: Settings, symbols: list[str]) -> int:
    """Number of currently-held (non-dust) positions in `symbols` -- drives the
    per-venue concurrency cap that bounds correlated exposure."""
    n = 0
    for sym in symbols:
        qty = portfolio["balances"].get(_base_asset(sym, settings.quote_currency), 0.0)
        price = portfolio["prices"].get(sym)
        if qty > 0 and price and qty * price >= MIN_SELL_NOTIONAL_USD:
            n += 1
    return n


def build_performance_context(
    db: Session, settings: Settings, portfolio: dict, *, venue: str = "alpaca", whitelist: list[str] | None = None
) -> dict:
    """Gives Claude its own track record so it can actually learn instead of
    analysing every cycle from a blank slate: each currently-held position
    with its entry price and live unrealized P&L, plus the most recent
    executed trades and the reasoning behind them. This is the difference
    between 'fresh analyst every 15 min' and 'trader who remembers what just
    worked or lost'. Scoped to `venue` so each portfolio learns from its own
    positions/trades."""
    symbols = whitelist if whitelist is not None else settings.whitelist_symbols
    open_positions = []
    for symbol in symbols:
        base = _base_asset(symbol, settings.quote_currency)
        qty = portfolio["balances"].get(base, 0.0)
        price = portfolio["prices"].get(symbol)
        if qty <= 0 or price is None:
            continue
        basis = average_cost_basis(db, symbol, venue=venue)
        if basis is None or basis <= 0:
            continue
        open_positions.append(
            {
                "symbol": symbol,
                "qty": round(qty, 6),
                "entry_price": round(basis, 2),
                "current_price": round(price, 2),
                "unrealized_pnl_pct": round((price - basis) / basis * 100, 2),
                "unrealized_pnl_usd": round((price - basis) * qty, 2),
            }
        )

    recent = db.execute(
        select(Trade).where(Trade.venue == venue).order_by(Trade.timestamp.desc()).limit(RECENT_TRADES_FOR_LEARNING)
    ).scalars().all()
    recent_trades = [
        {
            "time": t.timestamp.isoformat(),
            "symbol": t.symbol,
            "side": t.side,
            "price": round(t.price, 2),
            "value_usd": round(t.usdt_value, 2),
            "reason": (t.decision.reasoning[:180] if t.decision and t.decision.reasoning else ""),
        }
        for t in recent
    ]

    # Am I actually beating buy-and-hold? Feeding this back makes Claude
    # accountable to a benchmark instead of just churning. Scorecard/benchmark
    # is account-wide (Alpaca-driven) for now -- the crypto venue skips it.
    card = scorecard.compute_scorecard(db, settings, portfolio) if venue == "alpaca" else None

    # Durable weekly-review lessons -- memory that outlives the recent-trade
    # window. Imported here (not at module top) to avoid a circular import
    # via self_review -> scorecard -> ... -> trading_engine test doubles.
    from app.services import self_review

    lessons = [l.get("lesson", "") for l in self_review.get_lessons(db)]

    return {
        "open_positions": open_positions,
        "recent_trades": recent_trades,
        "scorecard": card,
        "lessons_learned": lessons,
        # Quantitative per-symbol track record -- what actually works for me.
        "per_symbol_stats": compute_symbol_stats(db, venue=venue),
    }


def run_cycle(
    db: Session,
    settings: Settings,
    broker,
    news: NewsClient,
    advisor: ClaudeAdvisor,
    market_ctx: MarketContextClient | None = None,
    force: bool = False,
    *,
    venue: str = "alpaca",
    whitelist: list[str] | None = None,
    always_open: bool = False,
) -> Decision | None:
    """force=True bypasses the trigger gate and always asks Claude -- this is
    what the dashboard's "Wymuś analizę" button needs. Without it the manual
    button just ran a normal cycle, which returns None (does nothing) whenever
    the daily analysis already ran and no price moved past the threshold --
    exactly the "clicked it, nothing happened" behaviour reported from the
    dashboard.

    `venue`/`whitelist`/`always_open` select the portfolio: the default Alpaca
    (day, US stocks/ETFs, market-hours gated) path is behaviour-identical; the
    eToro crypto/forex venue passes always_open=True (trades 24/7) and skips the
    account-wide day/week risk + SPY benchmark, which stay Alpaca-driven."""
    symbols = whitelist if whitelist is not None else settings.whitelist_symbols
    portfolio = compute_portfolio(db, settings, broker, venue=venue, whitelist=symbols)
    if venue == "alpaca":
        state = risk_manager.update_portfolio_value(db, settings, portfolio["total_value_usdt"])
        scorecard.update_benchmark_baseline(db, settings, portfolio)
    else:
        state = risk_manager.get_state(db)

    if always_open:
        session_info = None
        tradable = True
    else:
        session_info = market_hours.get_session_info(broker)
        tradable = _is_tradable_session(session_info)

    # Mechanical take-profit / stop-loss runs every scheduled poll, before we
    # even decide whether to ask Claude -- this is what makes the bot actively
    # rotate capital (realize gains, cut losses) instead of buying and holding.
    # A manual "Wymuś analizę" (force) stays a pure Claude read and skips this.
    if not force:
        exits = check_take_profit_stop_loss(
            db, settings, broker, portfolio, session_info, venue=venue, whitelist=symbols, always_open=always_open
        )
        if exits:
            # Positions changed -- refresh the snapshot so the Claude leg below
            # sees post-exit balances/cash.
            portfolio = compute_portfolio(db, settings, broker, venue=venue, whitelist=symbols)

    # Stocks/ETFs don't trade 24/7 like crypto -- a scheduled poll while the
    # market is closed has nothing useful to do (any order would just be
    # rejected) and must not burn Claude budget on it. A manual "Wymuś analizę"
    # still runs so the user can see Claude's read on demand; it just can't
    # execute.
    if not force and not tradable:
        return None

    triggered, trigger_reason = check_trigger(db, settings, portfolio["prices"], venue=venue)

    # A brand-new per-ticker headline (earnings, material single-stock news)
    # wakes Claude on its own, independent of any price move -- especially
    # important pre-/after-market where thin trading means the price can lag
    # the news print by minutes. Always checked (even on a force/price-move
    # cycle) so the "seen headlines" state stays current either way.
    news_triggered, fresh_headlines = check_news_trigger(db, settings, news, venue=venue, whitelist=symbols)
    if news_triggered and not triggered:
        triggered = True
        trigger_reason = TriggerType.NEWS_EVENT

    if force:
        trigger_reason = TriggerType.MANUAL
    elif not triggered:
        return None

    trade_check = risk_manager.can_trade_automated(db, venue)

    # On a *scheduled* cycle, skip the (paid) Claude call entirely when
    # automated trading is halted or paused -- the decision could only ever be
    # rejected, so calling Claude would burn budget for nothing, potentially
    # on every triggered cycle for days. A manual "Wymuś analizę" (force=True)
    # still runs so the user can see Claude's read on demand; it just won't
    # execute a trade while stopped (the trade_check gate below still applies).
    if not force and not trade_check.approved:
        decision = Decision(
            symbol=None,
            action=TradeAction.HOLD,
            size_pct=0.0,
            confidence=0.0,
            reasoning=f"Cykl pominięty bez pytania Claude (oszczędność budżetu): {trade_check.reason}",
            market_data_snapshot="{}",
            news_snapshot="[]",
            market_context_snapshot="{}",
            triggered_by=trigger_reason,
            executed=False,
            rejection_reason=trade_check.reason,
            venue=venue,
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    market_data = {}
    for symbol in symbols:
        if symbol not in portfolio["prices"]:
            continue  # broker couldn't price this symbol this cycle -- see compute_portfolio
        try:
            klines_24 = broker.get_klines(symbol, "1h", 24)
            indicator_closes = [float(row[4]) for row in broker.get_klines(symbol, "1h", 200)]
        except Exception:
            logger.warning("Failed to fetch klines for %s, excluding it from this cycle", symbol, exc_info=True)
            continue
        # Token diet: with 11 whitelisted tickers, shipping 24 raw hourly bars
        # each (~260 JSON rows) dominated the prompt and the API bill. The
        # indicators are computed locally from the full 200-bar history anyway
        # -- Claude only needs the recent tape plus a 24h summary, not the
        # whole raw series.
        closes_24 = [float(row[4]) for row in klines_24 if row]
        change_24h_pct = (
            round((closes_24[-1] - closes_24[0]) / closes_24[0] * 100, 2)
            if len(closes_24) >= 2 and closes_24[0] > 0
            else None
        )
        market_data[symbol] = {
            "price": portfolio["prices"][symbol],
            "change_24h_pct": change_24h_pct,
            "recent_bars_1h": klines_24[-8:],
            "technical": compute_technical_indicators(indicator_closes),
        }
    # Only offer Claude symbols it actually has data for this cycle -- a symbol
    # missing from market_data (Alpaca failure above) must not be a choosable
    # BUY/SELL target.
    tradable_symbols = list(market_data.keys())
    headlines = news.get_headlines([_base_asset(s, settings.quote_currency) for s in symbols])
    # The headlines that actually TRIGGERED this cycle (fresh earnings print,
    # breaking single-stock news) must stand out from routine background news,
    # or Claude can't tell what it's reacting to. Flag and front-load them.
    if fresh_headlines:
        for h in fresh_headlines:
            h["just_published"] = True
        seen_titles = {h["title"] for h in fresh_headlines}
        headlines = fresh_headlines + [h for h in headlines if h["title"] not in seen_titles]
    global_context = market_ctx.get_market_context() if market_ctx is not None else {}
    # Broad-market regime (risk-on / neutral / risk-off) from the benchmark
    # trend + VIX + today's tape. Always given to Claude; equities-only (the
    # crypto venue has no SPY/VIX regime), so the eToro path skips the gate.
    regime = compute_market_regime(market_data, global_context, settings) if venue == "alpaca" else {"regime": "neutral", "score": 0, "reasons": []}
    if venue == "alpaca":
        # Cache it so /api/status can show the regime chip without recomputing.
        state.market_regime_json = json.dumps(regime)
        db.commit()
    performance_context = build_performance_context(db, settings, portfolio, venue=venue, whitelist=symbols)
    # Upcoming earnings per ticker (days until next report). Best-effort --
    # never blocks the cycle if the calendar lookup fails. Only meaningful for
    # equities -- crypto/forex have no earnings, so the eToro venue skips it.
    if venue == "alpaca":
        try:
            earnings_days = earnings_calendar.get_days_until_earnings(symbols)
        except Exception:
            logger.warning("Earnings calendar lookup failed, continuing without it", exc_info=True)
            earnings_days = {}
    else:
        earnings_days = {}
    earnings_context = {
        sym: {"days_until_earnings": days} for sym, days in earnings_days.items()
    }

    day_loss_budget_left_pct = max(
        0.0,
        settings.daily_loss_limit_pct
        - ((state.day_start_value - portfolio["total_value_usdt"]) / state.day_start_value * 100
           if state.day_start_value > 0 else 0),
    )
    risk_context = {
        "daily_loss_limit_pct": settings.daily_loss_limit_pct,
        "day_loss_budget_remaining_pct": day_loss_budget_left_pct,
        "max_position_pct": settings.max_position_pct,
        "automated_trading_currently_allowed": trade_check.approved,
        "auto_take_profit_arm_pct": settings.take_profit_pct,
        "auto_stop_loss_pct": settings.stop_loss_pct,
        "auto_trailing_stop_pct": settings.trailing_stop_pct if settings.trailing_stop_enabled else None,
        "exit_note": (
            "Wyjścia z pozycji są w pełni automatyczne: twardy stop-loss -auto_stop_loss_pct od "
            "wejścia, a po zysku +auto_take_profit_arm_pct uzbraja się trailing-stop (sprzedaż gdy "
            "cena spadnie auto_trailing_stop_pct od szczytu) — zyski mogą rosnąć. Skup się WYŁĄCZNIE "
            "na trafnym WEJŚCIU; nie planuj wyjścia."
        ),
        # Forward-looking event risk: mechanical stop-loss can't protect
        # against an earnings gap, so Claude should avoid opening a fresh
        # position right before a report (the engine also hard-blocks new BUYs
        # inside earnings_blackout_days as a backstop).
        "upcoming_earnings": earnings_context,
        "earnings_note": (
            "upcoming_earnings podaje ile dni do najbliższego raportu wyników danego tickera. "
            "Stop-loss NIE chroni przed luką po earnings (cena przeskakuje stopa). Nie otwieraj "
            f"nowej pozycji na tickerze raportującym w ciągu {settings.earnings_blackout_days} dni "
            "— takie BUY i tak zostanie odrzucone przez silnik."
        ),
        # Broad-market regime read. In "risk_off" the engine only lets defensive
        # / inverse names be bought (the rest is forced HOLD), so lean that way.
        "market_regime": regime,
        "regime_note": (
            "market_regime.regime to ogólny reżim rynku (risk_on / neutral / risk_off) z trendu "
            "benchmarku, VIX-a i dzisiejszej sesji. W risk_off bądź defensywny: silnik i tak "
            f"pozwoli KUPIĆ tylko nazwy defensywne/odwrotne ({', '.join(settings.defensive_symbol_list)}), "
            "resztę wymusi na HOLD. Wchodź tylko w realnie mocne setupy — nie handluj dla samego handlu."
        ),
        "min_buy_confidence": settings.min_buy_confidence,
        "conviction_note": (
            f"Automatyczne BUY z confidence poniżej {settings.min_buy_confidence} jest ODRZUCANE — "
            "gotówka to też pozycja. Podawaj realną pewność; nie zawyżaj, żeby wymusić wejście."
        ),
    }

    decision_data = advisor.decide(
        whitelist=tradable_symbols,
        market_data=market_data,
        news=headlines,
        portfolio=portfolio,
        risk_context=risk_context,
        market_context=global_context,
        performance_context=performance_context,
        trigger_reason=trigger_reason.value,
    )
    _mark_analysis_done_today(db, venue=venue)
    budget_tracker.record_usage_cost(db, decision_data.cost_usd)

    # Volatility-aware sizing: scale a BUY down for a more-volatile ticker so
    # one wild name (MSTR) can't dominate P&L. HOLD/SELL are untouched.
    effective_size_pct = decision_data.size_pct
    if decision_data.action == "BUY":
        ticker_vol = (market_data.get(decision_data.symbol) or {}).get("technical", {}).get("volatility_pct_1h")
        effective_size_pct = volatility_adjusted_size(settings, decision_data.size_pct, ticker_vol)
        # Risk-based cap: hitting this ticker's (vol-scaled) stop must not cost
        # more than risk_per_trade_pct of the whole account -- a wider stop
        # implies a smaller slice. Composed via min(), so it only ever shrinks.
        stop_dist = dynamic_stop_loss_pct(settings, ticker_vol)
        effective_size_pct = round(min(effective_size_pct, risk_based_size_cap(settings, portfolio, stop_dist)), 4)
        # Wide-spread / thinner names pay more on every round trip -> haircut
        # their size so they only earn a slot when the edge is proportionally big.
        if decision_data.symbol in settings.high_spread_symbol_list and settings.high_spread_size_scale < 1.0:
            effective_size_pct = round(effective_size_pct * settings.high_spread_size_scale, 4)

    decision = Decision(
        symbol=decision_data.symbol,
        action=TradeAction(decision_data.action),
        size_pct=effective_size_pct,
        confidence=decision_data.confidence,
        reasoning=decision_data.reasoning,
        market_data_snapshot=json.dumps(market_data, default=str),
        news_snapshot=json.dumps(headlines),
        market_context_snapshot=json.dumps(global_context),
        triggered_by=trigger_reason,
        executed=False,
        venue=venue,
    )

    if not trade_check.approved:
        decision.rejection_reason = trade_check.reason
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    if decision_data.action == "HOLD":
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    # A force=True "Wymuś analizę" still asks Claude while the market is closed
    # (so the user can see its read on demand), but a resulting BUY/SELL can't
    # actually execute until the regular session resumes -- Alpaca would just
    # reject it.
    if not tradable:
        decision.rejection_reason = _session_closed_reason(session_info)
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    validation = risk_manager.validate_trade(
        settings=settings,
        symbol=decision_data.symbol,
        action=decision_data.action,
        size_pct=effective_size_pct,
        whitelist=symbols,
    )
    if not validation.approved:
        decision.rejection_reason = validation.reason
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    # Post-stop-loss cooldown: refuse to re-buy a coin we just cut, even if
    # Claude wants back in -- this is the anti-churn guard for a small account.
    if decision_data.action == "BUY":
        # Conviction floor: a weak-edge BUY is not worth the spread -- reject it
        # outright rather than churn the account (cash is a valid position).
        if settings.min_buy_confidence > 0 and decision_data.confidence < settings.min_buy_confidence:
            decision.rejection_reason = (
                f"Zbyt niska pewność: {decision_data.confidence:.2f} < próg {settings.min_buy_confidence:.2f} "
                "— wejście pominięte (gotówka to też pozycja)"
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision

        # Regime gate: while the broad market is risk-off, only defensive /
        # inverse names may be OPENED; everything else is forced to HOLD.
        if (
            settings.regime_gate_enabled
            and regime.get("regime") == "risk_off"
            and decision_data.symbol not in settings.defensive_symbol_list
        ):
            decision.rejection_reason = (
                f"Reżim risk-off ({'; '.join(regime.get('reasons') or []) or 'sygnały rynku'}) — "
                f"nowe wejście tylko na nazwach defensywnych/odwrotnych ({', '.join(settings.defensive_symbol_list)})"
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision

        # Per-day new-entry cap: stop a small account churning on many low-edge
        # entries. SELL/HOLD and mechanical exits are unaffected.
        if (
            settings.max_new_positions_per_day > 0
            and count_new_entries_today(db, venue=venue) >= settings.max_new_positions_per_day
        ):
            decision.rejection_reason = (
                f"Limit nowych wejść na dziś osiągnięty ({settings.max_new_positions_per_day}) — "
                "nowe BUY wstrzymane do jutra (anty-churn)"
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision

        # Entry-confluence filter: a BUY must trade WITH the trend/momentum
        # (score >= threshold, not overbought). Entry edge is the first-order
        # driver of profit -- this is the biggest lever on the win rate.
        if settings.entry_filter_enabled:
            tech = (market_data.get(decision_data.symbol) or {}).get("technical", {})
            sig = signals.entry_confluence(settings, tech)
            if not sig.ok:
                decision.rejection_reason = (
                    f"Filtr konfluencji: brak zgodnego sygnału wejścia dla {decision_data.symbol} "
                    f"(score {sig.score}/{settings.entry_min_score}"
                    f"{'; ' + '; '.join(sig.reasons) if sig.reasons else ''})"
                )
                db.add(decision)
                db.commit()
                db.refresh(decision)
                return decision

        # Concurrency cap: bound correlated exposure (the whitelist is mostly
        # tech beta -> many open names are really one bet). Scaling INTO an
        # already-held name is exempt.
        base_sym = _base_asset(decision_data.symbol, settings.quote_currency)
        already_held = (
            portfolio["balances"].get(base_sym, 0.0) * portfolio["prices"].get(decision_data.symbol, 0.0)
            >= MIN_SELL_NOTIONAL_USD
        )
        if (
            settings.max_concurrent_positions > 0
            and not already_held
            and count_open_positions(portfolio, settings, symbols) >= settings.max_concurrent_positions
        ):
            decision.rejection_reason = (
                f"Limit równoczesnych pozycji osiągnięty ({settings.max_concurrent_positions}) — "
                "ograniczenie skorelowanej ekspozycji"
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision

        # Auto-demotion: a ticker with a proven negative track record on this
        # venue is quarantined from NEW entries -- stop repeating what loses.
        if settings.auto_demote_enabled:
            st = (performance_context.get("per_symbol_stats") or {}).get(decision_data.symbol)
            if (
                st
                and st["closed"] >= settings.auto_demote_min_trades
                and st["realized_pnl"] < 0
                and (st["win_rate"] or 0) < settings.auto_demote_win_rate_floor
            ):
                decision.rejection_reason = (
                    f"Auto-degradacja {decision_data.symbol}: ujemna historia "
                    f"({st['wins']}W/{st['losses']}L, P&L {st['realized_pnl']:.2f}) — nowe wejście zablokowane"
                )
                db.add(decision)
                db.commit()
                db.refresh(decision)
                return decision

        in_cooldown, cooldown_reason = stop_loss_cooldown_active(db, decision_data.symbol, venue=venue)
        if in_cooldown:
            decision.rejection_reason = cooldown_reason
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision

        # Earnings-gap backstop: never OPEN a fresh position into a report the
        # mechanical stop-loss can't protect against. Only acts on a KNOWN
        # upcoming date, so a calendar-lookup failure never blocks trading.
        days_to_earnings = earnings_days.get(decision_data.symbol)
        if (
            settings.earnings_blackout_days > 0
            and days_to_earnings is not None
            and 0 <= days_to_earnings <= settings.earnings_blackout_days
        ):
            decision.rejection_reason = (
                f"Blackout przed earnings: {decision_data.symbol} raportuje za "
                f"{days_to_earnings} dni — ryzyko luki, nowe wejście pominięte"
            )
            db.add(decision)
            db.commit()
            db.refresh(decision)
            return decision

    db.add(decision)
    db.commit()
    db.refresh(decision)

    # Re-check right before placing the order: the Claude call above can take
    # several seconds, and a "Zatrzymaj automat" click during that window
    # should still stop the trade rather than only affecting the *next* cycle.
    final_check = risk_manager.can_trade_automated(db, venue)
    if not final_check.approved:
        decision.rejection_reason = f"Zatrzymano tuż przed wykonaniem: {final_check.reason}"
        db.commit()
        db.refresh(decision)
        return decision

    try:
        _execute_trade(
            db=db,
            broker=broker,
            settings=settings,
            symbol=decision_data.symbol,
            action=decision_data.action,
            size_pct=effective_size_pct,
            portfolio=portfolio,
            decision=decision,
            is_manual=False,
            session=session_info.session if session_info is not None else market_hours.REGULAR,
            venue=venue,
        )
    except (ValueError, AlpacaAPIError, EToroAPIError) as exc:
        # e.g. a computed order size that rounds to zero, or a broker
        # rejection. Record why instead of crashing the whole scheduled cycle.
        logger.warning("Wykonanie zlecenia %s nieudane, pomijam", decision_data.symbol, exc_info=True)
        decision.rejection_reason = f"Zlecenie niewykonane: {exc}"
        db.commit()
        db.refresh(decision)
    return decision


def _execute_trade(
    *,
    db: Session,
    broker,
    settings: Settings,
    symbol: str,
    action: str,
    size_pct: float,
    portfolio: dict,
    decision: Decision | None,
    is_manual: bool,
    session: str = market_hours.REGULAR,
    venue: str = "alpaca",
) -> Trade:
    if action == "BUY":
        usdt_amount = portfolio["usdt_balance"] * (size_pct / 100)
        result = broker.place_order_for_session(symbol, "BUY", usdt_amount=usdt_amount, session=session)
    elif action == "SELL":
        base_balance = portfolio["balances"].get(_base_asset(symbol, settings.quote_currency), 0.0)
        quantity = base_balance * (size_pct / 100)
        result = broker.place_order_for_session(symbol, "SELL", quantity=quantity, session=session)
    else:
        raise ValueError(f"Cannot execute action {action}")

    trade = Trade(
        symbol=result.symbol,
        side=result.side,
        quantity=result.quantity,
        price=result.price,
        usdt_value=result.usdt_value,
        order_id=result.order_id,
        mode=TradeMode.LIVE,
        is_manual=is_manual,
        venue=venue,
        decision_id=decision.id if decision else None,
    )
    db.add(trade)

    if decision is not None:
        decision.executed = True

    db.commit()
    db.refresh(trade)
    logger.info("Executed %s %s qty=%s price=%s", result.side, result.symbol, result.quantity, result.price)
    email_reporter.send_trade_alert(settings, trade, reason=decision.reasoning if decision else "")
    return trade


def execute_manual_trade(
    db: Session,
    settings: Settings,
    broker,
    symbol: str,
    side: str,
    usdt_amount: float | None = None,
    quantity: float | None = None,
    *,
    venue: str = "alpaca",
    whitelist: list[str] | None = None,
) -> Trade:
    """Human-initiated trade from the dashboard, bypassing Claude entirely.
    Intentionally NOT gated by the pause/halt state or the automated
    max_position_pct cap -- that's the whole point of a manual override. Still
    enforced: the trading whitelist, as a safety net against a typo'd or
    otherwise unintended symbol reaching a real order. `venue` selects which
    portfolio it belongs to (records are stamped accordingly)."""
    whitelist_check = risk_manager.validate_symbol_whitelist(settings, symbol, whitelist)
    if not whitelist_check.approved:
        raise ValueError(whitelist_check.reason)

    # Deliberately not blocked when the market is closed -- same as the
    # existing pause/halt bypass, a manual click is the override; the broker
    # itself is the final backstop if the session genuinely can't trade.
    if usdt_amount is not None:
        result = broker.place_order_for_session(symbol, side, usdt_amount=usdt_amount)
    elif quantity is not None:
        result = broker.place_order_for_session(symbol, side, quantity=quantity)
    else:
        raise ValueError("Must provide either usdt_amount or quantity")

    decision = Decision(
        symbol=symbol,
        action=TradeAction(side.upper()),
        size_pct=0.0,
        confidence=1.0,
        reasoning="Ręczna transakcja zainicjowana z dashboardu (z pominięciem Claude).",
        triggered_by=TriggerType.MANUAL,
        executed=True,
        venue=venue,
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)

    trade = Trade(
        symbol=result.symbol,
        side=result.side,
        quantity=result.quantity,
        price=result.price,
        usdt_value=result.usdt_value,
        order_id=result.order_id,
        mode=TradeMode.LIVE,
        is_manual=True,
        venue=venue,
        decision_id=decision.id,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    email_reporter.send_trade_alert(settings, trade, reason=decision.reasoning)
    return trade
