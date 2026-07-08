import asyncio
import json
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.db import SessionLocal, get_db
from app.models import Decision, PortfolioSnapshot, SystemState, Trade
from app.serialization import serialize
from app.services import budget_tracker, market_hours, risk_manager, scorecard
from app.services.alpaca_client import AlpacaClient
from app.services.trading_engine import average_cost_basis

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])


def _serialize_session_info(settings: Settings) -> dict:
    """Best-effort -- /api/status is polled every ~15s by every open dashboard
    tab and must keep working even if Alpaca's calendar endpoint is briefly
    unavailable, so a failure here degrades to omitting the session fields
    rather than 500ing the whole endpoint."""
    try:
        info = market_hours.get_session_info(AlpacaClient(settings))
    except Exception:
        logger.warning("Failed to compute market session info for /api/status", exc_info=True)
        return {"market_session": None, "session_bounds": None}

    return {
        "market_session": info.session,
        "session_bounds": {
            "regular_open": info.regular_open.isoformat() if info.regular_open else None,
            "regular_close": info.regular_close.isoformat() if info.regular_close else None,
        },
    }


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
        "mode": "testnet" if settings.alpaca_paper else "live",
        "quote_currency": settings.quote_currency,
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
        **_serialize_session_info(settings),
        **budget_tracker.get_budget_status(db, settings),
    }


@router.get("/portfolio")
def get_portfolio(
    limit: int = Query(200, le=2000),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
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

    # Average entry price per currently-held base asset ("XBT" -> 61234.5), so
    # the dashboard can show per-position unrealized P&L. Keyed by base asset to
    # match balances_json.
    cost_basis: dict[str, float] = {}
    for symbol in settings.whitelist_symbols:
        basis = average_cost_basis(db, symbol)
        if basis is not None:
            base = symbol[: -len(settings.quote_currency)] if symbol.endswith(settings.quote_currency) else symbol
            cost_basis[base] = round(basis, 6)

    # Scorecard vs buy-and-hold benchmark, computed from the latest snapshot's
    # prices (no live broker call needed on this hot, auth-gated endpoint).
    latest = rows[0] if rows else None
    card = None
    if latest is not None:
        snapshot_portfolio = {
            "total_value_usdt": latest.total_value_usdt,
            "prices": json.loads(latest.prices_json or "{}"),
        }
        card = scorecard.compute_scorecard(db, settings, snapshot_portfolio)

    return {
        "current": current,
        "history": history,
        "inception": inception,
        "cost_basis": cost_basis,
        "scorecard": card,
    }


EVENTS_POLL_SECONDS = 2.0
EVENTS_KEEPALIVE_EVERY = 12  # polls between keepalive comments (~24s)


def _data_fingerprint() -> tuple:
    """Cheap local-sqlite read summarizing 'did anything the dashboard shows
    change?' -- new decision/trade/snapshot or a pause/halt flip."""
    db = SessionLocal()
    try:
        d = db.execute(select(func.max(Decision.id))).scalar() or 0
        t = db.execute(select(func.max(Trade.id))).scalar() or 0
        s = db.execute(select(func.max(PortfolioSnapshot.id))).scalar() or 0
        state = db.get(SystemState, 1)
        return (d, t, s, bool(state.is_paused) if state else True, bool(state.is_halted) if state else False)
    finally:
        db.close()


@router.get("/events")
async def events():
    """Server-Sent Events: pushes a tick the moment a new decision, trade,
    snapshot, or pause/halt change lands, so the dashboard refreshes instantly
    instead of waiting out its 15s polling interval (which stays as a
    fallback for clients where SSE doesn't connect)."""

    async def stream():
        last = await run_in_threadpool(_data_fingerprint)
        polls = 0
        while True:
            await asyncio.sleep(EVENTS_POLL_SECONDS)
            polls += 1
            current = await run_in_threadpool(_data_fingerprint)
            if current != last:
                last = current
                yield "data: changed\n\n"
            elif polls % EVENTS_KEEPALIVE_EVERY == 0:
                yield ": keepalive\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/trades")
def get_trades(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.execute(select(Trade).order_by(Trade.timestamp.desc()).limit(limit)).scalars().all()
    return [serialize(r) for r in rows]


@router.get("/decisions")
def get_decisions(limit: int = Query(100, le=1000), db: Session = Depends(get_db)):
    rows = db.execute(select(Decision).order_by(Decision.timestamp.desc()).limit(limit)).scalars().all()
    return [serialize(r) for r in rows]
