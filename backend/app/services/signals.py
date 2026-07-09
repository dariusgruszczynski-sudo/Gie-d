"""Mechanical entry-confluence filter.

Entry edge (win rate) is the FIRST-ORDER driver of profitability -- a path
Monte-Carlo of the exit geometry showed the geometry itself can't manufacture
profit from noise (E[R]≈0 with no edge), while a small positive drift swings
expectancy hugely. So before capital is committed a BUY must clear a simple,
transparent confluence of trend + momentum + RSI. Trading WITH the trend avoids
knife-catching and lifts the win rate. Works on any instrument's own price
series -- an inverse ETF (SH/PSQ) trending up IS a valid long (market falling).
"""

from dataclasses import dataclass, field

from app.config import Settings


@dataclass
class EntrySignal:
    ok: bool
    score: int
    reasons: list[str] = field(default_factory=list)


def entry_confluence(settings: Settings, technical: dict) -> EntrySignal:
    """Score 0-3 over {SMA50>SMA200, MACD bullish, RSI in a healthy long zone};
    a BUY is allowed when score >= entry_min_score AND RSI is not overbought.
    `technical` is a compute_technical_indicators() dict (may hold None when
    there isn't enough history yet -> treated as 'signal absent')."""
    trend = technical.get("sma50_vs_sma200_1h")
    macd = technical.get("macd_signal")
    rsi = technical.get("rsi_14")

    score = 0
    reasons: list[str] = []

    if trend == "above":
        score += 1
        reasons.append("trend SMA50>SMA200")
    if macd in ("bullish", "bullish_cross"):
        score += 1
        reasons.append(f"MACD {macd}")
    if rsi is not None:
        if 45 <= rsi < settings.entry_rsi_overbought:
            score += 1
            reasons.append(f"RSI {rsi} (momentum)")
        elif rsi < 35:
            score += 1
            reasons.append(f"RSI {rsi} (wyprzedanie/odbicie)")

    overbought = rsi is not None and rsi >= settings.entry_rsi_overbought
    if overbought:
        reasons.append(f"RSI {rsi} wykupienie → weto")

    ok = score >= settings.entry_min_score and not overbought
    return EntrySignal(ok=ok, score=score, reasons=reasons)
