"""Ślad audytowy operacji wrażliwych z panelu (patrz models.AuditLog).

Best-effort: zapis audytu NIGDY nie może wywrócić samej operacji (handlu,
pauzy, restartu) -- łapiemy i logujemy każdy błąd zapisu, a operacja leci dalej.
Nie trzymamy tu żadnych sekretów, tylko czytelny skrót „co się stało"."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)


def client_ip(request) -> str:
    """IP wywołującego, z uwzględnieniem reverse-proxy (Caddy) -- bierzemy
    pierwszy adres z X-Forwarded-For, a w ostateczności bezpośredni peer."""
    try:
        xff = request.headers.get("x-forwarded-for") if request is not None else None
        if xff:
            return xff.split(",")[0].strip()[:64]
        if request is not None and request.client is not None:
            return str(request.client.host)[:64]
    except Exception:  # pragma: no cover - defensywnie
        pass
    return ""


def record(db: Session, action: str, *, detail: str = "", request=None, outcome: str = "ok") -> None:
    """Dopisuje jeden wpis do dziennika. Best-effort -- błąd zapisu nie przerywa
    operacji, którą audytujemy."""
    try:
        db.add(AuditLog(action=action[:32], detail=(detail or "")[:255], client_ip=client_ip(request), outcome=outcome[:16]))
        db.commit()
    except Exception:  # pragma: no cover - audyt nie może wywalić operacji
        logger.warning("Zapis audytu nie powiódł się (%s)", action, exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass


def recent(db: Session, limit: int = 100) -> list[dict]:
    """Ostatnie wpisy audytu (najnowsze pierwsze) dla widoku w panelu."""
    rows = list(db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)).scalars())
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp is not None else None,
            "action": r.action,
            "detail": r.detail,
            "client_ip": r.client_ip,
            "outcome": r.outcome,
        }
        for r in rows
    ]
