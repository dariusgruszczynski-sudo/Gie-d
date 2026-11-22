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
    s = settings or get_settings()
    applied = False
    key = (state.alpaca_api_key_override or "").strip()
    secret = (state.alpaca_api_secret_override or "").strip()
    if key and secret:
        s.alpaca_api_key = key
        s.alpaca_api_secret = secret
        s.alpaca_paper = True  # override z panelu dotyczy fazy paper
        logger.info("Alpaca: użyto kluczy z panelu (override) — konto przełączone (paper).")
        applied = True
    # Kraken (noga krypto) — ten sam mechanizm, niezależnie od Alpaki.
    kkey = (getattr(state, "kraken_api_key_override", "") or "").strip()
    ksecret = (getattr(state, "kraken_api_secret_override", "") or "").strip()
    if kkey and ksecret:
        s.kraken_api_key = kkey
        s.kraken_api_secret = ksecret
        logger.info("Kraken: użyto kluczy z panelu (override) — noga krypto gotowa na Kraken.")
        applied = True
    # Przełącznik live/paper z panelu (runtime, bez deployu). "" = config.
    live_ovr = (getattr(state, "crypto_kraken_live_override", "") or "").strip()
    if live_ovr in ("0", "1"):
        s.crypto_kraken_live = (live_ovr == "1")
        logger.info("Kraken: tryb z panelu (override) = %s", "LIVE" if live_ovr == "1" else "paper")
        applied = True
    return applied


def set_kraken_live(db: Session, live: bool) -> None:
    """Ustaw tryb live/paper nogi Kraken RUNTIME z panelu (bez deployu). Zapis do DB
    + nałożenie na singleton od zaraz (następny cykl użyje nowego trybu)."""
    state = _get_state(db)
    if state is None:
        state = SystemState(id=1)
        db.add(state)
    state.crypto_kraken_live_override = "1" if live else "0"
    db.commit()
    apply_override(db)


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


def set_kraken_override(db: Session, api_key: str, api_secret: str) -> None:
    """Zapisz override kluczy Kraken do DB i nałóż na singleton od zaraz. NIE loguje
    sekretu. Następny cykl krypto użyje Krakena bez restartu i bez dostępu do serwera."""
    state = _get_state(db)
    if state is None:
        state = SystemState(id=1)
        db.add(state)
    state.kraken_api_key_override = api_key.strip()
    state.kraken_api_secret_override = api_secret.strip()
    db.commit()
    apply_override(db)
