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
from app.services import budget_tracker, market_hours, risk_manager, scorecard, shadow_analysis
from app.services.alpaca_client import AlpacaClient
from app.services.strategy_profiles import effective_settings
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
    # Day/week P&L must compare against the TRUE combined account (cash once +
    # both engines' positions) -- NOT the single most-recently-written snapshot
    # across either venue. Extended polls far more often than equities, so that
    # naive "latest snapshot" was almost always the extended-only total, compared
    # against a day_start_value baselined on the (much larger) equities total:
    # a purely cosmetic scope mismatch that showed a large, entirely fake loss.
    account = _account_view(db)

    day_pnl_pct = None
    week_pnl_pct = None
    if account is not None:
        current_total = account["total_value"]
        if state.day_start_value > 0:
            day_pnl_pct = (current_total - state.day_start_value) / state.day_start_value * 100
        if state.week_start_value > 0:
            week_pnl_pct = (current_total - state.week_start_value) / state.week_start_value * 100

    return {
        "mode": "testnet" if settings.alpaca_paper else "live",
        "quote_currency": settings.quote_currency,
        "is_paused": state.is_paused,
        "extended_paused": state.extended_paused,
        "is_halted": state.is_halted,
        "halted_reason": state.halted_reason,
        "day_pnl_pct": day_pnl_pct,
        "week_pnl_pct": week_pnl_pct,
        "daily_loss_limit_pct": settings.daily_loss_limit_pct,
        "weekly_loss_limit_pct": settings.weekly_loss_limit_pct,
        "max_drawdown_halt_pct": settings.max_drawdown_halt_pct,
        "peak_account_value": state.peak_account_value,
        "max_position_pct": settings.max_position_pct,
        "whitelist": settings.whitelist_symbols,
        "poll_interval_minutes": settings.poll_interval_minutes,
        # Extended (24-7, same Alpaca account) venue -- lets the dashboard
        # show/hide the second portfolio panel and its whitelist.
        "extended_enabled": settings.extended_enabled,
        "extended_whitelist": settings.extended_whitelist_symbols,
        "market_regime": _load_regime(state.market_regime_json),
        "extended_market_regime": _load_regime(state.extended_market_regime_json) if settings.extended_enabled else None,
        # ONE Alpaca account shared by both engines (cash counted once). Lets the
        # dashboard show a single account total instead of two double-counted
        # per-engine "portfolio" values.
        "account": account,
        # Read-only share link enabled? (token itself never leaves the server.)
        "share_enabled": bool(settings.share_token),
        # Exact per-engine tuning (Centrum Sterowania): every live knob, not
        # just the headline daily/weekly limits above.
        "profiles": {
            "alpaca": _engine_profile_view(settings, "alpaca"),
            "extended": _engine_profile_view(settings, "extended"),
        },
        **_serialize_session_info(settings),
        **_net_result_view(db, settings),
    }


def _engine_profile_view(settings: Settings, venue: str) -> dict:
    """Every live tuning knob for one venue, resolved through the SAME
    effective_settings() the trading engine itself uses -- this is exactly
    what the engine is running with right now, not a guess."""
    s = effective_settings(settings, venue)
    return {
        "signal_timeframe": s.signal_timeframe,
        "poll_interval_minutes": s.poll_interval_minutes,
        "risk_per_trade_pct": s.risk_per_trade_pct,
        "min_buy_confidence": s.min_buy_confidence,
        "max_new_positions_per_day": s.max_new_positions_per_day,
        "max_concurrent_positions": s.max_concurrent_positions,
        "min_hold_minutes": s.min_hold_minutes,
        "max_position_pct": s.max_position_pct,
        "stop_loss_min_pct": s.stop_loss_min_pct,
        "stop_loss_max_pct": s.stop_loss_max_pct,
        "reward_risk_ratio": s.reward_risk_ratio,
        "trailing_stop_frac": s.trailing_stop_frac,
        "partial_take_profit_frac": s.partial_take_profit_frac,
        "partial_take_profit_r": s.partial_take_profit_r,
        "price_move_trigger_pct": s.price_move_trigger_pct,
        "full_analysis_every_minutes": s.full_analysis_every_minutes,
        "volatility_reference_pct": s.volatility_reference_pct,
        "allocation_pct": s.extended_allocation_pct if venue == "extended" else s.alpaca_allocation_pct,
    }


def _net_result_view(db: Session, settings: Settings) -> dict:
    """The honest bottom line: realized P&L across BOTH engines (one shared
    account, since inception) minus what Claude has actually cost OVER THE SAME
    LIFETIME -- not just this month's spend, which would understate the true
    cost more and more as months pass (P&L is cumulative, so the cost side must
    be too) -- so "are we ahead" answers with real money, not brutto P&L that
    ignores the AI bill."""
    budget = budget_tracker.get_budget_status(db, settings)
    realized = scorecard.total_realized_pnl(db)
    lifetime_spend = risk_manager.get_state(db).claude_spend_usd_lifetime
    return {
        "realized_pnl_usd": realized,
        "net_result_usd": round(realized - lifetime_spend, 2),
        **budget,
    }


def _load_regime(regime_json: str | None) -> dict | None:
    try:
        data = json.loads(regime_json or "{}")
        return data or None
    except json.JSONDecodeError:
        return None


def _latest_snapshot(db: Session, venue: str) -> PortfolioSnapshot | None:
    return db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.venue == venue)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()


def _account_view(db: Session) -> dict | None:
    """The ONE Alpaca account, not two portfolios: both engines share a single
    cash balance and hold positions in the same account. Each per-venue snapshot
    records the SAME account cash plus only that engine's positions, so naively
    summing the two snapshots' totals double-counts the cash. Reconstruct the
    true account here: cash counted ONCE + each engine's position value
    (snapshot total minus that shared cash)."""
    a = _latest_snapshot(db, "alpaca")
    c = _latest_snapshot(db, "extended")
    if a is None and c is None:
        return None
    # Cash is identical in both snapshots; take it from the freshest one.
    freshest = max((s for s in (a, c) if s is not None), key=lambda s: s.timestamp)
    cash = freshest.usdt_balance
    equity_positions_value = (a.total_value_usdt - a.usdt_balance) if a else 0.0
    extended_positions_value = (c.total_value_usdt - c.usdt_balance) if c else 0.0
    return {
        "cash": round(cash, 2),
        "equity_positions_value": round(equity_positions_value, 2),
        "extended_positions_value": round(extended_positions_value, 2),
        "total_value": round(cash + equity_positions_value + extended_positions_value, 2),
    }


@router.get("/portfolio")
def get_portfolio(
    limit: int = Query(200, le=2000),
    venue: str = "alpaca",
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    rows = db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.venue == venue)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .limit(limit)
    ).scalars().all()
    history = [serialize(r) for r in reversed(rows)]
    current = history[-1] if history else None

    # Queried separately (not just history[0]) so "since the very beginning"
    # P&L stays correct even once more than `limit` snapshots have accumulated.
    # Anchor on the first snapshot with a REAL value (> 0): a leading $0
    # snapshot (recorded right after a history reset, before the account was
    # first priced) would otherwise become the baseline and make "Od początku"
    # show "—" forever (division by a zero baseline).
    inception_row = db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.venue == venue, PortfolioSnapshot.total_value_usdt > 0)
        .order_by(PortfolioSnapshot.timestamp.asc())
        .limit(1)
    ).scalar_one_or_none()
    inception = serialize(inception_row) if inception_row else None

    whitelist = settings.extended_whitelist_symbols if venue == "extended" else settings.whitelist_symbols

    # Average entry price per currently-held base asset ("BTC" -> 61234.5), so
    # the dashboard can show per-position unrealized P&L. Keyed by base asset to
    # match balances_json.
    cost_basis: dict[str, float] = {}
    for symbol in whitelist:
        basis = average_cost_basis(db, symbol, venue=venue)
        if basis is not None:
            base = symbol[: -len(settings.quote_currency)] if symbol.endswith(settings.quote_currency) else symbol
            cost_basis[base] = round(basis, 6)

    # Scorecard vs buy-and-hold benchmark, computed from the latest snapshot's
    # prices (no live broker call needed on this hot, auth-gated endpoint).
    # Account-wide benchmark is Alpaca-driven; the extended venue has no scorecard.
    latest = rows[0] if rows else None
    card = None
    if latest is not None and venue == "alpaca":
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
        "venue": venue,
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


def _widget_positions(db: Session, settings: Settings, venue: str) -> list[dict]:
    """Held positions for one venue, from its latest snapshot -- what's held,
    its value and unrealized P&L. Same reconstruction the dashboard's
    PositionsBoard does, but server-side and compact (for the iPhone widget)."""
    snap = _latest_snapshot(db, venue)
    if snap is None:
        return []
    try:
        balances = json.loads(snap.balances_json or "{}")
        prices = json.loads(snap.prices_json or "{}")
    except (TypeError, ValueError):
        return []
    leg = "extended" if venue == "extended" else "us"
    out: list[dict] = []
    for asset, qty_raw in balances.items():
        qty = float(qty_raw)
        if qty <= 0:
            continue
        # equities: prices keyed by ticker (== base); extended: by full "BTCUSD".
        full = asset if asset in prices else asset + settings.quote_currency
        price = prices.get(asset)
        if price is None:
            price = prices.get(asset + settings.quote_currency)
        if price is None:
            continue
        value = qty * price
        if value < 1:
            continue
        basis = average_cost_basis(db, full, venue=venue)
        pnl_pct = round((price - basis) / basis * 100, 2) if basis and basis > 0 else None
        out.append({"asset": asset, "leg": leg, "value": round(value, 2), "pnl_pct": pnl_pct})
    return out


@router.get("/widget")
def get_widget(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """ONE compact, fast payload for the iPhone (Scriptable) widget: account
    total + cash, day %, net result, held positions across both engines, and a
    downsampled equity curve. Purpose-built so the widget makes a single small
    request (the full /api/portfolio series was too heavy to load reliably in
    the widget sandbox)."""
    state = risk_manager.get_state(db)
    account = _account_view(db)
    net = _net_result_view(db, settings)

    # Day P&L vs the TRUE combined account total (cash once + both engines'
    # positions), NOT the latest single-venue snapshot -- extended polls far more
    # often, so "latest snapshot" is usually the extended-only slice, which
    # against a combined day_start_value shows a large fake loss. Same fix as
    # get_status.
    day_pnl_pct = None
    if account is not None and state.day_start_value > 0:
        day_pnl_pct = round((account["total_value"] - state.day_start_value) / state.day_start_value * 100, 2)

    positions = _widget_positions(db, settings, "alpaca")
    if settings.extended_enabled:
        positions += _widget_positions(db, settings, "extended")
    positions.sort(key=lambda p: p["value"], reverse=True)

    # Downsampled account-value curve (equities-venue history == the account
    # when extended is off; a fair trend proxy otherwise). ~30 points, oldest→newest.
    rows = db.execute(
        select(PortfolioSnapshot.total_value_usdt)
        .where(PortfolioSnapshot.venue == "alpaca", PortfolioSnapshot.total_value_usdt > 0)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .limit(400)
    ).scalars().all()
    series = list(reversed(rows))
    if len(series) > 30:
        step = len(series) / 30.0
        series = [series[min(len(series) - 1, int(i * step))] for i in range(30)]
    spark = [round(v, 2) for v in series]

    return {
        "mode": "testnet" if settings.alpaca_paper else "live",
        "total": account["total_value"] if account else None,
        "cash": account["cash"] if account else None,
        "day_pnl_pct": day_pnl_pct,
        "net_result_usd": net["net_result_usd"],
        # Live estimated Claude budget remaining ($) -- if the budget is set to
        # what was loaded on the console, this tracks the real balance directionally.
        "claude_budget_remaining_usd": net["claude_budget_remaining_usd"],
        "positions": positions,
        "spark": spark,
    }


@router.get("/claude-edge")
def get_claude_edge(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """On-demand, read-only: would the mechanical filter alone have done as
    well as Claude-directed trading? Recomputed from stored decision history,
    never touches the live trading path. Cheap enough to run per request at
    this account's current history size; not polled automatically."""
    return shadow_analysis.compute_claude_edge(db, settings, venue=venue)


@router.get("/trades")
def get_trades(limit: int = Query(100, le=1000), venue: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Trade).order_by(Trade.timestamp.desc()).limit(limit)
    if venue is not None:
        stmt = select(Trade).where(Trade.venue == venue).order_by(Trade.timestamp.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [serialize(r) for r in rows]


@router.get("/decisions")
def get_decisions(limit: int = Query(100, le=1000), venue: str | None = None, db: Session = Depends(get_db)):
    stmt = select(Decision).order_by(Decision.timestamp.desc()).limit(limit)
    if venue is not None:
        stmt = select(Decision).where(Decision.venue == venue).order_by(Decision.timestamp.desc()).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [serialize(r) for r in rows]
