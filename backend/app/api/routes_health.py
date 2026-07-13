from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.config import Settings, get_settings
from app.db import get_db
from app.services import health

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def get_health(settings: Settings = Depends(get_settings)):
    """Run every health probe and return the traffic-light board. Probes make
    external calls (broker, news), so run off the event loop -- each probe opens
    its own db session internally, so no request-scoped session is needed here."""
    return await run_in_threadpool(health.run_health_checks, None, settings)


class ResetRequest(BaseModel):
    action: str


@router.post("/reset")
def reset(req: ResetRequest, db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Trigger one named reset (resume engine, clear halt, restart scheduler,
    zero the Claude budget meter, refresh snapshots). Auth-gated (never reachable
    by a read-only share viewer). Returns a short human-readable result."""
    try:
        return health.run_reset(req.action, db, settings)
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Nieznana akcja resetu: {req.action}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}")
