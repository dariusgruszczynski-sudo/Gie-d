"""Measures whether the bot is actually earning its complexity: portfolio
value vs simply buying and holding the benchmark (SPY), realized P&L, and a
win/loss tally on closed trades. Without this the whole strategy is unmeasured
-- and you can't improve what you don't measure. Feeds both the dashboard and
Claude's own decision context ("you're underperforming buy-and-hold, rethink")."""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import SystemState, Trade
from app.services import risk_manager


def _walk_realized(db: Session) -> tuple[float, int, int]:
    """Walks the full trade history per ticker, tracking a running average
    cost, and books realized P&L on each SELL. Returns
    (total_realized_usd, winning_sells, losing_sells)."""
    trades = db.execute(select(Trade).order_by(Trade.timestamp.asc())).scalars().all()
    qty_by: dict[str, float] = defaultdict(float)
    cost_by: dict[str, float] = defaultdict(float)  # total cost of held qty
    realized = 0.0
    wins = 0
    losses = 0
    for t in trades:
        sym = t.symbol
        if t.side.upper() == "BUY":
            qty_by[sym] += t.quantity
            cost_by[sym] += t.usdt_value
        else:  # SELL
            held = qty_by[sym]
            if held <= 1e-12:
                continue
            avg_cost = cost_by[sym] / held
            sell_qty = min(t.quantity, held)
            pnl = (t.price - avg_cost) * sell_qty
            realized += pnl
            if pnl >= 0:
                wins += 1
            else:
                losses += 1
            cost_by[sym] -= avg_cost * sell_qty
            qty_by[sym] -= sell_qty
            if qty_by[sym] <= 1e-12:
                qty_by[sym] = 0.0
                cost_by[sym] = 0.0
    return realized, wins, losses


def realized_history(db: Session, *, venue: str | None = None, limit: int = 300) -> list[dict]:
    """Zakładka HISTORIA: dla KAŻDEJ sprzedaży (zamknięcia) zwraca jedną pozycję
    'kupiłem X — sprzedałem Y — zarobiłem Z', licząc zysk tą samą metodą średniego
    kosztu co reszta appki (_walk_realized). Zwraca najnowsze pierwsze.

    Każdy wpis: symbol, ilość, średnia cena kupna (koszt w chwili sprzedaży),
    cena sprzedaży, wartość kupna/sprzedaży, zysk USD + %, kiedy pozycja się
    zaczęła (opened_at) i kiedy ją sprzedano (sold_at), ile dni trzymana."""
    q = select(Trade).order_by(Trade.timestamp.asc())
    if venue is not None:
        q = q.where(Trade.venue == venue)
    trades = db.execute(q).scalars().all()

    qty_by: dict[str, float] = defaultdict(float)
    cost_by: dict[str, float] = defaultdict(float)      # łączny koszt trzymanej ilości
    opened_by: dict[str, object] = {}                   # kiedy zaczęła się bieżąca partia
    out: list[dict] = []
    for t in trades:
        sym = t.symbol
        if t.side.upper() == "BUY":
            if qty_by[sym] <= 1e-12:
                opened_by[sym] = t.timestamp            # partia rusza od zera
            qty_by[sym] += t.quantity
            cost_by[sym] += t.usdt_value
        else:  # SELL
            held = qty_by[sym]
            if held <= 1e-12:
                continue
            avg_cost = cost_by[sym] / held
            sell_qty = min(t.quantity, held)
            cost_usd = avg_cost * sell_qty
            proceeds = t.price * sell_qty
            pnl = proceeds - cost_usd
            opened = opened_by.get(sym)
            days = None
            if opened is not None and t.timestamp is not None:
                try:
                    days = max(0, (t.timestamp - opened).days)
                except Exception:
                    days = None
            out.append({
                "symbol": sym,
                "venue": getattr(t, "venue", "alpaca"),
                "qty": round(sell_qty, 6),
                "avg_buy_price": round(avg_cost, 4),
                "sell_price": round(t.price, 4),
                "cost_usd": round(cost_usd, 2),
                "proceeds_usd": round(proceeds, 2),
                "pnl_usd": round(pnl, 2),
                "pnl_pct": round((pnl / cost_usd * 100), 2) if cost_usd > 0 else None,
                "opened_at": opened.isoformat() if opened is not None else None,
                "sold_at": t.timestamp.isoformat() if t.timestamp is not None else None,
                "days_held": days,
            })
            cost_by[sym] -= cost_usd
            qty_by[sym] -= sell_qty
            if qty_by[sym] <= 1e-12:
                qty_by[sym] = 0.0
                cost_by[sym] = 0.0
                opened_by.pop(sym, None)
    out.reverse()  # najnowsze pierwsze
    return out[:limit]


def update_benchmark_baseline(db: Session, settings: Settings, portfolio: dict) -> SystemState:
    """Sets the buy-and-hold baseline once, on the first cycle that can price
    the benchmark ticker. Left untouched afterwards so the comparison stays
    anchored to inception (a portfolio reset clears it via reset_scorecard)."""
    state = risk_manager.get_state(db)
    if state.benchmark_start_price > 0:
        return state
    price = portfolio["prices"].get(settings.benchmark_symbol)
    total = portfolio.get("total_value_usdt", 0.0)
    if price and price > 0 and total > 0:
        from datetime import date

        state.benchmark_start_price = price
        state.benchmark_start_value = total
        state.benchmark_start_date = date.today().isoformat()
        db.commit()
        db.refresh(state)
    return state


def total_realized_pnl(db: Session) -> float:
    """Realized P&L across BOTH engines (one shared account, one bottom line)
    -- used for the account-wide "net result after Claude cost" figure."""
    realized, _wins, _losses = _walk_realized(db)
    return round(realized, 2)


def compute_scorecard(db: Session, settings: Settings, portfolio: dict) -> dict:
    """Portfolio vs benchmark buy-and-hold, plus realized P&L and win rate.
    All fields degrade to None when there isn't a baseline / price yet, so the
    dashboard and Claude context never break on a fresh account."""
    state = risk_manager.get_state(db)
    portfolio_value = portfolio.get("total_value_usdt", 0.0)
    benchmark_price_now = portfolio["prices"].get(settings.benchmark_symbol)

    benchmark_value = None
    alpha_usd = None
    alpha_pct = None
    if state.benchmark_start_price > 0 and benchmark_price_now:
        benchmark_value = state.benchmark_start_value * (benchmark_price_now / state.benchmark_start_price)
        alpha_usd = portfolio_value - benchmark_value
        if benchmark_value > 0:
            alpha_pct = alpha_usd / benchmark_value * 100

    realized, wins, losses = _walk_realized(db)
    closed = wins + losses

    return {
        "portfolio_value": round(portfolio_value, 2),
        "benchmark_symbol": settings.benchmark_symbol,
        # Baseline exposed so the frontend can draw a full buy-and-hold series
        # over the portfolio chart (per-snapshot benchmark prices come from
        # each snapshot's own prices_json).
        "benchmark_start_price": state.benchmark_start_price if state.benchmark_start_price > 0 else None,
        "benchmark_start_value": state.benchmark_start_value if state.benchmark_start_value > 0 else None,
        "benchmark_value": round(benchmark_value, 2) if benchmark_value is not None else None,
        "alpha_usd": round(alpha_usd, 2) if alpha_usd is not None else None,
        "alpha_pct": round(alpha_pct, 2) if alpha_pct is not None else None,
        "realized_pnl_usd": round(realized, 2),
        "closed_trades": closed,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / closed * 100, 1) if closed > 0 else None,
        "since": state.benchmark_start_date or None,
    }


def reset_scorecard(db: Session) -> None:
    """Clears the benchmark baseline so a fresh start re-anchors it. Called by
    the data-wipe path; trade-derived stats reset naturally when trades are
    deleted."""
    state = risk_manager.get_state(db)
    state.benchmark_start_date = ""
    state.benchmark_start_price = 0.0
    state.benchmark_start_value = 0.0
    db.commit()
