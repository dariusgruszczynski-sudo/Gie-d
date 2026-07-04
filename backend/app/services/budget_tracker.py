"""Estimated Claude API spend tracking.

Anthropic's API has no endpoint to read the actual prepaid console balance --
this is a self-tracked estimate (real token usage from each response x known
Opus 4.8 pricing) measured against a monthly budget the user sets to match
what they've loaded on console.anthropic.com. Treat it as a directional
warning, not an exact balance reading.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.services import risk_manager

OPUS_INPUT_USD_PER_MTOK = 5.0
OPUS_OUTPUT_USD_PER_MTOK = 25.0


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * OPUS_INPUT_USD_PER_MTOK + (
        output_tokens / 1_000_000
    ) * OPUS_OUTPUT_USD_PER_MTOK


def record_usage(db: Session, input_tokens: int, output_tokens: int) -> None:
    state = risk_manager.get_state(db)
    month_key = date.today().strftime("%Y-%m")
    if state.claude_budget_month_key != month_key:
        state.claude_budget_month_key = month_key
        state.claude_spend_usd_this_month = 0.0
    state.claude_spend_usd_this_month += estimate_cost_usd(input_tokens, output_tokens)
    db.commit()


def get_budget_status(db: Session, settings: Settings) -> dict:
    state = risk_manager.get_state(db)
    today_month = date.today().strftime("%Y-%m")
    spent = state.claude_spend_usd_this_month if state.claude_budget_month_key == today_month else 0.0
    budget = settings.claude_monthly_budget_usd
    pct_used = (spent / budget * 100) if budget > 0 else 0.0
    return {
        "claude_monthly_budget_usd": budget,
        "claude_spend_usd_this_month": round(spent, 4),
        "claude_budget_pct_used": round(pct_used, 1),
        "claude_budget_alert": pct_used >= settings.claude_budget_alert_threshold_pct,
    }
