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


def compute_portfolio(db: Session, binance: BinanceClient) -> dict:
    balances = binance.get_account_balances()
    btc_price = binance.get_price("BTCUSDT")
    eth_price = binance.get_price("ETHUSDT")
    usdt_balance = balances.get("USDT", 0.0)
    btc_balance = balances.get("BTC", 0.0)
    eth_balance = balances.get("ETH", 0.0)
    total_value = usdt_balance + btc_balance * btc_price + eth_balance * eth_price

    snapshot = PortfolioSnapshot(
        total_value_usdt=total_value,
        usdt_balance=usdt_balance,
        btc_balance=btc_balance,
        eth_balance=eth_balance,
        btc_price=btc_price,
        eth_price=eth_price,
    )
    db.add(snapshot)
    db.commit()

    return {
        "total_value_usdt": total_value,
        "usdt_balance": usdt_balance,
        "btc_balance": btc_balance,
        "eth_balance": eth_balance,
        "btc_price": btc_price,
        "eth_price": eth_price,
    }


def check_trigger(db: Session, settings: Settings, prices: dict) -> tuple[bool, TriggerType]:
    state = risk_manager.get_state(db)
    today_str = date.today().isoformat()

    triggered = False
    reason = TriggerType.SCHEDULED_DAILY

    for price_field, current_price in (
        ("last_btc_check_price", prices["btc_price"]),
        ("last_eth_check_price", prices["eth_price"]),
    ):
        last_price = getattr(state, price_field)
        if last_price > 0:
            move_pct = abs(current_price - last_price) / last_price * 100
            if move_pct >= settings.price_move_trigger_pct:
                triggered = True
                reason = TriggerType.PRICE_MOVE
        setattr(state, price_field, current_price)

    if state.last_full_analysis_date != today_str:
        triggered = True
        if reason != TriggerType.PRICE_MOVE:
            reason = TriggerType.SCHEDULED_DAILY

    if triggered:
        state.last_full_analysis_date = today_str

    db.commit()
    return triggered, reason


def run_cycle(
    db: Session,
    settings: Settings,
    binance: BinanceClient,
    news: NewsClient,
    advisor: ClaudeAdvisor,
) -> Decision | None:
    portfolio = compute_portfolio(db, binance)
    state = risk_manager.update_portfolio_value(db, settings, portfolio["total_value_usdt"])

    triggered, trigger_reason = check_trigger(db, settings, portfolio)
    if not triggered:
        return None

    trade_check = risk_manager.can_trade_automated(db)

    market_data = {
        "BTCUSDT": {
            "price": portfolio["btc_price"],
            "klines_1h_24": binance.get_klines("BTCUSDT", "1h", 24),
        },
        "ETHUSDT": {
            "price": portfolio["eth_price"],
            "klines_1h_24": binance.get_klines("ETHUSDT", "1h", 24),
        },
    }
    headlines = news.get_headlines(["BTC", "ETH"])

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
        base_balance = portfolio.get(f"{_base_asset(symbol).lower()}_balance", 0.0)
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
    Intentionally NOT gated by the pause/halt state -- that state only
    governs the automated decision loop, per the product's manual-override
    requirement."""
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
