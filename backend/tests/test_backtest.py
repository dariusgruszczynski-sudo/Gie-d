import math

from app.services import backtest, signals


def _uptrend(n=420, slope=0.0006, wobble=0.04, phase=0.0):
    """Deterministic gently-rising series with oscillation, so SMA50>SMA200
    holds after warmup while RSI still dips out of overbought on pullbacks."""
    return [100 * (1 + slope) ** i * (1 + wobble * math.sin(i / 9 + phase)) for i in range(n)]


# ---- entry-confluence filter --------------------------------------------
def test_entry_confluence_passes_on_trend_momentum(settings):
    tech = {"sma50_vs_sma200_1h": "above", "macd_signal": "bullish", "rsi_14": 58.0, "volatility_pct_1h": 1.0}
    sig = signals.entry_confluence(settings.model_copy(update={"entry_min_score": 2}), tech)
    assert sig.ok is True
    assert sig.score == 3


def test_entry_confluence_vetoes_overbought(settings):
    tech = {"sma50_vs_sma200_1h": "above", "macd_signal": "bullish", "rsi_14": 80.0}
    sig = signals.entry_confluence(settings.model_copy(update={"entry_min_score": 2, "entry_rsi_overbought": 72.0}), tech)
    assert sig.ok is False  # RSI veto overrides an otherwise-strong score


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

    for key in ("bars", "entries", "closed_trades", "win_rate_pct", "expectancy_R", "total_return_pct", "alpha_pct", "max_drawdown_pct"):
        assert key in report
    assert report["bars"] > 0
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
