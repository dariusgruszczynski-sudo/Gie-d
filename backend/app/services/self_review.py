"""Weekly self-review: Claude reads its own week of trades + scorecard and
distills a handful of durable lessons ("MSTR breakouts kept stopping out",
"GLD entries worked when VIX was rising"). Lessons persist in SystemState and
are fed back into every future decision's context -- memory that outlives the
15-trade recent-history window. Deliberately cheap: one fast-model call a
week, plain text, budget-tracked like any other Claude usage."""

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Callable

import anthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Trade
from app.services import budget_tracker, risk_manager, scorecard

logger = logging.getLogger(__name__)

MAX_LESSONS_KEPT = 10
MAX_TRADES_REVIEWED = 40
REVIEW_MAX_TOKENS = 600


def get_lessons(db: Session) -> list[dict]:
    state = risk_manager.get_state(db)
    try:
        lessons = json.loads(state.lessons_json or "[]")
        return lessons if isinstance(lessons, list) else []
    except json.JSONDecodeError:
        return []


def _default_generate(settings: Settings, prompt: str) -> tuple[str, float]:
    """One plain-text fast-model call; returns (text, cost_usd)."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model_fast,
        max_tokens=REVIEW_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    cost = budget_tracker.estimate_cost_usd(
        settings.claude_model_fast, response.usage.input_tokens, response.usage.output_tokens
    )
    return text, cost


def _parse_lessons(text: str) -> list[str]:
    lessons = []
    for line in text.splitlines():
        cleaned = line.strip().lstrip("-*•0123456789. ").strip()
        if len(cleaned) >= 15:  # skip headers/blank filler
            lessons.append(cleaned)
    return lessons


def run_self_review(
    db: Session,
    settings: Settings,
    generate: Callable[[Settings, str], tuple[str, float]] | None = None,
) -> list[dict]:
    """Runs the weekly review and returns the updated lessons list. Never
    raises -- a failed review just leaves the previous lessons in place."""
    state = risk_manager.get_state(db)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    trades = list(
        db.execute(
            select(Trade)
            .where(Trade.timestamp >= since)
            .order_by(Trade.timestamp.desc())
            .limit(MAX_TRADES_REVIEWED)
        ).scalars()
    )
    if not trades:
        logger.info("Self-review skipped: no trades in the last 7 days")
        return get_lessons(db)

    trade_lines = "\n".join(
        f"- {t.timestamp.strftime('%d.%m %H:%M')} {t.side} {t.symbol} @ {t.price:.2f} "
        f"(${t.usdt_value:.2f}){' | ' + t.decision.reasoning[:140] if t.decision and t.decision.reasoning else ''}"
        for t in reversed(trades)
    )
    # Scorecard without live prices still yields realized P&L / win rate.
    card = scorecard.compute_scorecard(db, settings, {"total_value_usdt": 0.0, "prices": {}})
    previous = get_lessons(db)
    previous_txt = "\n".join(f"- {l.get('lesson', '')}" for l in previous) or "(brak)"

    prompt = (
        "Jesteś traderem robiącym cotygodniowy przegląd własnych transakcji. "
        "Poniżej Twoje transakcje z ostatnich 7 dni, wynik (zrealizowany P&L, trafność) "
        "i Twoje dotychczasowe lekcje.\n\n"
        f"TRANSAKCJE:\n{trade_lines}\n\n"
        f"WYNIK: zrealizowany P&L ${card['realized_pnl_usd']:.2f}, "
        f"trafność {card['win_rate_pct'] if card['win_rate_pct'] is not None else '—'}% "
        f"({card['wins']}W/{card['losses']}L)\n\n"
        f"DOTYCHCZASOWE LEKCJE:\n{previous_txt}\n\n"
        "Napisz 3-5 KONKRETNYCH lekcji na przyszły tydzień -- co działało, czego nie powtarzać, "
        "które tickery/setupy unikać lub preferować. Jedna lekcja = jedna linia zaczynająca się od '- '. "
        "Bez wstępu i podsumowania, tylko lekcje."
    )

    try:
        text, cost = (generate or _default_generate)(settings, prompt)
        budget_tracker.record_usage_cost(db, cost)
    except Exception:
        logger.warning("Self-review Claude call failed, keeping previous lessons", exc_info=True)
        return previous

    new_lessons = _parse_lessons(text)
    if not new_lessons:
        logger.warning("Self-review produced no parseable lessons, keeping previous")
        return previous

    today = date.today().isoformat()
    merged = ([{"date": today, "lesson": l} for l in new_lessons] + previous)[:MAX_LESSONS_KEPT]
    state.lessons_json = json.dumps(merged, ensure_ascii=False)
    state.last_self_review_date = today
    db.commit()
    logger.info("Self-review stored %d new lessons", len(new_lessons))
    return merged
