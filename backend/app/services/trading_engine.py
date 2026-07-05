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
from app.services import budget_tracker, risk_manager
from app.services.claude_advisor import ClaudeAdvisor
from app.services.kraken_client import KrakenClient
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.technical_indicators import compute_technical_indicators

logger = logging.getLogger(__name__)


def _base_asset(symbol: str, quote_currency: str) -> str:
    return symbol.replace(quote_currency, "")


def compute_portfolio(db: Session, settings: Settings, kraken: KrakenClient) -> dict:
    """Generic across the whole whitelist -- works for 2 coins or 10 without
    any schema or code change per coin. A single symbol failing on Kraken
    (network hiccup, delisted pair, etc.) is skipped rather than aborting the
    whole cycle -- otherwise one bad symbol silently kills every scheduled
    cycle and manual "run now" indefinitely."""
    balances = kraken.get_account_balances()
    usdt_balance = balances.get(settings.quote_currency, 0.0)

    prices: dict[str, float] = {}
    coin_balances: dict[str, float] = {}
    failed_symbols: list[str] = []
    total_value = usdt_balance

    for symbol in settings.whitelist_symbols:
        try:
            price = kraken.get_price(symbol)
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
    )
    db.add(snapshot)
    db.commit()

    return {
        "total_value_usdt": total_value,
        "usdt_balance": usdt_balance,
        "balances": coin_balances,
        "prices": prices,
        "failed_symbols": failed_symbols,
    }


def check_trigger(db: Session, settings: Settings, prices: dict[str, float]) -> tuple[bool, TriggerType]:
    state = risk_manager.get_state(db)
    today_str = date.today().isoformat()

    last_prices: dict[str, float] = json.loads(state.last_check_prices_json or "{}")

    triggered = False
    reason = TriggerType.SCHEDULED_DAILY

    for symbol, current_price in prices.items():
        last_price = last_prices.get(symbol, 0.0)
        if last_price > 0:
            move_pct = abs(current_price - last_price) / last_price * 100
            if move_pct >= settings.price_move_trigger_pct:
                triggered = True
                reason = TriggerType.PRICE_MOVE
        last_prices[symbol] = current_price

    state.last_check_prices_json = json.dumps(last_prices)

    if state.last_full_analysis_date != today_str:
        triggered = True
        if reason != TriggerType.PRICE_MOVE:
            reason = TriggerType.SCHEDULED_DAILY

    db.commit()
    return triggered, reason


def average_cost_basis(db: Session, symbol: str) -> float | None:
    """Weighted-average entry price of the CURRENTLY held quantity of `symbol`,
    walked from the full trade history (buys add, sells remove proportionally).
    Returns None if nothing is currently held. Used by the take-profit/stop-loss
    engine to know each position's entry price without storing extra state."""
    trades = db.execute(
        select(Trade).where(Trade.symbol == symbol).order_by(Trade.timestamp.asc())
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


def _set_stop_loss_cooldown(db: Session, symbol: str, minutes: int) -> None:
    if minutes <= 0:
        return
    state = risk_manager.get_state(db)
    cooldowns = json.loads(state.stop_loss_cooldowns_json or "{}")
    cooldowns[symbol] = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
    state.stop_loss_cooldowns_json = json.dumps(cooldowns)
    db.commit()


def stop_loss_cooldown_active(db: Session, symbol: str) -> tuple[bool, str | None]:
    """True (with a human reason) if `symbol` is still inside its post-stop-loss
    cooldown window and must not be re-bought yet."""
    state = risk_manager.get_state(db)
    cooldowns = json.loads(state.stop_loss_cooldowns_json or "{}")
    until = cooldowns.get(symbol)
    if not until:
        return False, None
    until_dt = datetime.fromisoformat(until)
    now = datetime.now(timezone.utc)
    if now >= until_dt:
        return False, None
    mins_left = int((until_dt - now).total_seconds() // 60) + 1
    return True, f"Cooldown po stop-lossie: {symbol} zablokowany do odkupu jeszcze ~{mins_left} min"


def check_take_profit_stop_loss(
    db: Session, settings: Settings, kraken: KrakenClient, portfolio: dict
) -> list[Trade]:
    """Mechanical exits run on every poll, WITHOUT asking Claude: auto-SELL a
    whole position the moment it reaches +take_profit_pct or -stop_loss_pct
    versus its average entry price. Respects the same stop/halt gate as any
    automated trade -- if the user pressed STOP, these don't fire either."""
    if not risk_manager.can_trade_automated(db).approved:
        return []

    executed: list[Trade] = []
    for symbol in settings.whitelist_symbols:
        if symbol not in portfolio["prices"]:
            continue
        base = _base_asset(symbol, settings.quote_currency)
        qty = portfolio["balances"].get(base, 0.0)
        if qty <= 0:
            continue
        basis = average_cost_basis(db, symbol)
        if basis is None or basis <= 0:
            continue

        price = portfolio["prices"][symbol]
        change_pct = (price - basis) / basis * 100

        reason = None
        is_stop_loss = False
        if settings.take_profit_pct > 0 and change_pct >= settings.take_profit_pct:
            reason = f"Take-profit: {base} +{change_pct:.1f}% od wejścia (średnia {basis:.2f} → {price:.2f})"
        elif settings.stop_loss_pct > 0 and change_pct <= -settings.stop_loss_pct:
            reason = f"Stop-loss: {base} {change_pct:.1f}% od wejścia (średnia {basis:.2f} → {price:.2f})"
            is_stop_loss = True
        if reason is None:
            continue

        decision = Decision(
            symbol=symbol,
            action=TradeAction.SELL,
            size_pct=100.0,
            confidence=1.0,
            reasoning=reason,
            triggered_by=TriggerType.PRICE_MOVE,
            executed=False,
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)

        trade = _execute_trade(
            db=db,
            kraken=kraken,
            settings=settings,
            symbol=symbol,
            action="SELL",
            size_pct=100.0,
            portfolio=portfolio,
            decision=decision,
            is_manual=False,
        )
        executed.append(trade)
        logger.info("TP/SL exit: %s", reason)
        if is_stop_loss:
            _set_stop_loss_cooldown(db, symbol, settings.stop_loss_cooldown_minutes)

    return executed


def _mark_analysis_done_today(db: Session) -> None:
    """Called only after advisor.decide() actually succeeds, so a transient
    Claude/network failure doesn't burn today's scheduled-fallback trigger."""
    state = risk_manager.get_state(db)
    state.last_full_analysis_date = date.today().isoformat()
    db.commit()


def run_cycle(
    db: Session,
    settings: Settings,
    kraken: KrakenClient,
    news: NewsClient,
    advisor: ClaudeAdvisor,
    market_ctx: MarketContextClient | None = None,
    force: bool = False,
) -> Decision | None:
    """force=True bypasses the trigger gate and always asks Claude -- this is
    what the dashboard's "Wymuś analizę" button needs. Without it the manual
    button just ran a normal cycle, which returns None (does nothing) whenever
    the daily analysis already ran and no price moved past the threshold --
    exactly the "clicked it, nothing happened" behaviour reported from the
    dashboard."""
    portfolio = compute_portfolio(db, settings, kraken)
    state = risk_manager.update_portfolio_value(db, settings, portfolio["total_value_usdt"])

    # Mechanical take-profit / stop-loss runs every scheduled poll, before we
    # even decide whether to ask Claude -- this is what makes the bot actively
    # rotate capital (realize gains, cut losses) instead of buying and holding.
    # A manual "Wymuś analizę" (force) stays a pure Claude read and skips this.
    if not force:
        exits = check_take_profit_stop_loss(db, settings, kraken, portfolio)
        if exits:
            # Positions changed -- refresh the snapshot so the Claude leg below
            # sees post-exit balances/cash.
            portfolio = compute_portfolio(db, settings, kraken)

    triggered, trigger_reason = check_trigger(db, settings, portfolio["prices"])
    if force:
        trigger_reason = TriggerType.MANUAL
    elif not triggered:
        return None

    trade_check = risk_manager.can_trade_automated(db)

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
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        return decision

    market_data = {}
    for symbol in settings.whitelist_symbols:
        if symbol not in portfolio["prices"]:
            continue  # Kraken couldn't price this symbol this cycle -- see compute_portfolio
        try:
            klines_24 = kraken.get_klines(symbol, "1h", 24)
            indicator_closes = [float(row[4]) for row in kraken.get_klines(symbol, "1h", 200)]
        except Exception:
            logger.warning("Failed to fetch klines for %s, excluding it from this cycle", symbol, exc_info=True)
            continue
        market_data[symbol] = {
            "price": portfolio["prices"][symbol],
            "klines_1h_24": klines_24,
            "technical": compute_technical_indicators(indicator_closes),
        }
    # Only offer Claude symbols it actually has data for this cycle -- a symbol
    # missing from market_data (Kraken failure above) must not be a choosable
    # BUY/SELL target.
    tradable_symbols = list(market_data.keys())
    headlines = news.get_headlines([_base_asset(s, settings.quote_currency) for s in settings.whitelist_symbols])
    global_context = market_ctx.get_market_context() if market_ctx is not None else {}

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
        "auto_take_profit_pct": settings.take_profit_pct,
        "auto_stop_loss_pct": settings.stop_loss_pct,
        "exit_note": (
            "Pozycje są automatycznie zamykane przy +auto_take_profit_pct (zysk) lub "
            "-auto_stop_loss_pct (strata) względem średniej ceny wejścia. Skup się na trafnym "
            "WEJŚCIU; nie musisz planować wyjścia."
        ),
    }

    decision_data = advisor.decide(
        whitelist=tradable_symbols,
        market_data=market_data,
        news=headlines,
        portfolio=portfolio,
        risk_context=risk_context,
        market_context=global_context,
        trigger_reason=trigger_reason.value,
    )
    _mark_analysis_done_today(db)
    budget_tracker.record_usage_cost(db, decision_data.cost_usd)

    decision = Decision(
        symbol=decision_data.symbol,
        action=TradeAction(decision_data.action),
        size_pct=decision_data.size_pct,
        confidence=decision_data.confidence,
        reasoning=decision_data.reasoning,
        market_data_snapshot=json.dumps(market_data, default=str),
        news_snapshot=json.dumps(headlines),
        market_context_snapshot=json.dumps(global_context),
        triggered_by=trigger_reason,
        executed=False,
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

    validation = risk_manager.validate_trade(
        settings=settings,
        symbol=decision_data.symbol,
        action=decision_data.action,
        size_pct=decision_data.size_pct,
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
        in_cooldown, cooldown_reason = stop_loss_cooldown_active(db, decision_data.symbol)
        if in_cooldown:
            decision.rejection_reason = cooldown_reason
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
    final_check = risk_manager.can_trade_automated(db)
    if not final_check.approved:
        decision.rejection_reason = f"Zatrzymano tuż przed wykonaniem: {final_check.reason}"
        db.commit()
        db.refresh(decision)
        return decision

    _execute_trade(
        db=db,
        kraken=kraken,
        settings=settings,
        symbol=decision_data.symbol,
        action=decision_data.action,
        size_pct=decision_data.size_pct,
        portfolio=portfolio,
        decision=decision,
        is_manual=False,
    )
    return decision


def _execute_trade(
    *,
    db: Session,
    kraken: KrakenClient,
    settings: Settings,
    symbol: str,
    action: str,
    size_pct: float,
    portfolio: dict,
    decision: Decision | None,
    is_manual: bool,
) -> Trade:
    if action == "BUY":
        usdt_amount = portfolio["usdt_balance"] * (size_pct / 100)
        result = kraken.place_market_order_usdt_amount(symbol, "BUY", usdt_amount)
    elif action == "SELL":
        base_balance = portfolio["balances"].get(_base_asset(symbol, settings.quote_currency), 0.0)
        quantity = base_balance * (size_pct / 100)
        result = kraken.place_market_order_quantity(symbol, "SELL", quantity)
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
        decision_id=decision.id if decision else None,
    )
    db.add(trade)

    if decision is not None:
        decision.executed = True

    db.commit()
    db.refresh(trade)
    logger.info("Executed %s %s qty=%s price=%s", result.side, result.symbol, result.quantity, result.price)
    return trade


def execute_manual_trade(
    db: Session,
    settings: Settings,
    kraken: KrakenClient,
    symbol: str,
    side: str,
    usdt_amount: float | None = None,
    quantity: float | None = None,
) -> Trade:
    """Human-initiated trade from the dashboard, bypassing Claude entirely.
    Intentionally NOT gated by the pause/halt state or the automated
    max_position_pct cap -- that's the whole point of a manual override. Still
    enforced: the trading whitelist, as a safety net against a typo'd or
    otherwise unintended symbol reaching a real order."""
    whitelist_check = risk_manager.validate_symbol_whitelist(settings, symbol)
    if not whitelist_check.approved:
        raise ValueError(whitelist_check.reason)

    if usdt_amount is not None:
        result = kraken.place_market_order_usdt_amount(symbol, side, usdt_amount)
    elif quantity is not None:
        result = kraken.place_market_order_quantity(symbol, side, quantity)
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
        decision_id=decision.id,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade
