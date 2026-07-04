from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import Decision, PortfolioSnapshot, Trade
from app.serialization import serialize
from app.services import budget_tracker, risk_manager

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/status")
def get_status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    state = risk_manager.get_state(db)
    latest_snapshot = db.execute(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.desc()).limit(1)
    ).scalar_one_or_none()

    day_pnl_pct = None
    week_pnl_pct = None
    if latest_snapshot:
        if state.day_start_value > 0:
            day_pnl_pct = (latest_snapshot.total_value_usdt - state.day_start_value) / state.day_start_value * 100
        if state.week_start_value > 0:
            week_pnl_pct = (
                (latest_snapshot.total_value_usdt - state.week_start_value) / state.week_start_value * 100
            )

    return {
        "mode": "testnet" if settings.binance_testnet else "live",
        "is_paused": state.is_paused,
        "is_halted": state.is_halted,
        "halted_reason": state.halted_reason,
        "day_pnl_pct": day_pnl_pct,
        "week_pnl_pct": week_pnl_pct,
        "daily_loss_limit_pct": settings.daily_loss_limit_pct,
        "weekly_loss_limit_pct": settings.weekly_loss_limit_pct,
        "max_position_pct": settings.max_position_pct,
        "whitelist": settings.whitelist_symbols,
        "poll_interval_minutes": settings.poll_interval_minutes,
        **budget_tracker.get_budget_status(db, settings),
    }


@router.get("/portfolio")
def get_portfolio(limit: int = Query(200, le=2000), db: Session = Depends(get_db)):
    rows = db.execute(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.desc()).limit(limit)
    ).scalars().all()
    history = [serialize(r) for r in reversed(rows)]
    current = history[-1] if history else None

    # Queried separately (not just history[0]) so "since the very beginning"
    # P&L stays correct even once more than `limit` snapshots have accumulated.
    inception_row = db.execute(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.asc()).limit(1)
    ).scalar_one_or_none()
    inception = serialize(inception_row) if inception_row else None

    return {"current": current, "history": history, "inception": inception}


@router.get("/trades")
def get_trades(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.execute(select(Trade).order_by(Trade.timestamp.desc()).limit(limit)).scalars().all()
    return [serialize(r) for r in rows]


@router.get("/decisions")
def get_decisions(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.execute(select(Decision).order_by(Decision.timestamp.desc()).limit(limit)).scalars().all()
    return [serialize(r) for r in rows]
