"""#11 Meta-uczeń LLM: raz na jakiś czas bierze track-rekord bota (krzywa uczenia
+ atrybucja cech → wynik z learning.py) i prosi Claude o uczciwy wniosek: co
działa, co krwawi, JEDNA proponowana zmiana. PROPONUJE — nigdy nie mutuje knobów
(to dalej decyzja właściciela). Tani (jeden call), chroniony budżetem i progiem
próbki (nie goni szumu). Realny call na prodzie (klucz z env); w testach fake."""

import json
import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config import Settings
from app.services import budget_tracker, learning, risk_manager

logger = logging.getLogger(__name__)


def _build_summary(db: Session, settings: Settings, venue: str) -> dict:
    lc = learning.learning_curve(db, settings, venue=venue)
    # Tylko bramki o sensownej próbce trafiają do LLM (reszta to szum).
    attr = [a for a in lc.get("attribution", []) if a["n"] >= 3]
    return {
        "venue": venue,
        "total_closes": lc["total_closes"],
        "trend": lc["trend"],
        "since": lc["since"],
        "cohorts": lc["cohorts"],
        "attribution": attr,
    }


def run_meta_review(db: Session, settings: Settings, advisor, *, venue: str = "crypto",
                    min_closes: int = 20) -> dict:
    """Uruchamia meta-przegląd. Zwraca wniosek (dict) albo {"skipped": powód}.
    Guardy: za mała próbka (min_closes) i wyczerpany budżet — wtedy pomijamy.
    Zapisuje ostatni wniosek do SystemState.llm_meta_insight_json."""
    summary = _build_summary(db, settings, venue)
    if summary["total_closes"] < min_closes:
        return {"skipped": f"za mała próbka ({summary['total_closes']}/{min_closes}) — nie uczymy się na szumie"}

    # Budżet: jeśli włączona twarda pauza i budżet wyczerpany — nie płać za meta-call.
    if getattr(settings, "claude_pause_trading_at_budget", False):
        bs = budget_tracker.get_budget_status(db, settings)
        if bs["claude_monthly_budget_usd"] > 0 and bs["claude_spend_usd_this_month"] >= bs["claude_monthly_budget_usd"]:
            return {"skipped": "budżet Claude wyczerpany"}

    try:
        insight, cost, in_tok, out_tok = advisor.review_learning(summary)
    except Exception:
        logger.warning("Meta-przegląd LLM nie powiódł się (best-effort)", exc_info=True)
        return {"skipped": "błąd wywołania LLM"}

    budget_tracker.record_usage_cost(db, cost, in_tok, out_tok)
    record = {
        **{k: insight.get(k) for k in ("working", "bleeding", "proposed_change", "rationale", "confidence")},
        "based_on_closes": summary["total_closes"],
        "trend": summary["trend"],
        "at": datetime.now(UTC).isoformat(),
    }
    state = risk_manager.get_state(db)
    state.llm_meta_insight_json = json.dumps(record, ensure_ascii=False)
    db.commit()
    logger.info("Meta-przegłąd LLM: %s", record.get("proposed_change"))
    return record


def latest_insight(db: Session) -> dict | None:
    """Ostatni zapisany wniosek meta-ucznia (do UI / nadzoru). None gdy brak."""
    state = risk_manager.get_state(db)
    try:
        data = json.loads(getattr(state, "llm_meta_insight_json", "") or "{}")
    except (TypeError, ValueError):
        return None
    return data or None
