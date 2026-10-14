"""Runtime-owe nadpisanie kluczy Alpaca z panelu („Podłącz konto Alpaca"), bez
dostępu do serwera/env. Klucze trzymane w SystemState (override) i nakładane na
WSPÓŁDZIELONY singleton Settings z get_settings() — wszystkie 14 miejsc budujących
AlpacaClient(settings) czyta ten sam obiekt, więc podmiana przełącza konto od zaraz.

Bezpieczeństwo: to konto PAPER (sztuczny kapitał). Klucze nie są serializowane do
API (serialization._SENSITIVE_COLUMNS) ani logowane."""

import logging

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import SystemState

logger = logging.getLogger(__name__)


def _get_state(db: Session) -> SystemState | None:
    return db.get(SystemState, 1)


def apply_override(db: Session, settings: Settings | None = None) -> bool:
    """Jeśli w DB są override'owe klucze Alpaca, wstaw je do singletonu Settings
    (i wymuś tryb paper). Zwraca True, gdy nadpisano. Wołane na starcie aplikacji
    oraz zaraz po zapisaniu kluczy z panelu."""
    state = _get_state(db)
    if state is None:
        return False
    key = (state.alpaca_api_key_override or "").strip()
    secret = (state.alpaca_api_secret_override or "").strip()
    if not key or not secret:
        return False
    s = settings or get_settings()
    s.alpaca_api_key = key
    s.alpaca_api_secret = secret
    s.alpaca_paper = True  # override z panelu dotyczy fazy paper
    logger.info("Alpaca: użyto kluczy z panelu (override) — konto przełączone (paper).")
    return True


def set_override(db: Session, api_key: str, api_secret: str) -> None:
    """Zapisz override do DB i nałóż na singleton od zaraz. NIE loguje sekretu."""
    state = _get_state(db)
    if state is None:
        state = SystemState(id=1)
        db.add(state)
    state.alpaca_api_key_override = api_key.strip()
    state.alpaca_api_secret_override = api_secret.strip()
    db.commit()
    apply_override(db)
