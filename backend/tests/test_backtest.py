import math

from app.services import backtest, signals


def _uptrend(n=420, slope=0.0006, wobble=0.04, phase=0.0):
    """Deterministic gently-rising OHLC rows [t,o,h,l,c,v] (timestamp-aligned),
    so SMA50>SMA200 holds after warmup while RSI still dips out of overbought."""
    rows = []
    for i in range(n):
        c = 100 * (1 + slope) ** i * (1 + wobble * math.sin(i / 9 + phase))
        rows.append([i * 3600, c, c, c, c, 1000])  # hourly-spaced epoch stamps
    return rows


# ---- entry-confluence filter --------------------------------------------
def test_entry_confluence_passes_on_trend_momentum(settings):
    tech = {"sma50_vs_sma200_1h": "above", "macd_signal": "bullish", "rsi_14": 58.0, "volatility_pct_1h": 1.0}
    sig = signals.entry_confluence(settings.model_copy(update={"entry_min_score": 2}), tech)
    assert sig.ok is True
    assert sig.score == 3


def test_entry_confluence_high_rsi_does_not_veto_a_strong_trend(settings):
    """A trending name with persistently high RSI (the NVDA/MSTR case) must
    still be allowed through -- an earlier hard veto here filtered out exactly
    the continuation entries the strategy most needs, per the 6-year backtest."""
    tech = {"sma50_vs_sma200_1h": "above", "macd_signal": "bullish", "rsi_14": 80.0}
    sig = signals.entry_confluence(settings.model_copy(update={"entry_min_score": 2}), tech)
    assert sig.ok is True
    assert sig.score == 3  # trend + MACD + RSI-momentum all still count


def test_entry_confluence_blocks_when_no_data(settings):
    tech = {"sma50_vs_sma200_1h": "insufficient_data", "macd_signal": "insufficient_data", "rsi_14": None}
    assert signals.entry_confluence(settings, tech).ok is False


# ---- backtest engine ----------------------------------------------------
def test_backtest_runs_and_reports_uptrend(settings):
    s = settings.model_copy(update={
        "entry_filter_enabled": False, "risk_per_trade_pct": 1.0,
        "partial_take_profit_enabled": True, "max_concurrent_positions": 4,
        "min_hold_minutes": 0, "max_position_pct": 50.0,
    })
    data = {"SPY": _uptrend(), "QQQ": _uptrend(phase=1.0)}
    report = backtest.run_backtest(data, s, benchmark_symbol="SPY", starting_cash=1000.0)

    for key in ("steps", "entries", "closed_trades", "win_rate_pct", "expectancy_R", "total_return_pct", "alpha_pct", "max_drawdown_pct"):
        assert key in report
    assert report["steps"] > 0
    assert report["entries"] > 0
    assert report["total_return_pct"] > 0  # a rising market should make money


def test_backtest_entry_filter_is_selective(settings):
    base = {
        "risk_per_trade_pct": 1.0, "partial_take_profit_enabled": True,
        "max_concurrent_positions": 4, "min_hold_minutes": 0, "max_position_pct": 50.0,
    }
    data = {"SPY": _uptrend(), "QQQ": _uptrend(phase=2.0)}
    off = backtest.run_backtest(data, settings.model_copy(update={**base, "entry_filter_enabled": False}), benchmark_symbol="SPY")
    on = backtest.run_backtest(data, settings.model_copy(update={**base, "entry_filter_enabled": True, "entry_min_score": 2}), benchmark_symbol="SPY")
    # The filter only ever removes entries -- it can never add them.
    assert on["entries"] <= off["entries"]


def test_backtest_handles_insufficient_history(settings):
    report = backtest.run_backtest({"SPY": [100.0, 101.0, 102.0]}, settings, benchmark_symbol="SPY")
    assert report.get("error") == "insufficient history"


# ---- yearly / regime breakdown ------------------------------------------
def test_yearly_breakdown_flags_a_bad_year_even_when_overall_return_is_positive(settings):
    """Simulates a strategy that grinds up steadily while the benchmark crashes
    hard in year 2 then recovers in year 3 -- the yearly breakdown must show
    the strategy protecting capital in the crash year even though the
    aggregate multi-year numbers alone wouldn't reveal that."""
    from app.services.backtest import _yearly_breakdown

    day = 86400
    year_starts = [0, 365 * day, 2 * 365 * day, 3 * 365 * day]
    timeline = [year_starts[0], year_starts[1] - day, year_starts[1], year_starts[2] - day, year_starts[2], year_starts[3] - day]
    # Strategy equity: steady grind up throughout.
    equity_curve = [1000, 1020, 1040, 1060, 1080, 1100]
    # Benchmark: flat, then crashes -40% in year 2, partially recovers in year 3.
    bench_curve = [1000, 1010, 1020, 600, 610, 750]

    rows = _yearly_breakdown(timeline, equity_curve, bench_curve)
    by_year = {r["year"]: r for r in rows}

    # The crash year: strategy should show strongly positive alpha (protected capital).
    crash_year = sorted(by_year)[1]
    assert by_year[crash_year]["alpha_pct"] > 20


def test_backtest_report_includes_yearly_breakdown_and_benchmark_drawdown(settings):
    s = settings.model_copy(update={
        "entry_filter_enabled": False, "risk_per_trade_pct": 1.0,
        "max_concurrent_positions": 4, "min_hold_minutes": 0, "max_position_pct": 50.0,
    })
    data = {"SPY": _uptrend(n=800), "QQQ": _uptrend(n=800, phase=1.0)}
    report = backtest.run_backtest(data, s, benchmark_symbol="SPY", starting_cash=1000.0)

    assert "yearly_breakdown" in report
    assert isinstance(report["yearly_breakdown"], list)
    assert len(report["yearly_breakdown"]) >= 1
    assert "benchmark_max_drawdown_pct" in report
    assert "years_beating_benchmark" in report
    row = report["yearly_breakdown"][0]
    assert set(row.keys()) == {"year", "strategy_return_pct", "benchmark_return_pct", "alpha_pct"}


def test_backtest_handles_millisecond_timestamps_without_crashing(settings):
    """Regression: Yahoo bars carry epoch-MILLISECOND timestamps. Earlier these
    flowed into datetime.fromtimestamp() as if they were seconds and blew up
    the yearly breakdown with 'year out of range'. Feed ms-stamped multi-year
    data and assert it runs and buckets into sane calendar years."""
    import math

    s = settings.model_copy(update={
        "entry_filter_enabled": False, "risk_per_trade_pct": 1.0,
        "max_concurrent_positions": 4, "min_hold_minutes": 0, "max_position_pct": 50.0,
    })
    day_ms = 86_400_000
    start_ms = 1_167_609_600_000  # 2007-01-01 in ms
    rows = []
    for i in range(900):  # ~2.5 years of daily bars
        c = 100 * (1.0004) ** i * (1 + 0.03 * math.sin(i / 9))
        rows.append([start_ms + i * day_ms, c, c, c, c, 1000])
    report = backtest.run_backtest({"SPY": rows, "QQQ": rows}, s, benchmark_symbol="SPY")

    assert "error" not in report
    years = [row["year"] for row in report["yearly_breakdown"]]
    assert all(2006 <= y <= 2011 for y in years)  # sane calendar years, not 38551
    assert len(years) >= 2
