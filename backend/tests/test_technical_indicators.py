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
    assert set(result) == {"rsi_14", "macd_signal", "sma50_vs_sma200_1h", "volatility_pct_1h"}


def test_volatility_none_on_insufficient_data():
    from app.services.technical_indicators import compute_volatility_pct

    assert compute_volatility_pct([100.0, 101.0], period=24) is None


def test_volatility_higher_for_choppier_series():
    from app.services.technical_indicators import compute_volatility_pct

    calm = [100.0 + i * 0.1 for i in range(30)]
    wild = [100.0 * (1.05 if i % 2 else 0.95) for i in range(30)]
    assert compute_volatility_pct(wild) > compute_volatility_pct(calm)


def test_donchian_high_excludes_current_bar():
    from app.services.technical_indicators import donchian_high

    highs = [10.0, 11.0, 12.0, 11.5, 13.0]  # bieżąca (ostatnia) = 13 wykluczona
    assert donchian_high(highs, 3) == 12.0   # max z [11,12,11.5]
    assert donchian_high(highs, 10) is None  # za mało historii
    assert donchian_high([], 5) is None


def test_compute_adx_strong_vs_flat_trend():
    from app.services.technical_indicators import compute_adx

    n = 40
    # Silny, jednokierunkowy trend -> wysoki ADX.
    up_c = [100.0 + i for i in range(n)]
    up_h = [c + 0.5 for c in up_c]
    up_l = [c - 0.5 for c in up_c]
    # Płaski, boczny rynek -> niski ADX.
    flat_c = [100.0 + (0.2 if i % 2 else -0.2) for i in range(n)]
    flat_h = [c + 0.3 for c in flat_c]
    flat_l = [c - 0.3 for c in flat_c]
    adx_trend = compute_adx(up_h, up_l, up_c)
    adx_flat = compute_adx(flat_h, flat_l, flat_c)
    assert adx_trend is not None and adx_flat is not None
    assert adx_trend > adx_flat
    assert compute_adx([1.0] * 5, [1.0] * 5, [1.0] * 5) is None  # za mało świec
