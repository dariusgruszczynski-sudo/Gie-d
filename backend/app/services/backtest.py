"""Deterministic backtest.

Replays historical bars through the SAME mechanical entry filter + exit geometry
the live engine uses -- WITHOUT Claude (non-deterministic and paid). It measures
the strategy's core, tunable edge (win rate, expectancy in R, return, alpha vs
buy-and-hold, max drawdown) BEFORE any real money is risked.

Bars are aligned by TIMESTAMP (not list index), so symbols with different
history lengths / start dates don't collapse the window. Pure and self-contained:
give it {symbol: [[t,o,h,l,c,v], ...]} (oldest first) + a Settings, get a report.

Note on timeframe: on the free Alpaca feed hourly history is too short for a
200-bar SMA (~30 trading days of 1h bars), so the runner defaults to DAILY bars
-- this measures the same LOGIC/edge on a longer sample, not the exact live 1h
cadence. Stops/vol scale with the chosen timeframe.

The report includes a YEARLY breakdown (strategy vs benchmark return + alpha
per calendar year) -- a single aggregate number over a multi-year run can hide
a strategy that lags a raging bull market yet actually protects capital in a
crash year (2008/2020/2022). Feed it deep history via
app.services.historical_data (Yahoo, free, decades back) to see that; the
default Alpaca feed alone only reaches back a few years.
"""

import math
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone

from app.config import Settings
from app.services import signals
from app.services.technical_indicators import compute_technical_indicators, compute_volatility_pct
from app.services.trading_engine import (
    MIN_SELL_NOTIONAL_USD,
    _decide_mechanical_exit,
    dynamic_stop_loss_pct,
    risk_based_size_cap,
)

WARMUP = 210          # bars before the first signal is meaningful (SMA200 + a bit)
VOL_WINDOW = 32


def _epoch(t) -> float:
    """Normalize a bar timestamp to epoch SECONDS. Accepts an ISO string
    (Alpaca), an epoch-milliseconds int (Yahoo), or epoch-seconds
    (synthetic data). Values above ~1e11 are treated as milliseconds -- 1e11
    seconds is ~year 5138, so no real trading date collides, while any ms
    timestamp today (~1.7e12) is safely above the threshold. Without this,
    ms timestamps flowed straight into datetime.fromtimestamp() and blew up
    with 'year out of range' in the yearly breakdown."""
    if isinstance(t, (int, float)):
        v = float(t)
        return v / 1000.0 if abs(v) > 1e11 else v
    try:
        return datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _yearly_breakdown(timeline: list[float], equity_curve: list[float], bench_curve: list[float | None]) -> list[dict]:
    """Splits the run into calendar years and reports strategy vs benchmark
    return for EACH one -- the whole point of testing 20 years instead of the
    last bull run: a system can lag buy-and-hold in a raging uptrend yet still
    be worth running if it protects capital in years like 2008/2022, which a
    single aggregate number can't show."""
    if not timeline:
        return []
    year_of = [datetime.fromtimestamp(t, tz=timezone.utc).year for t in timeline]
    bounds: "OrderedDict[int, list[int]]" = OrderedDict()
    for i, y in enumerate(year_of):
        if y not in bounds:
            bounds[y] = [i, i]
        else:
            bounds[y][1] = i

    rows = []
    prev_equity = equity_curve[0]
    prev_bench = next((b for b in bench_curve if b is not None), None)
    for year, (start_i, end_i) in bounds.items():
        end_equity = equity_curve[end_i]
        strat_ret = (end_equity / prev_equity - 1) * 100 if prev_equity else None

        end_bench = bench_curve[end_i]
        bench_ret = (end_bench / prev_bench - 1) * 100 if prev_bench and end_bench is not None else None

        alpha = strat_ret - bench_ret if strat_ret is not None and bench_ret is not None else None
        rows.append({
            "year": year,
            "strategy_return_pct": round(strat_ret, 2) if strat_ret is not None else None,
            "benchmark_return_pct": round(bench_ret, 2) if bench_ret is not None else None,
            "alpha_pct": round(alpha, 2) if alpha is not None else None,
        })
        prev_equity = end_equity
        if end_bench is not None:
            prev_bench = end_bench
    return rows


@dataclass
class _Pos:
    qty: float
    cost: float
    peak: float
    entry_i: int
    entry_risk_usd: float
    partial: bool = False


def run_backtest(
    bars_by_symbol: dict[str, list[list]],
    settings: Settings,
    *,
    benchmark_symbol: str | None = None,
    starting_cash: float = 1000.0,
    warmup: int = WARMUP,
) -> dict:
    symbols = [s for s, b in bars_by_symbol.items() if len(b) > warmup]
    if not symbols:
        return {"error": "insufficient history", "bars": 0}

    closes = {s: [float(r[4]) for r in bars_by_symbol[s]] for s in symbols}
    times = {s: [_epoch(r[0]) for r in bars_by_symbol[s]] for s in symbols}
    timeline = sorted({e for s in symbols for e in times[s]})

    cash = starting_cash
    positions: dict[str, _Pos] = {}
    idx = {s: 0 for s in symbols}  # bars with time <= current step
    equity_curve: list[float] = []
    bench_curve: list[float | None] = []
    sell_returns_r: list[float] = []
    wins = losses = n_entries = 0
    realized_total = 0.0
    min_hold = math.ceil(settings.min_hold_minutes / 60) if settings.min_hold_minutes > 0 else 0

    bench = benchmark_symbol if benchmark_symbol in symbols else None
    bench_shares = None  # set once trading becomes possible, for a fair comparison

    for step, ti in enumerate(timeline):
        for s in symbols:
            while idx[s] < len(times[s]) and times[s][idx[s]] <= ti:
                idx[s] += 1

        # ---- exits ----
        for s in list(positions):
            if idx[s] == 0:
                continue
            sc = closes[s][: idx[s]]
            price = sc[-1]
            pos = positions[s]
            pos.peak = max(pos.peak, price)
            basis = pos.cost / pos.qty
            stop_pct = dynamic_stop_loss_pct(settings, compute_volatility_pct(sc[-(VOL_WINDOW + 2):]))
            reason, sell_pct, kind = _decide_mechanical_exit(
                settings, s, basis, price, pos.peak, stop_pct=stop_pct, partial_taken=pos.partial
            )
            if kind is None:
                continue
            if kind != "stop" and min_hold and (step - pos.entry_i) < min_hold:
                continue
            sell_qty = pos.qty * (sell_pct / 100)
            if kind == "partial" and sell_qty * price < MIN_SELL_NOTIONAL_USD:
                continue
            pnl = (price - basis) * sell_qty
            cash += sell_qty * price
            realized_total += pnl
            if pos.entry_risk_usd > 0:
                sell_returns_r.append(pnl / pos.entry_risk_usd)
            wins += 1 if pnl >= 0 else 0
            losses += 1 if pnl < 0 else 0
            if kind == "partial":
                pos.qty -= sell_qty
                pos.cost = basis * pos.qty
                pos.partial = True
            else:
                del positions[s]

        equity = cash + sum(closes[s][idx[s] - 1] * p.qty for s, p in positions.items() if idx[s] > 0)

        # ---- benchmark baseline: buy-and-hold from the first tradeable step ----
        if bench and bench_shares is None and idx[bench] > warmup:
            bench_shares = starting_cash / closes[bench][idx[bench] - 1]
            bench_start_equity = starting_cash

        # ---- entries ----
        for s in symbols:
            if s in positions or idx[s] <= warmup:
                continue
            if settings.max_concurrent_positions > 0 and len(positions) >= settings.max_concurrent_positions:
                break
            sc = closes[s][: idx[s]]
            technical = compute_technical_indicators(sc)
            if settings.entry_filter_enabled and not signals.entry_confluence(settings, technical).ok:
                continue
            price = sc[-1]
            stop_pct = dynamic_stop_loss_pct(settings, technical.get("volatility_pct_1h"))
            size_pct = min(
                risk_based_size_cap(settings, {"total_value_usdt": equity, "usdt_balance": cash}, stop_pct),
                settings.max_position_pct,
            )
            if s in settings.high_spread_symbol_list and settings.high_spread_size_scale < 1.0:
                size_pct *= settings.high_spread_size_scale
            value = cash * size_pct / 100
            if value < MIN_SELL_NOTIONAL_USD:
                continue
            cash -= value
            positions[s] = _Pos(
                qty=value / price, cost=value, peak=price, entry_i=step, entry_risk_usd=value * stop_pct / 100
            )
            n_entries += 1

        equity_curve.append(cash + sum(closes[s][idx[s] - 1] * p.qty for s, p in positions.items() if idx[s] > 0))
        bench_curve.append(
            bench_shares * closes[bench][idx[bench] - 1] if bench_shares is not None and idx[bench] > 0 else None
        )

    # Liquidate whatever is still open at each symbol's last price.
    for s, p in positions.items():
        cash += closes[s][-1] * p.qty
    final_equity = cash
    if equity_curve:
        equity_curve[-1] = final_equity

    closed = wins + losses
    total_return_pct = (final_equity / starting_cash - 1) * 100
    bench_return_pct = None
    if bench and bench_shares is not None:
        bench_return_pct = (bench_shares * closes[bench][-1] / bench_start_equity - 1) * 100

    def _max_dd(curve: list[float]) -> float:
        peak = -math.inf
        dd = 0.0
        for e in curve:
            peak = max(peak, e)
            if peak > 0:
                dd = max(dd, (peak - e) / peak * 100)
        return dd

    max_dd = _max_dd(equity_curve)
    bench_curve_clean = [b for b in bench_curve if b is not None]
    bench_max_dd = _max_dd(bench_curve_clean) if bench_curve_clean else None

    # CAGR + Calmar: the metrics that actually reveal this strategy's edge. In
    # ABSOLUTE return it lags a raging bull (it's underinvested), but Calmar
    # (CAGR per unit of max drawdown) is where a low-drawdown system wins -- it
    # earns its return with a fraction of the pain. span_years from the timeline
    # (epoch seconds) so a 20y run and a 2y run are compared on equal footing.
    span_years = (timeline[-1] - timeline[0]) / (365.25 * 86400) if len(timeline) > 1 else 0.0

    def _cagr(final: float, start: float) -> float | None:
        if span_years <= 0 or start <= 0 or final <= 0:
            return None
        return ((final / start) ** (1 / span_years) - 1) * 100

    def _calmar(cagr: float | None, dd: float | None) -> float | None:
        if cagr is None or not dd:  # dd of 0 -> undefined (no drawdown to divide by)
            return None
        return cagr / dd

    cagr_pct = _cagr(final_equity, starting_cash)
    bench_final = bench_shares * closes[bench][-1] if bench and bench_shares is not None else None
    bench_cagr_pct = _cagr(bench_final, bench_start_equity) if bench_final is not None else None
    calmar = _calmar(cagr_pct, max_dd)
    bench_calmar = _calmar(bench_cagr_pct, bench_max_dd)

    yearly = _yearly_breakdown(timeline, equity_curve, bench_curve)
    years_beating_benchmark = sum(1 for r in yearly if (r["alpha_pct"] or 0) > 0)
    years_with_alpha = sum(1 for r in yearly if r["alpha_pct"] is not None)

    avg_r = round(sum(sell_returns_r) / len(sell_returns_r), 3) if sell_returns_r else None
    return {
        "steps": len(timeline),
        "entries": n_entries,
        "closed_trades": closed,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": round(wins / closed * 100, 1) if closed else None,
        "avg_R": avg_r,
        "expectancy_R": avg_r,
        "realized_pnl_usd": round(realized_total, 2),
        "total_return_pct": round(total_return_pct, 2),
        "benchmark_return_pct": round(bench_return_pct, 2) if bench_return_pct is not None else None,
        "alpha_pct": round(total_return_pct - bench_return_pct, 2) if bench_return_pct is not None else None,
        "max_drawdown_pct": round(max_dd, 2),
        "benchmark_max_drawdown_pct": round(bench_max_dd, 2) if bench_max_dd is not None else None,
        # CAGR + Calmar: risk-adjusted view. Calmar = CAGR / max drawdown, so a
        # system that grows steadily with shallow drawdowns beats a boom-bust one
        # even at a lower headline return -- this is where the strategy shines.
        "cagr_pct": round(cagr_pct, 2) if cagr_pct is not None else None,
        "benchmark_cagr_pct": round(bench_cagr_pct, 2) if bench_cagr_pct is not None else None,
        "calmar": round(calmar, 2) if calmar is not None else None,
        "benchmark_calmar": round(bench_calmar, 2) if bench_calmar is not None else None,
        "final_equity": round(final_equity, 2),
        # Rok po roku: pokazuje, czy strategia broni kapitału w latach spadkowych
        # (2008/2020/2022), nawet jeśli w sumie przegrywa z hossą ostatnich lat.
        "yearly_breakdown": yearly,
        "years_beating_benchmark": f"{years_beating_benchmark}/{years_with_alpha}" if years_with_alpha else None,
    }
