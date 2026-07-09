"""Deterministic backtest.

Replays historical bars through the SAME mechanical entry filter + exit geometry
the live engine uses -- WITHOUT Claude (non-deterministic and paid). It measures
the strategy's core, tunable edge (win rate, expectancy in R, return, alpha vs
buy-and-hold, max drawdown) BEFORE any real money is risked, so the geometry and
filters can be tuned on data instead of guesswork. Claude sits on top of this
mechanical baseline in production; the baseline is the measurable floor.

Pure and self-contained: give it {symbol: [closes...]} (oldest first, aligned
by index) and a Settings, get a report dict back. No DB, no network.
"""

import math
from dataclasses import dataclass, field

from app.config import Settings
from app.services import signals
from app.services.technical_indicators import compute_technical_indicators, compute_volatility_pct
from app.services.trading_engine import (
    MIN_SELL_NOTIONAL_USD,
    _decide_mechanical_exit,
    dynamic_stop_loss_pct,
    risk_based_size_cap,
)

WARMUP = 210  # need SMA200 (+ a little) before the first signal is meaningful
VOL_WINDOW = 30


@dataclass
class _Pos:
    qty: float
    cost: float
    peak: float
    entry_idx: int
    entry_stop_pct: float
    entry_risk_usd: float
    partial: bool = False


def _min_hold_bars(settings: Settings) -> int:
    return math.ceil(settings.min_hold_minutes / 60) if settings.min_hold_minutes > 0 else 0


def run_backtest(
    closes_by_symbol: dict[str, list[float]],
    settings: Settings,
    *,
    benchmark_symbol: str | None = None,
    starting_cash: float = 1000.0,
) -> dict:
    symbols = [s for s, c in closes_by_symbol.items() if len(c) > WARMUP]
    if not symbols:
        return {"error": "insufficient history", "bars": 0}
    n = min(len(closes_by_symbol[s]) for s in symbols)

    cash = starting_cash
    positions: dict[str, _Pos] = {}
    equity_curve: list[float] = []
    sell_returns_r: list[float] = []  # R-multiple booked on each SELL slice
    wins = losses = 0
    realized_total = 0.0
    n_entries = 0
    min_hold = _min_hold_bars(settings)

    bench = benchmark_symbol if benchmark_symbol in closes_by_symbol else None
    bench_shares = starting_cash / closes_by_symbol[bench][WARMUP] if bench else None

    for t in range(WARMUP, n):
        # ---- exits on held positions ----
        for s in list(positions):
            series = closes_by_symbol[s][: t + 1]
            price = series[t]
            pos = positions[s]
            pos.peak = max(pos.peak, price)
            basis = pos.cost / pos.qty
            stop_pct = dynamic_stop_loss_pct(settings, compute_volatility_pct(series[-VOL_WINDOW - 2:]))
            reason, sell_pct, kind = _decide_mechanical_exit(
                settings, s, basis, price, pos.peak, stop_pct=stop_pct, partial_taken=pos.partial
            )
            if kind is None:
                continue
            # Minimum hold blocks non-stop exits (the hard stop always fires).
            if kind != "stop" and min_hold and (t - pos.entry_idx) < min_hold:
                continue
            sell_qty = pos.qty * (sell_pct / 100)
            if kind == "partial" and sell_qty * price < MIN_SELL_NOTIONAL_USD:
                continue
            pnl = (price - basis) * sell_qty
            cash += sell_qty * price
            realized_total += pnl
            if pos.entry_risk_usd > 0:
                sell_returns_r.append(pnl / pos.entry_risk_usd)
            if pnl >= 0:
                wins += 1
            else:
                losses += 1
            if kind == "partial":
                pos.qty -= sell_qty
                pos.cost = basis * pos.qty
                pos.partial = True
            else:
                del positions[s]

        # ---- entries ----
        equity = cash + sum(closes_by_symbol[s][t] * p.qty for s, p in positions.items())
        for s in symbols:
            if s in positions:
                continue
            if settings.max_concurrent_positions > 0 and len(positions) >= settings.max_concurrent_positions:
                break
            series = closes_by_symbol[s][: t + 1]
            technical = compute_technical_indicators(series)
            if settings.entry_filter_enabled and not signals.entry_confluence(settings, technical).ok:
                continue
            price = series[t]
            stop_pct = dynamic_stop_loss_pct(settings, technical.get("volatility_pct_1h"))
            cap = risk_based_size_cap(settings, {"total_value_usdt": equity, "usdt_balance": cash}, stop_pct)
            size_pct = min(cap, settings.max_position_pct)
            if s in settings.high_spread_symbol_list and settings.high_spread_size_scale < 1.0:
                size_pct *= settings.high_spread_size_scale
            value = cash * size_pct / 100
            if value < MIN_SELL_NOTIONAL_USD:
                continue
            qty = value / price
            cash -= value
            positions[s] = _Pos(
                qty=qty, cost=value, peak=price, entry_idx=t,
                entry_stop_pct=stop_pct, entry_risk_usd=value * stop_pct / 100,
            )
            n_entries += 1

        equity_curve.append(cash + sum(closes_by_symbol[s][t] * p.qty for s, p in positions.items()))

    # Liquidate whatever is still open at the last price.
    last = n - 1
    for s, p in positions.items():
        cash += closes_by_symbol[s][last] * p.qty
    final_equity = cash
    if equity_curve:
        equity_curve[-1] = final_equity

    closed = wins + losses
    total_return_pct = (final_equity / starting_cash - 1) * 100
    bench_return_pct = (
        (bench_shares * closes_by_symbol[bench][last] / starting_cash - 1) * 100 if bench else None
    )
    peak = -math.inf
    max_dd = 0.0
    for e in equity_curve:
        peak = max(peak, e)
        if peak > 0:
            max_dd = max(max_dd, (peak - e) / peak * 100)

    return {
        "bars": n - WARMUP,
        "entries": n_entries,
        "closed_trades": closed,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / closed * 100, 1) if closed else None,
        "avg_R": round(sum(sell_returns_r) / len(sell_returns_r), 3) if sell_returns_r else None,
        "expectancy_R": round(sum(sell_returns_r) / len(sell_returns_r), 3) if sell_returns_r else None,
        "realized_pnl_usd": round(realized_total, 2),
        "total_return_pct": round(total_return_pct, 2),
        "benchmark_return_pct": round(bench_return_pct, 2) if bench_return_pct is not None else None,
        "alpha_pct": round(total_return_pct - bench_return_pct, 2) if bench_return_pct is not None else None,
        "max_drawdown_pct": round(max_dd, 2),
        "final_equity": round(final_equity, 2),
    }
