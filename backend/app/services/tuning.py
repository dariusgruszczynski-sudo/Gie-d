"""Runtime-tunable knobs the user can drag on the dashboard WITHOUT a redeploy.

Only a small, safe subset of profit/risk parameters is exposed; everything
else stays fixed in .env. Overrides are persisted in
SystemState.tuning_overrides_json and layered on top of the env-based Settings
by apply_tuning() at the start of every automated cycle (scheduler + the
"Wymuś analizę" button), so a slider change takes effect on the next poll."""

import json
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.config import Settings
from app.services import risk_manager


@dataclass(frozen=True)
class Tunable:
    key: str
    label: str
    min: float
    max: float
    step: float
    is_int: bool = False
    unit: str = ""
    help: str = ""


# The dashboard sliders. Each maps 1:1 to a Settings field of the same name.
TUNABLES: list[Tunable] = [
    Tunable("risk_per_trade_pct", "Ryzyko na transakcję", 0.0, 5.0, 0.25, unit="% konta",
            help="Ile % całego konta może kosztować trafienie stopa. Niżej = ostrożniej, mniejsze pozycje."),
    Tunable("reward_risk_ratio", "Stosunek zysk/ryzyko (R:R)", 0.0, 3.0, 0.1, unit="×",
            help="Cel take-profit = dystans stopa × ta wartość. Wyżej = puszczaj zyski dalej. 0 = sztywny take-profit."),
    Tunable("min_buy_confidence", "Próg pewności BUY", 0.0, 0.9, 0.05,
            help="Poniżej tej pewności automat nie wchodzi. Wyżej = bardziej selektywnie, mniej transakcji."),
    Tunable("max_new_positions_per_day", "Limit wejść / dobę", 0.0, 10.0, 1.0, is_int=True,
            help="Ile nowych pozycji dziennie na portfel. Niżej = mniej churnu. 0 = bez limitu."),
    Tunable("price_move_trigger_pct", "Próg ruchu ceny", 0.5, 5.0, 0.25, unit="%",
            help="O ile musi drgnąć cena od kotwicy, by wywołać (płatną) analizę. Wyżej = rzadziej."),
    Tunable("stop_loss_vol_mult", "Szerokość stopa", 0.0, 10.0, 0.5, unit="× zmienność",
            help="Mnożnik zmienności (ATR) dla stop-lossa. Wyżej = szerszy stop, mniej wytrząsania na szumie. 0 = sztywny %."),
]

_BY_KEY = {t.key: t for t in TUNABLES}


def get_overrides(db: Session) -> dict:
    state = risk_manager.get_state(db)
    try:
        data = json.loads(state.tuning_overrides_json or "{}")
        return {k: v for k, v in data.items() if k in _BY_KEY} if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _clamp(t: Tunable, value) -> float | int:
    value = max(t.min, min(t.max, float(value)))
    return int(round(value)) if t.is_int else round(value, 4)


def set_overrides(db: Session, updates: dict) -> dict:
    """Validate/clamp incoming slider values against each tunable's bounds and
    persist. Unknown keys are ignored (never trust the client blindly)."""
    current = get_overrides(db)
    for key, value in (updates or {}).items():
        t = _BY_KEY.get(key)
        if t is None or value is None:
            continue
        current[key] = _clamp(t, value)
    state = risk_manager.get_state(db)
    state.tuning_overrides_json = json.dumps(current)
    db.commit()
    return current


def apply_tuning(db: Session, settings: Settings) -> Settings:
    """Return a Settings copy with the persisted slider overrides applied. No
    overrides -> the original settings object unchanged."""
    overrides = get_overrides(db)
    if not overrides:
        return settings
    return settings.model_copy(update=overrides)


def effective_values(db: Session, settings: Settings) -> dict:
    """Slider specs plus each knob's current effective value (override if set,
    otherwise the .env default) for the dashboard panel."""
    overrides = get_overrides(db)
    tunables = [
        {
            "key": t.key,
            "label": t.label,
            "min": t.min,
            "max": t.max,
            "step": t.step,
            "is_int": t.is_int,
            "unit": t.unit,
            "help": t.help,
            "value": overrides.get(t.key, getattr(settings, t.key)),
            "default": getattr(settings, t.key),
            "overridden": t.key in overrides,
        }
        for t in TUNABLES
    ]
    return {"tunables": tunables}
