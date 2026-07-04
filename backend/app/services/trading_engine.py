"""Orchestrates one full decision cycle: gather data -> ask Opus (if
triggered) -> risk checks -> execute -> log everything."""

import json
import logging
from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Decision, PortfolioSnapshot, Trade, TradeAction, TradeMode, TriggerType
from app.services import budget_tracker, risk_manager
from app.services.binance_client import BinanceClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.news_client import NewsClient

logger = logging.getLogger(__name__)


def _base_asset(symbol: str) -> str:
    return symbol.replace("USDT", "")


def compute_portfolio(db: Session, settings: Settings, binance: BinanceClient) -> dict:
    """Generic across the whole whitelist -- works for 2 coins or 10 without
    any schema or code change per coin."""
    balances = binance.get_account_balances()
    usdt_balance = balances.get("USDT", 0.0)

    prices: dict[str, float] = {}
    coin_balances: dict[str, float] = {}
    total_value = usdt_balance

    for symbol in settings.whitelist_symbols:
        price = binance.get_price(symbol)
        base = _base_asset(symbol)
        qty = balances.get(base, 0.0)
        prices[symbol] = price
        coin_balances[base] = qty
        total_value += qty * price

    snapshot = PortfolioSnapshot(
        total_value_usdt=total_value,
        usdt_balance=usdt_balance,
        balances_json=json.dumps(coin_balances),
        prices_json=json.dumps(prices),
    )
    db.add(snapshot)
    db.commit()

    return {
        "total_value_usdt": total_value,
        "usdt_balance": usdt_balance,
        "balances": coin_balances,
        "prices": prices,
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


def _mark_analysis_done_today(db: Session) -> None:
    """Called only after advisor.decide() actually succeeds, so a transient
    Claude/network failure doesn't burn today's scheduled-fallback trigger."""
    state = risk_manager.get_state(db)
    state.last_full_analysis_date = date.today().isoformat()
    db.commit()


def run_cycle(
    db: Session,
    settings: Settings,
    binance: BinanceClient,
    news: NewsClient,
    advisor: ClaudeAdvisor,
) -> Decision | None:
    portfolio = compute_portfolio(db, settings, binance)
    state = risk_manager.update_portfolio_value(db, settings, portfolio["total_value_usdt"])

    triggered, trigger_reason = check_trigger(db, settings, portfolio["prices"])
    if not triggered:
        return None

    trade_check = risk_manager.can_trade_automated(db)

    market_data = {
        symbol: {
            "price": portfolio["prices"][symbol],
            "klines_1h_24": binance.get_klines(symbol, "1h", 24),
        }
        for symbol in settings.whitelist_symbols
    }
    headlines = news.get_headlines([_base_asset(s) for s in settings.whitelist_symbols])

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
    }

    decision_data = advisor.decide(
        whitelist=settings.whitelist_symbols,
        market_data=market_data,
        news=headlines,
        portfolio=portfolio,
        risk_context=risk_context,
        trigger_reason=trigger_reason.value,
    )
    _mark_analysis_done_today(db)
    budget_tracker.record_usage(db, decision_data.input_tokens, decision_data.output_tokens)

    decision = Decision(
        symbol=decision_data.symbol,
        action=TradeAction(decision_data.action),
        size_pct=decision_data.size_pct,
        confidence=decision_data.confidence,
        reasoning=decision_data.reasoning,
        market_data_snapshot=json.dumps(market_data, default=str),
        news_snapshot=json.dumps(headlines),
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

    db.add(decision)
    db.commit()
    db.refresh(decision)

    # Re-check right before placing the order: the Opus call above can take
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
        binance=binance,
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
    binance: BinanceClient,
    settings: Settings,
    symbol: str,
    action: str,
    size_pct: float,
    portfolio: dict,
    decision: Decision | None,
    is_manual: bool,
) -> Trade:
    mode = TradeMode.TESTNET if settings.binance_testnet else TradeMode.LIVE

    if action == "BUY":
        usdt_amount = portfolio["usdt_balance"] * (size_pct / 100)
        result = binance.place_market_order_usdt_amount(symbol, "BUY", usdt_amount)
    elif action == "SELL":
        base_balance = portfolio["balances"].get(_base_asset(symbol), 0.0)
        quantity = base_balance * (size_pct / 100)
        result = binance.place_market_order_quantity(symbol, "SELL", quantity)
    else:
        raise ValueError(f"Cannot execute action {action}")

    trade = Trade(
        symbol=result.symbol,
        side=result.side,
        quantity=result.quantity,
        price=result.price,
        usdt_value=result.usdt_value,
        order_id=result.order_id,
        mode=mode,
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
    binance: BinanceClient,
    symbol: str,
    side: str,
    usdt_amount: float | None = None,
    quantity: float | None = None,
) -> Trade:
    """Human-initiated trade from the dashboard, bypassing Opus entirely.
    Intentionally NOT gated by the pause/halt state or the automated
    max_position_pct cap -- that's the whole point of a manual override. Still
    enforced: the trading whitelist, as a safety net against a typo'd or
    otherwise unintended symbol reaching a real order."""
    whitelist_check = risk_manager.validate_symbol_whitelist(settings, symbol)
    if not whitelist_check.approved:
        raise ValueError(whitelist_check.reason)

    mode = TradeMode.TESTNET if settings.binance_testnet else TradeMode.LIVE

    if usdt_amount is not None:
        result = binance.place_market_order_usdt_amount(symbol, side, usdt_amount)
    elif quantity is not None:
        result = binance.place_market_order_quantity(symbol, side, quantity)
    else:
        raise ValueError("Must provide either usdt_amount or quantity")

    decision = Decision(
        symbol=symbol,
        action=TradeAction(side.upper()),
        size_pct=0.0,
        confidence=1.0,
        reasoning="Ręczna transakcja zainicjowana z dashboardu (z pominięciem Opus).",
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
        mode=mode,
        is_manual=True,
        decision_id=decision.id,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade
