"""Estimated Claude API spend tracking.

Anthropic's API has no endpoint to read the actual prepaid console balance --
this is a self-tracked estimate (real token usage from each response x known
per-model pricing) measured against a monthly budget the user sets to match
what they've loaded on console.anthropic.com. Treat it as a directional
warning, not an exact balance reading.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.config import Settings
from app.services import risk_manager

# (input $/1M tokens, output $/1M tokens) per model. The advisor now routes
# most cycles through the cheap/fast model and only escalates to Opus for
# low-confidence calls, so pricing must be looked up per-model rather than
# assumed to always be Opus.
MODEL_PRICING_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
}
# Unknown/future model id -- price conservatively at the more expensive known
# rate rather than silently under-counting spend.
_DEFAULT_PRICING = MODEL_PRICING_USD_PER_MTOK["claude-opus-4-8"]


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    input_price, output_price = MODEL_PRICING_USD_PER_MTOK.get(model, _DEFAULT_PRICING)
    return (input_tokens / 1_000_000) * input_price + (output_tokens / 1_000_000) * output_price


def record_usage_cost(db: Session, cost_usd: float, input_tokens: int = 0, output_tokens: int = 0) -> None:
    state = risk_manager.get_state(db)
    month_key = date.today().strftime("%Y-%m")
    if state.claude_budget_month_key != month_key:
        # New month -> reset the dollar AND token meters together so both always
        # describe the same window.
        state.claude_budget_month_key = month_key
        state.claude_spend_usd_this_month = 0.0
        state.claude_input_tokens_this_month = 0
        state.claude_output_tokens_this_month = 0
    state.claude_spend_usd_this_month += cost_usd
    state.claude_input_tokens_this_month += int(input_tokens)
    state.claude_output_tokens_this_month += int(output_tokens)
    # Never resets (unlike the monthly counter above) -- feeds the "net wynik"
    # figure, which compares against realized P&L since account inception.
    state.claude_spend_usd_lifetime += cost_usd
    db.commit()


def get_budget_status(db: Session, settings: Settings) -> dict:
    state = risk_manager.get_state(db)
    today_month = date.today().strftime("%Y-%m")
    is_current = state.claude_budget_month_key == today_month
    spent = state.claude_spend_usd_this_month if is_current else 0.0
    # Tokens live in the same monthly window as spend; a stale month reads zero.
    in_tokens = state.claude_input_tokens_this_month if is_current else 0
    out_tokens = state.claude_output_tokens_this_month if is_current else 0
    budget = settings.claude_monthly_budget_usd
    pct_used = (spent / budget * 100) if budget > 0 else 0.0
    return {
        "claude_monthly_budget_usd": budget,
        "claude_spend_usd_this_month": round(spent, 4),
        "claude_budget_pct_used": round(pct_used, 1),
        "claude_budget_alert": pct_used >= settings.claude_budget_alert_threshold_pct,
        # Live token meter for the current month (input + output kept separate so
        # the UI can show throughput and the cache/output split).
        "claude_input_tokens_this_month": in_tokens,
        "claude_output_tokens_this_month": out_tokens,
        "claude_total_tokens_this_month": in_tokens + out_tokens,
    }
