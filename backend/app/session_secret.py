"""HMAC key for signing login session cookies. Generated once on first boot
and persisted in SystemState so restarting the app (e.g. via the dashboard's
RESTART button) doesn't invalidate every logged-in session. Cached in memory
after first load so the auth middleware never hits the DB per request."""

import secrets

from app.db import SessionLocal
from app.models import SystemState

_session_secret: str | None = None


def init_session_secret() -> str:
    global _session_secret
    db = SessionLocal()
    try:
        state = db.get(SystemState, 1)
        if state is None:
            state = SystemState(id=1)
            db.add(state)
            db.commit()
            db.refresh(state)
        if not state.session_secret:
            state.session_secret = secrets.token_hex(32)
            db.commit()
        _session_secret = state.session_secret
        return _session_secret
    finally:
        db.close()


def get_session_secret() -> str:
    if _session_secret is None:
        raise RuntimeError("Session secret not initialized -- call init_session_secret() at app startup")
    return _session_secret
