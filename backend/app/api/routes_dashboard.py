import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone

# Stempel wersji wstrzyknięty przy buildzie (Dockerfile ARG -> ENV). Pozwala
# apce pokazać, JAKI kod realnie działa, żeby nie zgadywać "czy się wdrożyło".
BUILD_SHA = os.getenv("GIT_SHA", "dev")
BUILD_TIME = os.getenv("BUILD_TIME", "")

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
from app.services.trading_engine import _state_col, average_cost_basis, describe_position_plan, position_opened_at
from app.services.whitelist_review import get_extended_whitelist

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dashboard"])


def _serialize_session_info(settings: Settings) -> dict:
    """/api/status jest odpytywane co ~15s przez KAŻDĄ otwartą zakładkę, więc NIE
    MOŻE robić synchronicznego wywołania Alpaca -- to potrafiło trwać do 15s
    (timeout klienta) przy zimnym cache/wolnym brokerze i przekraczało 12s timeout
    apki ("auto sprawdzenie nie działa"). Czytamy WYŁĄCZNIE z cache (bez brokera);
    cache grzeje w tle scheduler/prime. Zimny cache -> pola null (UI pokaże '—')."""
    info = market_hours.cached_session_info()
    if info is None:
        return {"market_session": None, "session_bounds": None}

    return {
        "market_session": info.session,
        "session_bounds": {
            "regular_open": info.regular_open.isoformat() if info.regular_open else None,
            "regular_close": info.regular_close.isoformat() if info.regular_close else None,
        },
    }


def _claude_budget_view(db: Session, settings: Settings) -> dict:
    """Licznik tokenów AI dla dashboardu: budżet, wydane, ZOSTAŁO ($) i czy
    automat jest wstrzymany przez wyczerpanie budżetu."""
    bs = budget_tracker.get_budget_status(db, settings)
    budget = float(bs["claude_monthly_budget_usd"])
    spent = float(bs["claude_spend_usd_this_month"])
    remaining = max(0.0, budget - spent)
    exhausted = settings.claude_pause_trading_at_budget and budget > 0 and spent >= budget
    return {
        "budget_usd": round(budget, 2),
        "spent_usd": round(spent, 2),
        "remaining_usd": round(remaining, 2),
        "pct_used": round(bs["claude_budget_pct_used"], 1),
        "halt_at_zero": settings.claude_pause_trading_at_budget,
        "exhausted": exhausted,
        # ODCZYTANE (nie szacowane) liczby tokenów -- Anthropic zwraca dokładny
        # `usage` przy każdej odpowiedzi; to jest suma za bieżący miesiąc.
        "input_tokens": bs["claude_input_tokens_this_month"],
        "output_tokens": bs["claude_output_tokens_this_month"],
        "total_tokens": bs["claude_total_tokens_this_month"],
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
    account = _account_view(db, settings)

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
        "extended_whitelist": get_extended_whitelist(db, settings),
        # Licznik tokenów AI: ile ZOSTAŁO z budżetu (na żywo). Gdy halt_at_zero i
        # remaining=0 -> automat wstrzymuje pytania do Claude i nowe wejścia
        # (mechaniczne wyjścia i tak chronią pozycje). budget_status liczy spend z
        # realnego usage per-call.
        "claude_budget": _claude_budget_view(db, settings),
        "market_regime": _load_regime(state.market_regime_json),
        "extended_market_regime": _load_regime(state.extended_market_regime_json) if settings.extended_enabled else None,
        # ONE Alpaca account shared by both engines (cash counted once). Lets the
        # dashboard show a single account total instead of two double-counted
        # per-engine "portfolio" values.
        "account": account,
        # Ile ZAROBIŁ/STRACIŁ sam automat (odporne na wpłaty): zrealizowany +
        # niezrealizowany P&L z transakcji.
        "trading_pnl": _trading_pnl_view(db, settings),
        # Alfa vs trzymanie SPY -- czy bot bije zwykłe DCA w indeks.
        "alpha_vs_spy": _alpha_view(db, settings, account),
        # Read-only share link enabled? (token itself never leaves the server.)
        "share_enabled": bool(settings.share_token),
        # Exact per-engine tuning (Centrum Sterowania): every live knob, not
        # just the headline daily/weekly limits above.
        "profiles": {
            "alpaca": _engine_profile_view(settings, "alpaca"),
            "extended": _engine_profile_view(settings, "extended"),
        },
        # Stempel wersji: jaki kod realnie działa (SHA + czas buildu).
        "build_sha": BUILD_SHA,
        "build_time": BUILD_TIME,
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
        "progressive_confidence_step": s.progressive_confidence_step,
        "progressive_confidence_cap": s.progressive_confidence_cap,
        "max_new_positions_per_day": s.max_new_positions_per_day,
        "max_concurrent_positions": s.max_concurrent_positions,
        "min_hold_minutes": s.min_hold_minutes,
        "min_hold_profit_bypass_pct": s.min_hold_profit_bypass_pct,
        "hard_take_profit_pct": s.hard_take_profit_pct,
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


def _account_view(db: Session, settings: Settings | None = None) -> dict | None:
    """The ONE Alpaca account, not two portfolios: both engines share a single
    cash balance and hold positions in the same account. Each per-venue snapshot
    records the SAME account cash plus only that engine's positions, so naively
    summing the two snapshots' totals double-counts the cash. Reconstruct the
    true account here: cash counted ONCE + each engine's position value
    (snapshot total minus that shared cash)."""
    a = _latest_snapshot(db, "alpaca")
    # Jeden silnik: gdy POZA SESJĄ wyłączona, WSZYSTKIE pozycje należą do portfela
    # sesji (po migracji przy starcie). Nie czytamy zamrożonego snapshotu extended
    # -- inaczej ta sama pozycja policzyłaby się podwójnie (raz w alpaca, raz w
    # nieodświeżanym extended).
    c = _latest_snapshot(db, "extended") if (settings or get_settings()).extended_enabled else None
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


def _trading_pnl_view(db: Session, settings: Settings | None = None) -> dict:
    """Ile ZAROBIŁ/STRACIŁ sam automat -- ODPORNE na wpłaty. Wpłata dodaje
    gotówkę, nie tworzy transakcji, więc nie rusza tej liczby. To jest czysty
    wynik handlu = zrealizowany (z zamkniętych) + niezrealizowany (papierowy na
    otwartych pozycjach)."""
    realized = scorecard.total_realized_pnl(db)
    unrealized = 0.0
    # Gdy POZA SESJĄ wyłączona, cały kapitał jest w portfelu sesji -- pomijamy
    # zamrożony snapshot extended, żeby nie liczyć pozycji podwójnie.
    venues = ("alpaca", "extended") if (settings or get_settings()).extended_enabled else ("alpaca",)
    for venue in venues:
        snap = _latest_snapshot(db, venue)
        if snap is None:
            continue
        try:
            balances = json.loads(snap.balances_json or "{}")
            prices = json.loads(snap.prices_json or "{}")
        except (TypeError, ValueError):
            continue
        for base, qty in balances.items():
            if not qty or qty <= 0:
                continue
            price = prices.get(base)
            if price is None:
                continue
            basis = average_cost_basis(db, base, venue=venue)
            if basis:
                unrealized += (price - basis) * qty
    return {
        "realized_usd": round(realized, 2),
        "unrealized_usd": round(unrealized, 2),
        "total_usd": round(realized + unrealized, 2),
    }


def _alpha_view(db: Session, settings: Settings, account: dict | None) -> dict | None:
    """Alfa vs zwykłe trzymanie benchmarku (SPY): czy bot bije DCA w indeks.
    benchmark_value = ile byłbyś wart, gdybyś tę samą bazę trzymał w SPY od
    baseline'u; alpha = konto − to. None dopóki nie ma baseline'u/ceny SPY."""
    if account is None:
        return None
    state = risk_manager.get_state(db)
    if getattr(state, "benchmark_start_price", 0) <= 0 or getattr(state, "benchmark_start_value", 0) <= 0:
        return None
    snap = _latest_snapshot(db, "alpaca")
    spy_now = None
    if snap:
        try:
            spy_now = json.loads(snap.prices_json or "{}").get(settings.benchmark_symbol)
        except (TypeError, ValueError):
            spy_now = None
    if not spy_now:
        return None
    bench_value = state.benchmark_start_value * (spy_now / state.benchmark_start_price)
    alpha_usd = account["total_value"] - bench_value
    return {
        "benchmark": settings.benchmark_symbol,
        "benchmark_value": round(bench_value, 2),
        "alpha_usd": round(alpha_usd, 2),
        "alpha_pct": round(alpha_usd / bench_value * 100, 2) if bench_value > 0 else None,
    }


def _trading_pnl_series(db: Session, venue: str, rows_asc: list) -> list[float]:
    """Deposit-proof P&L curve: for each snapshot, realized(up to that moment) +
    unrealized(at that moment) -- the pure trading result over time, WITHOUT the
    jumps a deposit puts into the account-value curve. Walked incrementally over
    the venue's trade ledger (O(snapshots + trades)), so it stays cheap."""
    trades = db.execute(
        select(Trade).where(Trade.venue == venue).order_by(Trade.timestamp.asc())
    ).scalars().all()
    q = get_settings().quote_currency
    qty_by: dict[str, float] = {}
    cost_by: dict[str, float] = {}
    realized = 0.0
    i = 0
    series: list[float] = []
    for snap in rows_asc:
        ts = snap.timestamp
        while i < len(trades) and trades[i].timestamp <= ts:
            t = trades[i]
            sym = t.symbol
            if t.side.upper() == "BUY":
                qty_by[sym] = qty_by.get(sym, 0.0) + t.quantity
                cost_by[sym] = cost_by.get(sym, 0.0) + t.usdt_value
            else:
                held = qty_by.get(sym, 0.0)
                if held > 1e-12:
                    avg = cost_by[sym] / held
                    sell_qty = min(t.quantity, held)
                    realized += (t.price - avg) * sell_qty
                    cost_by[sym] -= avg * sell_qty
                    qty_by[sym] = held - sell_qty
                    if qty_by[sym] <= 1e-12:
                        qty_by[sym] = 0.0
                        cost_by[sym] = 0.0
            i += 1
        unreal = 0.0
        try:
            balances = json.loads(snap.balances_json or "{}")
            prices = json.loads(snap.prices_json or "{}")
        except (TypeError, ValueError):
            balances, prices = {}, {}
        for base, qraw in balances.items():
            held = float(qraw or 0.0)
            if held <= 0:
                continue
            sym = base if base in qty_by else (base + q if (base + q) in qty_by else base)
            held_ledger = qty_by.get(sym, 0.0)
            if held_ledger <= 1e-12:
                continue
            avg = cost_by[sym] / held_ledger
            price = prices.get(base) if prices.get(base) is not None else prices.get(base + q)
            if price is None:
                continue
            unreal += (price - avg) * held
        series.append(round(realized + unreal, 2))
    return series


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

    whitelist = get_extended_whitelist(db, settings) if venue == "extended" else settings.whitelist_symbols

    # Average entry price per currently-held base asset ("BTC" -> 61234.5), so
    # the dashboard can show per-position unrealized P&L. Keyed by base asset to
    # match balances_json. IMPORTANT: cover every ACTUALLY-HELD symbol, not just
    # the static whitelist -- a position bought from the dynamic universe (or an
    # ETF adopted from the extended leg) sits OUTSIDE trading_whitelist, so a
    # whitelist-only loop left it without an entry price and the dashboard showed
    # no +/- on it. Union: held bases (from the latest snapshot) ∪ whitelist.
    held_bases: set[str] = set()
    if current is not None:
        try:
            held_bases = {b for b, q in json.loads(current.get("balances_json") or "{}").items() if q and q > 0}
        except (TypeError, ValueError):
            held_bases = set()
    q = settings.quote_currency
    lookup = set(whitelist) | {b + q for b in held_bases} | held_bases
    cost_basis: dict[str, float] = {}
    for symbol in lookup:
        basis = average_cost_basis(db, symbol, venue=venue)
        if basis is not None:
            base = symbol[: -len(q)] if symbol.endswith(q) else symbol
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
        "pnl_history": _trading_pnl_series(db, venue, list(reversed(rows))),
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


@router.get("/position-plans")
def get_position_plans(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Per-position 'co robię przy tym indeksie': for every held position, the
    mechanical exit plan in plain language (take-profit / partial / trailing /
    stop levels + a note), computed from the SAME math the exits run. Read-only,
    no broker call -- derived from the latest snapshot + stored trailing peaks."""
    snap = _latest_snapshot(db, venue)
    if snap is None:
        return {"venue": venue, "positions": []}
    try:
        balances = json.loads(snap.balances_json or "{}")
        prices = json.loads(snap.prices_json or "{}")
    except (TypeError, ValueError):
        return {"venue": venue, "positions": []}
    state = risk_manager.get_state(db)
    # Use the venue's EFFECTIVE settings so the extended leg's plan reflects its
    # own stop/reward knobs, not the regular-session base.
    eff = effective_settings(settings, venue)
    try:
        peaks = json.loads(getattr(state, _state_col("peaks", venue)) or "{}")
    except (TypeError, ValueError):
        peaks = {}

    out: list[dict] = []
    for asset, qty_raw in balances.items():
        qty = float(qty_raw)
        if qty <= 0:
            continue
        full = asset if asset in prices else asset + settings.quote_currency
        price = prices.get(asset) or prices.get(asset + settings.quote_currency)
        if price is None:
            continue
        value = qty * price
        if value < 1:
            continue
        basis = average_cost_basis(db, full, venue=venue)
        peak = float(peaks.get(asset) or peaks.get(full) or price)
        plan = describe_position_plan(eff, basis=basis, price=price, peak=peak)
        # Strategia pozycyjna: pokaż "po co trzymamy" -- ile dni w pozycji,
        # poziomy wejścia/stop/cel i tezę Claude'a z ostatniego kupna.
        opened = position_opened_at(db, full, venue=venue)
        days_held = None
        if opened is not None:
            delta = datetime.now(timezone.utc) - (opened if opened.tzinfo else opened.replace(tzinfo=timezone.utc))
            days_held = max(0, delta.days)
        stop_price = None
        target_price = None
        if basis and basis > 0:
            stop_price = round(basis * (1 - plan["stop_pct"] / 100), 4)
            arm = plan.get("take_profit_arm_pct") or 0
            if arm > 0:
                target_price = round(basis * (1 + arm / 100), 4)
        out.append({
            "asset": asset,
            "qty": qty,
            "basis": round(basis, 4) if basis else None,
            "price": round(price, 4),
            "value": round(value, 2),
            "days_held": days_held,
            "stop_price": stop_price,
            "target_price": target_price,
            "thesis": _latest_thesis(db, full, venue),
            "sell_plan": _sell_timing(eff, plan, basis=basis, price=price,
                                      stop_price=stop_price, target_price=target_price, opened=opened),
            **plan,
        })
    out.sort(key=lambda p: p["value"], reverse=True)
    return {"venue": venue, "positions": out}


def _sell_timing(
    settings: Settings,
    plan: dict,
    *,
    basis: float | None,
    price: float,
    stop_price: float | None,
    target_price: float | None,
    opened: datetime | None,
) -> dict:
    """"KIEDY SPRZEDAM" -- the single clearest thing the owner asked for: for one
    held position, WHEN and WHY it will be sold, mirroring exactly the conditions
    the mechanical exit + min-hold gate use. Returns a compact structure the UI
    renders as a gauge + one-liner, so there's no guessing 'why is it still held'.

    state:
      sell_now     -- a trigger is live right now (hard take-profit / at stop)
      profit_ready -- gain >= profit-bypass: min-hold WON'T block a profit exit,
                      sells at the first cool-down from the peak ("bierzemy zysk")
      climbing     -- on the plus side, waiting to reach the take-profit target
      locked       -- anti-churn min-hold still holds it (and not yet in profit)
      waiting      -- flat/small loss, holding toward target or stop
      near_stop    -- close to the protective stop
    progress_pct -- 0..100 fill for the gauge: how far from entry toward the
                    up-side take-profit target (winners) or toward the stop (losers).
    """
    change = plan.get("change_pct")
    adopted = plan.get("adopted")
    bypass = settings.min_hold_profit_bypass_pct
    hard_tp = settings.hard_take_profit_pct
    arm = plan.get("take_profit_arm_pct") or 0.0

    # Min-hold release moment (anti-churn). None if no min-hold or unknown entry.
    release: datetime | None = None
    within_hold = False
    if opened is not None and settings.min_hold_minutes > 0:
        o = opened if opened.tzinfo else opened.replace(tzinfo=timezone.utc)
        release = o + timedelta(minutes=settings.min_hold_minutes)
        within_hold = datetime.now(timezone.utc) < release

    gain = change if change is not None else 0.0

    def money(v: float) -> str:
        return f"${v:,.2f}"

    # Progress gauge: winners fill toward the take-profit arm; losers toward stop.
    progress = 0.0
    if arm > 0 and gain >= 0:
        progress = max(0.0, min(100.0, gain / arm * 100))
    elif gain < 0 and settings.stop_loss_min_pct:
        stop_ref = plan.get("stop_pct") or settings.stop_loss_min_pct
        if stop_ref:
            progress = max(0.0, min(100.0, abs(gain) / stop_ref * 100))

    # ---- Decide the state + copy, in the SAME priority the engine exits use. ----
    if adopted:
        return {
            "state": "waiting", "headline": "Chronię trailingiem",
            "when": "gdy spadnie od szczytu", "progress_pct": round(progress),
            "release": None, "locked": False,
            "detail": "Pozycja adoptowana (bez ceny wejścia) — sprzedam przy schłodzeniu od szczytu.",
        }

    if plan.get("action") == "near_stop" or gain <= -(plan.get("stop_pct") or 0):
        return {
            "state": "near_stop", "headline": "Blisko stopu — bronię kapitału",
            "when": f"stop {money(stop_price)}" if stop_price else "przy stopie",
            "progress_pct": round(progress), "release": None, "locked": False,
            "detail": f"Strata {gain:+.1f}% — zamykam przy −{plan.get('stop_pct'):.1f}% od wejścia.",
        }

    if hard_tp > 0 and gain >= hard_tp:
        return {
            "state": "sell_now", "headline": f"Sprzedaję teraz (+{gain:.1f}%)",
            "when": "teraz", "progress_pct": 100, "release": None, "locked": False,
            "detail": f"Zysk sięgnął sufitu +{hard_tp:.1f}% — biorę cały zysk.",
        }

    # Profit big enough to bypass anti-churn: we will take it at the first dip.
    if bypass > 0 and gain >= bypass:
        return {
            "state": "profit_ready", "headline": f"Zysk do wzięcia (+{gain:.1f}%)",
            "when": f"cel {money(target_price)}" if target_price else "przy schłodzeniu",
            "progress_pct": round(progress), "release": None, "locked": False,
            "detail": (
                f"Jest zysk (+{gain:.1f}% ≥ +{bypass:.1f}%) — furtka zysku otwarta: "
                f"anty-churn NIE blokuje. Realizuję przy pierwszym cofnięciu lub na celu."
            ),
        }

    # Still inside anti-churn min-hold and not yet in bankable profit.
    if within_hold and release is not None:
        return {
            "state": "locked", "headline": "Anty-churn trzyma pozycję",
            "when": f"do {release.strftime('%d.%m %H:%M')}",
            "progress_pct": round(progress), "release": release.isoformat(), "locked": True,
            "detail": (
                f"Świeże wejście — nie odwracam się na spreadzie. Sprzedam po "
                f"{release.strftime('%d.%m %H:%M')} albo wcześniej, gdy zysk sięgnie +{bypass:.1f}%."
            ),
        }

    if gain > 0:
        return {
            "state": "climbing", "headline": f"Na plusie (+{gain:.1f}%) — rośnie",
            "when": f"cel {money(target_price)}" if target_price else f"przy +{arm:.1f}%",
            "progress_pct": round(progress), "release": None, "locked": False,
            "detail": (
                f"Zysk {gain:+.1f}%. Realizuję przy +{bypass:.1f}% (furtka) lub na celu "
                f"{money(target_price) if target_price else ''} — do tego czasu pozwalam rosnąć."
            ),
        }

    return {
        "state": "waiting", "headline": "Trzymam — czekam na ruch",
        "when": f"cel {money(target_price)}" if target_price else "na sygnał",
        "progress_pct": round(progress), "release": None, "locked": False,
        "detail": (
            f"Blisko zera ({gain:+.1f}%). Sprzedam na celu {money(target_price) if target_price else ''} "
            f"albo bronię przy stopie {money(stop_price) if stop_price else ''}."
        ),
    }


def _latest_thesis(db: Session, symbol: str, venue: str) -> str | None:
    """Teza Claude'a z ostatniego KUPNA tej nazwy -- 'po co ją mamy'. Skrócona."""
    row = db.execute(
        select(Trade)
        .where(Trade.symbol == symbol, Trade.venue == venue, Trade.side.ilike("BUY"))
        .order_by(Trade.timestamp.desc())
        .limit(1)
    ).scalars().first()
    if row is not None and row.decision is not None and row.decision.reasoning:
        return row.decision.reasoning[:220]
    return None


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
    account = _account_view(db, settings)
    net = _net_result_view(db, settings)
    trading_pnl = _trading_pnl_view(db, settings)

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
        # "Zysk automatu" -- TEN SAM deposit-proof wskaźnik co na Konsoli
        # (zrealizowany + papierowy, bez wpłat), żeby widżet i apka pokazywały
        # to samo. net_result_usd zostaje dla zgodności wstecznej, ale widżet go
        # już nie wyświetla (mylił: realized - koszt AI).
        "trading_pnl_usd": trading_pnl["total_usd"],
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


# --- News relevant to our operation -----------------------------------------
# Cached in-process: get_headlines() fans out to ~40 feeds + per-ticker sources,
# far too heavy to run on every poll. One shared fetch, reused for a few minutes.
_news_cache: dict = {"ts": 0.0, "items": []}
_NEWS_TTL_SECONDS = 300


def _mentions(title: str, ticker: str) -> bool:
    import re

    return re.search(rf"\b{re.escape(ticker)}\b", title, re.IGNORECASE) is not None


@router.get("/news")
async def get_news(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Headlines relevant to what we actually trade: our two legs' whitelists
    (ticker-specific feeds) plus broad US-market news. Tagged with any of our
    tickers named in the headline so the UI can flag what touches our book."""
    import time

    from app.services.news_client import NewsClient
    from app.services.trading_engine import _base_asset

    now = time.time()
    if now - _news_cache["ts"] < _NEWS_TTL_SECONDS and _news_cache["items"]:
        return {"items": _news_cache["items"], "cached": True}

    syms = list(dict.fromkeys(settings.whitelist_symbols + get_extended_whitelist(db, settings)))
    bases = [_base_asset(s, settings.quote_currency) for s in syms]
    try:
        news = NewsClient(settings)
        # Polish-language band for display (the model still reads original feeds).
        headlines = await run_in_threadpool(news.get_pl_headlines, 18)
    except Exception:
        logger.warning("news fetch failed", exc_info=True)
        return {"items": _news_cache["items"], "cached": True}

    items = []
    for h in headlines:
        title = (h.get("title") or "").strip()
        if not title:
            continue
        tickers = [t for t in bases if _mentions(title, t)][:2]
        items.append({"title": title, "source": h.get("source", ""), "published_at": h.get("published_at"), "tickers": tickers})
    _news_cache.update(ts=now, items=items)
    return {"items": items, "cached": False}


_sources_cache: dict = {"ts": 0.0, "data": None}
_SOURCES_TTL_SECONDS = 120


@router.get("/news/sources")
async def get_news_sources(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Zakładka NEWSY: do czego mamy połączenie i CO WIDZIMY na żywo. Odpala
    każde źródło osobno i raportuje ok/down + liczbę nagłówków ZWRÓCONYCH TERAZ,
    plus złączoną próbkę realnego feedu (z sentymentem). Cache 120 s, bo to
    ~40 zapytań na fan-out."""
    import time
    from datetime import datetime, timezone

    from app.services.news_client import NewsClient
    from app.services.trading_engine import _base_asset

    now = time.time()
    if _sources_cache["data"] and now - _sources_cache["ts"] < _SOURCES_TTL_SECONDS:
        return {**_sources_cache["data"], "cached": True}

    syms = list(dict.fromkeys(settings.whitelist_symbols))[:6]
    bases = [_base_asset(s, settings.quote_currency) for s in syms]
    try:
        rep = await run_in_threadpool(NewsClient(settings).source_report, bases)
    except Exception:
        logger.warning("news source report failed", exc_info=True)
        return _sources_cache["data"] or {"sources": [], "headlines": [], "summary": {"ok": 0, "down": 0, "headlines": 0}}

    ok = sum(1 for s in rep["sources"] if s["status"] == "ok")
    data = {
        "sources": rep["sources"],
        "headlines": rep["headlines"],
        "summary": {"ok": ok, "down": len(rep["sources"]) - ok, "headlines": len(rep["headlines"])},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _sources_cache.update(ts=now, data=data)
    return {**data, "cached": False}
