"""Pure functions computing technical indicators from a list of closing
prices (oldest first). No network calls -- degrades to None /
"insufficient_data" when there isn't enough price history yet, so the
trading engine never blocks or fails because of this."""


def _sma(values: list[float], period: int) -> float | None:
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2 / (period + 1)
    ema = [values[0]]
    for price in values[1:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema


def compute_rsi(closes: list[float], period: int = 14) -> float | None:
    if len(closes) < period + 1:
        return None
    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 1)


def compute_macd_signal(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> str:
    if len(closes) < slow + signal:
        return "insufficient_data"
    ema_fast = _ema_series(closes, fast)
    ema_slow = _ema_series(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = _ema_series(macd_line, signal)
    macd_now, macd_prev = macd_line[-1], macd_line[-2]
    signal_now, signal_prev = signal_line[-1], signal_line[-2]
    if macd_prev <= signal_prev and macd_now > signal_now:
        return "bullish_cross"
    if macd_prev >= signal_prev and macd_now < signal_now:
        return "bearish_cross"
    return "bullish" if macd_now > signal_now else "bearish"


def compute_sma_trend(closes: list[float], fast_period: int = 50, slow_period: int = 200) -> str:
    sma_fast = _sma(closes, fast_period)
    sma_slow = _sma(closes, slow_period)
    if sma_fast is None or sma_slow is None:
        return "insufficient_data"
    return "above" if sma_fast > sma_slow else "below"


def compute_volatility_pct(closes: list[float], period: int = 24) -> float | None:
    """Standard deviation of the last `period` bar-to-bar percentage returns,
    in percent -- a simple realized-volatility proxy used to size volatile
    tickers (MSTR, NVDA) down so one wild name can't dominate P&L."""
    if len(closes) < period + 1:
        return None
    window = closes[-(period + 1):]
    returns = [
        (window[i] - window[i - 1]) / window[i - 1]
        for i in range(1, len(window))
        if window[i - 1] > 0
    ]
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    return round(variance**0.5 * 100, 3)


def compute_technical_indicators(closes: list[float]) -> dict:
    return {
        "rsi_14": compute_rsi(closes),
        "macd_signal": compute_macd_signal(closes),
        "sma50_vs_sma200_1h": compute_sma_trend(closes),
        "volatility_pct_1h": compute_volatility_pct(closes),
    }
