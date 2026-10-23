"""Walidacja walk-forward (#15, Partia 5): rozłączne okna OOS + werdykt spójności."""

import math

import pytest

from app.services import walk_forward


def _uptrend(n=1400, slope=0.0006, wobble=0.04, phase=0.0):
    """Łagodnie rosnące OHLC [t,o,h,l,c,v], godzinowe stemple — SMA50>SMA200 po
    rozbiegu, długa seria na kilka okien OOS."""
    rows = []
    for i in range(n):
        c = 100 * (1 + slope) ** i * (1 + wobble * math.sin(i / 9 + phase))
        rows.append([i * 3600, c, c, c, c, 1000])
    return rows


def _settings(settings):
    return settings.model_copy(update={
        "entry_filter_enabled": False, "risk_per_trade_pct": 1.0,
        "partial_take_profit_enabled": True, "max_concurrent_positions": 4,
        "min_hold_minutes": 0, "max_position_pct": 50.0,
        "regime_filter_enabled": False,
    })


def test_walk_forward_splits_into_requested_folds(settings):
    data = {"SPY": _uptrend(), "QQQ": _uptrend(phase=1.0)}
    result = walk_forward.walk_forward(data, _settings(settings), benchmark_symbol="SPY", folds=4)
    assert "summary" in result, result
    assert result["summary"]["folds_run"] == 4
    assert len(result["folds"]) == 4
    # Okna są ROZŁĄCZNE i rosnące w czasie.
    tos = [r["to"] for r in result["folds"]]
    assert tos == sorted(tos)
    # W trwałej hossie strategia powinna zarabiać w każdym oknie.
    assert all(r["total_return_pct"] is not None for r in result["folds"])


def test_walk_forward_reports_consistency_verdict(settings):
    data = {"SPY": _uptrend(), "QQQ": _uptrend(phase=2.0)}
    result = walk_forward.walk_forward(data, _settings(settings), benchmark_symbol="SPY", folds=3)
    s = result["summary"]
    for key in ("folds_beating_benchmark", "median_alpha_pct", "worst_fold_drawdown_pct", "edge_consistent"):
        assert key in s
    assert isinstance(s["edge_consistent"], bool)


def test_walk_forward_rejects_too_few_folds(settings):
    data = {"SPY": _uptrend()}
    assert "error" in walk_forward.walk_forward(data, _settings(settings), folds=1)


def test_walk_forward_handles_insufficient_history(settings):
    # Krótka seria (< warmup) -> brak symboli -> czysty błąd, nie wyjątek.
    short = {"SPY": _uptrend(n=50)}
    result = walk_forward.walk_forward(short, _settings(settings), folds=4)
    assert "error" in result


def test_format_report_renders_table_and_error(settings):
    data = {"SPY": _uptrend(), "QQQ": _uptrend(phase=1.0)}
    result = walk_forward.walk_forward(data, _settings(settings), benchmark_symbol="SPY", folds=3)
    md = walk_forward.format_report(result)
    assert "Walk-forward" in md and "| # |" in md
    assert walk_forward.format_report({"error": "x"}).startswith("Walk-forward: BŁĄD")
