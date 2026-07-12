"""Retrospective measurement: would the MECHANICAL FILTER ALONE (no Claude in
the loop) have done better or worse than what Claude actually decided?

Recomputed AFTER THE FACT from each cycle's already-stored technical snapshot
(Decision.market_data_snapshot already holds every whitelisted symbol's price
+ technical indicators for that cycle, not just the one symbol Claude acted
on) -- no live trading path is touched here, this is pure read-only analysis,
run on demand (a button), not on every poll.

The mechanical shadow simulates one independent position per symbol at a fixed
notional (SHADOW_NOTIONAL_USD) using the EXACT SAME entry filter
(signals.entry_confluence) and exit rules (trading_engine._decide_mechanical_exit)
as the live engine's own mechanical layer -- so this answers "is Claude's
judgment adding value on top of the mechanical filter, or would blindly taking
every mechanically-qualified signal have done just as well (or better)?"

Dollar totals are NOT directly comparable (the shadow uses a fixed notional per
symbol; the real account sizes by risk/confidence/allocation) -- so the
headline comparison is win rate and average return per trade, with both
dollar figures shown for context only.
"""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Decision
from app.services import signals
from app.services.trading_engine import _base_asset, _decide_mechanical_exit, compute_symbol_stats, dynamic_stop_loss_pct

# Fixed notional per shadow "position" -- isolates each symbol's trade quality
# from the real account's cash constraints / position sizing, so the
# comparison measures signal quality, not capital allocation.
SHADOW_NOTIONAL_USD = 1000.0


def _mechanical_would_buy(settings: Settings, technical: dict) -> bool:
    return signals.entry_confluence(settings, technical).ok


def compute_claude_edge(db: Session, settings: Settings, venue: str = "alpaca") -> dict:
    """Walks this venue's full decision history in order, replaying the
    mechanical-only entry/exit rules against the same recorded prices, and
    compares the result to what Claude-directed trading actually realized."""
    decisions = db.execute(
        select(Decision).where(Decision.venue == venue).order_by(Decision.timestamp.asc())
    ).scalars().all()

    state: dict[str, dict] = {}  # symbol -> {entry, peak, partial_taken, remaining_frac}
    shadow_trades: list[dict] = []  # closed/partial shadow exits: {pnl_pct, frac}
    cycles = 0

    for d in decisions:
        try:
            market_data = json.loads(d.market_data_snapshot or "{}")
        except (TypeError, ValueError):
            continue
        if not market_data:
            continue
        cycles += 1
        for symbol, info in market_data.items():
            technical = info.get("technical") or {}
            price = info.get("price")
            if price is None or not technical:
                continue

            pos = state.get(symbol)
            if pos is None:
                if _mechanical_would_buy(settings, technical):
                    state[symbol] = {"entry": price, "peak": price, "partial_taken": False, "remaining_frac": 1.0}
                continue

            pos["peak"] = max(pos["peak"], price)
            stop_pct = dynamic_stop_loss_pct(settings, technical.get("volatility_pct_1h"))
            base = _base_asset(symbol, settings.quote_currency)
            _reason, sell_pct, kind = _decide_mechanical_exit(
                settings, base, pos["entry"], price, pos["peak"],
                stop_pct=stop_pct, partial_taken=pos["partial_taken"],
            )
            if kind is None:
                continue

            pnl_pct = (price - pos["entry"]) / pos["entry"] * 100
            frac_closed = pos["remaining_frac"] * (sell_pct / 100)
            shadow_trades.append({"pnl_pct": pnl_pct, "frac": frac_closed})
            if kind == "partial":
                pos["partial_taken"] = True
                pos["remaining_frac"] -= frac_closed
            else:
                del state[symbol]

    mech_wins = sum(1 for t in shadow_trades if t["pnl_pct"] >= 0)
    mech_closed = len(shadow_trades)
    frac_total = sum(t["frac"] for t in shadow_trades)
    mech_avg_pct = (
        round(sum(t["pnl_pct"] * t["frac"] for t in shadow_trades) / frac_total, 2) if frac_total > 0 else None
    )
    mech_realized_usd = round(sum(t["pnl_pct"] / 100 * t["frac"] * SHADOW_NOTIONAL_USD for t in shadow_trades), 2)

    actual_by_symbol = compute_symbol_stats(db, venue=venue)
    actual_closed = sum(v["closed"] for v in actual_by_symbol.values())
    actual_wins = sum(v["wins"] for v in actual_by_symbol.values())
    actual_realized_usd = round(sum(v["realized_pnl"] for v in actual_by_symbol.values()), 2)

    return {
        "venue": venue,
        "cycles_analyzed": cycles,
        "mechanical_only": {
            "closed_trades": mech_closed,
            "wins": mech_wins,
            "losses": mech_closed - mech_wins,
            "win_rate_pct": round(mech_wins / mech_closed * 100, 1) if mech_closed else None,
            "avg_return_pct": mech_avg_pct,
            "notional_realized_usd": mech_realized_usd,
        },
        "with_claude": {
            "closed_trades": actual_closed,
            "wins": actual_wins,
            "losses": actual_closed - actual_wins,
            "win_rate_pct": round(actual_wins / actual_closed * 100, 1) if actual_closed else None,
            "realized_usd": actual_realized_usd,
        },
    }
