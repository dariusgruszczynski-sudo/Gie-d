"""Mechanical entry-confluence filter.

Entry edge (win rate) is the FIRST-ORDER driver of profitability -- a path
Monte-Carlo of the exit geometry showed the geometry itself can't manufacture
profit from noise (E[R]≈0 with no edge), while a small positive drift swings
expectancy hugely. So before capital is committed a BUY must clear a simple,
transparent confluence of trend + momentum + RSI. Trading WITH the trend avoids
knife-catching and lifts the win rate. Works on any instrument's own price
series -- an inverse ETF (SH/PSQ) trending up IS a valid long (market falling).

A 6-year backtest (see scripts/run_backtest.py) showed the filter, as first
shipped, made results WORSE: fewer entries, lower expectancy, lower total
return than with the filter off, at roughly the same win rate. Root cause:
the RSI>=entry_rsi_overbought veto is a MEAN-REVERSION idea ("don't buy
something that's already run up") bolted onto a TREND-FOLLOWING system. In a
genuine multi-month trend (the NVDA/MSTR-style moves this strategy most needs
to catch), RSI sitting persistently above 70 is normal and often a sign of
STRENGTH, not exhaustion -- the veto was filtering out continuation entries
into exactly the trends worth being in. Fixed: RSI no longer hard-blocks a
BUY, only contributes to the confluence score like the other two signals.
"""

from dataclasses import dataclass, field

from app.config import Settings


@dataclass
class EntrySignal:
    ok: bool
    score: int
    reasons: list[str] = field(default_factory=list)


def entry_confluence(settings: Settings, technical: dict) -> EntrySignal:
    """Score 0-3 over {SMA50>SMA200, MACD bullish, RSI in a healthy zone}; a BUY
    is allowed when score >= entry_min_score. `technical` is a
    compute_technical_indicators() dict (may hold None when there isn't enough
    history yet -> treated as 'signal absent'). RSI staying elevated during a
    genuine trend is normal, not a reason to veto -- it only ever ADDS to the
    score (momentum zone or a fresh oversold bounce), never blocks on its own."""
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
        if rsi >= 45:
            score += 1
            reasons.append(f"RSI {rsi} (momentum)")
        elif rsi < 35:
            score += 1
            reasons.append(f"RSI {rsi} (wyprzedanie/odbicie)")

    ok = score >= settings.entry_min_score
    return EntrySignal(ok=ok, score=score, reasons=reasons)
