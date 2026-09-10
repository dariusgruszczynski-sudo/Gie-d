"""OPUS KONTROLER (P1/P2) — codzienny strateg z pełną władzą nad mechaniką.

Raz dziennie (po sesji) Opus (claude_model) przegląda wynik + własną bazę wiedzy
i USTAWIA knoby strategii wg uznania dla maksymalizacji zysku: próg pewności,
progresję, sizing, stopy/TP, limity. Zmiany trafiają do trwałego override-store
(knob_overrides_json), nakładanego na effective settings w KAŻDYM cyklu handlu.

Filozofia (decyzja właściciela): Opus ma pełną swobodę WARTOŚCI. Klamry poniżej
to WYŁĄCZNIE bezpieczniki anty-bug (żeby zhalucynowane 9999 albo wartość ujemna
nie wyzerowały konta) — nie są ograniczeniem strategii; zakresy są szerokie.
Właściciel zachowuje wyłącznik (opus_controller_enabled) i sekrety są poza
zasięgiem. Kontroler jest best-effort: NIGDY nie wywraca ścieżki handlu.

Uczy się: destyluje wnioski do opus_knowledge_json (akumulowana baza „co umie"),
która wraca do promptu kontrolera co dzień — pamięć, która przeżywa pojedynczy
cykl.
"""

import json
import logging
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.config import Settings
from app.services import risk_manager, scorecard

logger = logging.getLogger(__name__)

# Knoby, którymi Opus może sterować, z klamrami ANTY-BUG (min, max, czy int).
# Zakresy celowo szerokie — to zabezpieczenie przed absurdem, nie strategia.
ALLOWED_KNOBS: dict[str, tuple[float, float, bool]] = {
    "min_buy_confidence": (0.30, 0.85, False),
    "progressive_confidence_step": (0.0, 0.08, False),
    "progressive_confidence_cap": (0.55, 0.98, False),
    "max_new_positions_per_day": (1, 24, True),
    "max_concurrent_positions": (2, 24, True),
    "min_hold_minutes": (0, 10080, True),
    "min_hold_profit_bypass_pct": (0.5, 15.0, False),
    "hard_take_profit_pct": (2.0, 25.0, False),
    "stop_loss_min_pct": (1.0, 10.0, False),
    "stop_loss_max_pct": (2.0, 20.0, False),
    "trailing_stop_frac": (0.1, 0.97, False),
    "risk_per_trade_pct": (0.5, 6.0, False),
    "conviction_size_max_mult": (1.0, 3.0, False),
    "conviction_max_risk_per_trade_pct": (1.0, 8.0, False),
    "price_move_trigger_pct": (1.0, 10.0, False),
    "reward_risk_ratio": (1.0, 6.0, False),
}
MAX_KNOWLEDGE = 200  # baza wiedzy akumuluje się długo; górny limit tylko p-ko rozpełzaniu


def _clamp(name: str, raw) -> float | int | None:
    spec = ALLOWED_KNOBS.get(name)
    if spec is None:
        return None
    lo, hi, is_int = spec
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return None
    if val != val:  # NaN
        return None
    val = max(lo, min(hi, val))
    return int(round(val)) if is_int else round(val, 4)


def get_overrides(db: Session) -> dict:
    try:
        data = json.loads(risk_manager.get_state(db).knob_overrides_json or "{}")
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError):
        return {}


def _enforce_coherence(s: Settings) -> Settings:
    """Wymuś spójność MIĘDZY knobami (klamry są per-knob, więc Opus mógłby ustawić
    sprzeczną parę, np. stop_min > stop_max → silnik przypina stop do stop_min).
    Podnosimy „górną" wartość do „dolnej", żeby niezmiennik min<=max trzymał."""
    fix: dict = {}
    if s.stop_loss_max_pct < s.stop_loss_min_pct:
        fix["stop_loss_max_pct"] = s.stop_loss_min_pct
    if s.progressive_confidence_cap < s.min_buy_confidence:
        fix["progressive_confidence_cap"] = s.min_buy_confidence
    if s.conviction_max_risk_per_trade_pct < s.risk_per_trade_pct:
        fix["conviction_max_risk_per_trade_pct"] = s.risk_per_trade_pct
    return s.model_copy(update=fix) if fix else s


def apply_knob_overrides(db: Session, settings: Settings) -> Settings:
    """Nałóż knoby ustawione przez Opusa na effective settings. Wywoływane na
    starcie KAŻDEGO cyklu handlu. Odporne: zły JSON / nieznany knob / zły typ są
    pomijane, wartości klamrowane, a para knobów doprowadzona do spójności —
    nigdy nie ustawi absurdu ani sprzecznej konfiguracji ryzyka."""
    overrides = get_overrides(db)
    if not overrides:
        return settings
    update: dict = {}
    for name, raw in overrides.items():
        val = _clamp(name, raw)
        if val is not None and hasattr(settings, name):
            update[name] = val
    if not update:
        return settings
    return _enforce_coherence(settings.model_copy(update=update))


def set_overrides(db: Session, changes: dict, source: str = "opus") -> dict:
    """Zapisz/scal knoby (tylko dozwolone, klamrowane). Zwraca zastosowane."""
    if not isinstance(changes, dict):
        return {}
    current = get_overrides(db)
    applied: dict = {}
    for name, raw in changes.items():
        val = _clamp(name, raw)
        if val is not None:
            current[name] = val
            applied[name] = val
    state = risk_manager.get_state(db)
    state.knob_overrides_json = json.dumps(current)
    risk_manager._log_event(db, "opus-knobs", f"{source}: {json.dumps(applied)}")
    db.commit()
    return applied


def clear_overrides(db: Session) -> None:
    state = risk_manager.get_state(db)
    state.knob_overrides_json = "{}"
    risk_manager._log_event(db, "opus-knobs", "clear")
    db.commit()


def get_knowledge(db: Session) -> list[str]:
    try:
        data = json.loads(risk_manager.get_state(db).opus_knowledge_json or "[]")
        return [str(x) for x in data] if isinstance(data, list) else []
    except (TypeError, ValueError):
        return []


def add_knowledge(db: Session, lessons: list[str]) -> None:
    lessons = [str(x).strip() for x in (lessons or []) if str(x).strip()]
    if not lessons:
        return
    kb = get_knowledge(db)
    kb.extend(lessons)
    kb = kb[-MAX_KNOWLEDGE:]
    state = risk_manager.get_state(db)
    state.opus_knowledge_json = json.dumps(kb, ensure_ascii=False)
    db.commit()


def seed_enabled_from_env(db: Session, settings: Settings) -> None:
    """Przy starcie: env OPUS_CONTROLLER_ENABLED=true WŁĄCZA kontroler — ale tylko
    dopóki właściciel nie przełączył go ręcznie (user_set). Dzięki temu deploy
    włącza go raz, a późniejszy kill-switch właściciela przeżywa restarty."""
    state = risk_manager.get_state(db)
    if (
        getattr(settings, "opus_controller_enabled", False)
        and not state.opus_controller_user_set
        and not state.opus_controller_enabled
    ):
        state.opus_controller_enabled = True
        db.commit()
        logger.info("Opus controller ENABLED from env seed (no manual override set).")


def _default_generate(settings: Settings, prompt: str) -> str:
    """Jedno wywołanie MOCNEGO modelu (Opus = settings.claude_model). Best-effort;
    wstrzykiwalne w testach, więc tu żywy klient."""
    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.claude_model,
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(getattr(b, "text", "") for b in resp.content)


def _build_prompt(db: Session, settings: Settings) -> str:
    realized = scorecard.total_realized_pnl(db)
    knobs = {k: getattr(settings, k, None) for k in ALLOWED_KNOBS}
    kb = get_knowledge(db)
    kb_txt = "\n".join(f"- {x}" for x in kb[-40:]) or "(pusta)"
    return (
        "Jesteś strategiem-kontrolerem bota giełdowego GielDarek (dzienny swing, "
        "akcje US, Alpaca). Masz PEŁNĄ władzę ustawić poniższe knoby dla "
        "maksymalizacji zysku skorygowanego o ryzyko. Zwróć WYŁĄCZNIE JSON:\n"
        '{"knobs": {<nazwa>: <wartość>, ...}, "lessons": ["krótki wniosek", ...]}\n'
        "Zmieniaj tylko to, co chcesz zmienić. Wnioski (lessons) to trwała baza "
        "wiedzy — dopisz, czego się nauczyłeś o tym, co działa.\n\n"
        f"Zrealizowany P&L (życiowo): ${realized}\n"
        f"Aktualne knoby: {json.dumps(knobs)}\n"
        f"Dozwolone zakresy (bezpieczniki): {json.dumps({k: [v[0], v[1]] for k, v in ALLOWED_KNOBS.items()})}\n"
        f"Twoja dotychczasowa baza wiedzy:\n{kb_txt}\n"
    )


def _parse_response(text: str) -> dict:
    """Wyłuskaj JSON z odpowiedzi modelu (odporne na otoczkę tekstem)."""
    if not text:
        return {}
    s = text.find("{")
    e = text.rfind("}")
    if s == -1 or e == -1 or e <= s:
        return {}
    try:
        data = json.loads(text[s : e + 1])
        return data if isinstance(data, dict) else {}
    except (TypeError, ValueError):
        return {}


def run_opus_controller(db: Session, settings: Settings, generate=None) -> dict:
    """Codzienny przebieg kontrolera. Best-effort, throttlowany do raz/dzień,
    pomijany gdy wyłączony lub gdy konto w halcie (nie stroimy podczas awarii).
    Zwraca podsumowanie {ran, applied, lessons_added, reason}."""
    state = risk_manager.get_state(db)
    if not state.opus_controller_enabled:
        return {"ran": False, "reason": "disabled"}
    if getattr(state, "is_halted", False):
        return {"ran": False, "reason": "halted"}
    today = date.today().isoformat()
    if state.opus_controller_last_run == today:
        return {"ran": False, "reason": "already_ran_today"}
    try:
        prompt = _build_prompt(db, settings)
        text = (generate or _default_generate)(settings, prompt)
        data = _parse_response(text)
        applied = set_overrides(db, data.get("knobs", {}), source="opus-daily")
        lessons = data.get("lessons", [])
        add_knowledge(db, lessons if isinstance(lessons, list) else [])
        # stamp last-run dopiero po udanym przebiegu
        state = risk_manager.get_state(db)
        state.opus_controller_last_run = today
        db.commit()
        logger.info("Opus controller: applied=%s lessons=%d", applied, len(lessons) if isinstance(lessons, list) else 0)
        return {
            "ran": True,
            "applied": applied,
            "lessons_added": len(lessons) if isinstance(lessons, list) else 0,
            "at": datetime.now(UTC).isoformat(),
        }
    except Exception as exc:  # pragma: no cover - never break anything
        logger.warning("Opus controller failed: %s", exc, exc_info=True)
        return {"ran": False, "reason": f"error: {exc}"}
