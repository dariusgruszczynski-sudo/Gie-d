from app.services.technical_indicators import (
    compute_macd_signal,
    compute_rsi,
    compute_sma_trend,
    compute_technical_indicators,
)


def test_rsi_returns_none_with_insufficient_data():
    assert compute_rsi([100.0, 101.0, 102.0]) is None


def test_rsi_all_gains_is_100():
    closes = [100.0 + i for i in range(20)]  # strictly rising
    assert compute_rsi(closes) == 100.0


def test_rsi_all_losses_is_0():
    closes = [100.0 - i for i in range(20)]  # strictly falling
    assert compute_rsi(closes) == 0.0


def test_macd_signal_insufficient_data():
    assert compute_macd_signal([100.0] * 10) == "insufficient_data"


def test_macd_signal_bullish_on_sustained_uptrend():
    closes = [100.0 + i * 0.5 for i in range(60)]
    assert compute_macd_signal(closes) in {"bullish", "bullish_cross"}


def test_sma_trend_insufficient_data():
    assert compute_sma_trend([100.0] * 10) == "insufficient_data"


def test_sma_trend_above_on_sustained_uptrend():
    closes = [100.0 + i * 0.5 for i in range(210)]
    assert compute_sma_trend(closes) == "above"


def test_compute_technical_indicators_returns_all_keys():
    result = compute_technical_indicators([100.0] * 5)
    assert set(result) == {"rsi_14", "macd_signal", "sma50_vs_sma200_1h"}
