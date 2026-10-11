"""Weekly self-review: Claude reads its own week of trades + scorecard and
distills a handful of durable lessons ("MSTR breakouts kept stopping out",
"GLD entries worked when VIX was rising"). Lessons persist in SystemState and
are fed back into every future decision's context -- memory that outlives the
15-trade recent-history window. Deliberately cheap: one fast-model call a
week, plain text, budget-tracked like any other Claude usage."""

import json
import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

import anthropic
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Trade
from app.services import budget_tracker, risk_manager, scorecard

logger = logging.getLogger(__name__)

# Zwiększone 10 -> 30: Claude ma BUDOWAĆ bazę zachowań, więc nauczone lekcje
# akumulują się dłużej (obok stałego playbooka), zamiast szybko rotować.
MAX_LESSONS_KEPT = 30
MAX_TRADES_REVIEWED = 40
REVIEW_MAX_TOKENS = 600


def get_lessons(db: Session) -> list[dict]:
    state = risk_manager.get_state(db)
    try:
        lessons = json.loads(state.lessons_json or "[]")
        return lessons if isinstance(lessons, list) else []
    except json.JSONDecodeError:
        return []


def _default_generate(settings: Settings, prompt: str) -> tuple[str, float, int, int]:
    """One plain-text fast-model call; returns (text, cost_usd, in_tokens,
    out_tokens). The token counts are the REAL usage from the response so the
    live token meter reflects ALL Claude usage, self-review included."""
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.claude_model_fast,
        max_tokens=REVIEW_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    in_tok, out_tok = response.usage.input_tokens, response.usage.output_tokens
    cost = budget_tracker.estimate_cost_usd(settings.claude_model_fast, in_tok, out_tok)
    return text, cost, in_tok, out_tok


def _parse_lessons(text: str) -> list[str]:
    lessons = []
    for line in text.splitlines():
        cleaned = line.strip().lstrip("-*•0123456789. ").strip()
        if len(cleaned) >= 15:  # skip headers/blank filler
            lessons.append(cleaned)
    return lessons


def _market_ctx_tag(t: Trade) -> str:
    """Kompaktowy opis WARUNKÓW RYNKU w chwili decyzji (Fear&Greed, funding BTC,
    long/short, zmiana OI 24h) -- te liczby zapisujemy w
    decision.market_context_snapshot przy KAŻDEJ decyzji (też mechanicznej).

    Dzięki temu self-review widzi NIE tylko „co kupiłem", ale „przy jakich
    warunkach" -- więc lekcje mogą być PRZYCZYNOWE ('wejścia przy F&G>60 i
    dodatnim fundingu zawracały'), a nie tylko 'unikaj DOGE'. To największa
    dźwignia nauki: surowiec był logowany, ale destylacja go ignorowała.
    Pusto, gdy brak kontekstu (noga akcji / stary wpis / nieparsowalne)."""
    dec = t.decision
    raw = getattr(dec, "market_context_snapshot", None) if dec else None
    if not raw:
        return ""
    try:
        ctx = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return ""
    if not isinstance(ctx, dict) or not ctx:
        return ""
    bits: list[str] = []
    fng = ctx.get("fear_greed")
    if fng is not None:
        bits.append(f"F&G {fng}")
    funding = ctx.get("btc_funding_rate_pct")
    if funding is not None:
        bits.append(f"funding {funding:+.3f}%")
    ls = ctx.get("btc_long_short_ratio")
    if ls is not None:
        bits.append(f"L/S {ls:.2f}")
    oi = ctx.get("btc_open_interest_change_24h_pct")
    if oi is not None:
        bits.append(f"OI24h {oi:+.2f}%")
    return (" [" + ", ".join(bits) + "]") if bits else ""


def run_self_review(
    db: Session,
    settings: Settings,
    generate: Callable[[Settings, str], tuple[str, float, int, int]] | None = None,
) -> list[dict]:
    """Runs the weekly review and returns the updated lessons list. Never
    raises -- a failed review just leaves the previous lessons in place."""
    state = risk_manager.get_state(db)
    # Przegląd dotyczy NOGI GŁÓWNEJ (krypto po przełączeniu), żeby lekcje były o
    # tym, czym realnie handlujemy -- a nie mieszały zaszłości z ery akcji.
    venue = "crypto" if settings.crypto_enabled else "alpaca"
    market_label = "krypto (24/7, pary USD)" if venue == "crypto" else "akcje/ETF (sesja US)"
    since = datetime.now(UTC) - timedelta(days=7)
    trades = list(
        db.execute(
            select(Trade)
            .where(Trade.timestamp >= since, Trade.venue == venue)
            .order_by(Trade.timestamp.desc())
            .limit(MAX_TRADES_REVIEWED)
        ).scalars()
    )
    if not trades:
        logger.info("Self-review skipped: no %s trades in the last 7 days", venue)
        return get_lessons(db)

    trade_lines = "\n".join(
        f"- {t.timestamp.strftime('%d.%m %H:%M')} {t.side} {t.symbol} @ {t.price:.2f} "
        f"(${t.usdt_value:.2f}){_market_ctx_tag(t)}"
        f"{' | ' + t.decision.reasoning[:120] if t.decision and t.decision.reasoning else ''}"
        for t in reversed(trades)
    )
    # Scorecard nogi głównej (krypto -> trafność/realized z transakcji krypto),
    # bez live cen i tak daje zrealizowany P&L i win-rate.
    card = scorecard.compute_scorecard(db, settings, {"total_value_usdt": 0.0, "prices": {}}, venue=venue)
    previous = get_lessons(db)
    previous_txt = "\n".join(f"- {l.get('lesson', '')}" for l in previous) or "(brak)"

    prompt = (
        "Jesteś traderem robiącym cotygodniowy przegląd własnych transakcji "
        f"na rynku: {market_label}. "
        "Poniżej Twoje transakcje z ostatnich 7 dni, wynik (zrealizowany P&L, trafność) "
        "i Twoje dotychczasowe lekcje.\n\n"
        f"TRANSAKCJE:\n{trade_lines}\n\n"
        f"WYNIK: zrealizowany P&L ${card['realized_pnl_usd']:.2f}, "
        f"trafność {card['win_rate_pct'] if card['win_rate_pct'] is not None else '—'}% "
        f"({card['wins']}W/{card['losses']}L)\n\n"
        f"DOTYCHCZASOWE LEKCJE:\n{previous_txt}\n\n"
        "Przy transakcjach w nawiasie [...] masz WARUNKI RYNKU w chwili decyzji "
        "(Fear&Greed, funding BTC, long/short, zmiana OI 24h). SZUKAJ ZALEŻNOŚCI: "
        "przy jakich warunkach wejścia zarabiały, a przy jakich się sypały "
        "(np. 'longi przy F&G>60 i dodatnim fundingu zawracały', 'churn na bocznym "
        "rynku przy L/S>1,5 zżerał kapitał'). "
        "Napisz 3-5 KONKRETNYCH lekcji na przyszły tydzień -- co działało, czego nie powtarzać, "
        "które tickery/setupy unikać lub preferować i W JAKICH WARUNKACH rynku. "
        "Jedna lekcja = jedna linia zaczynająca się od '- '. "
        "Bez wstępu i podsumowania, tylko lekcje."
    )

    try:
        text, cost, in_tok, out_tok = (generate or _default_generate)(settings, prompt)
        budget_tracker.record_usage_cost(db, cost, in_tok, out_tok)
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
