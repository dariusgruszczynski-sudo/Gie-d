"""Web Push: klucz publiczny VAPID + zapis/wypis subskrypcji + wysyłka testowa.

Wszystko za tym samym logowaniem co reszta dashboardu (SessionAuthMiddleware),
więc obcy nie zapisze sobie powiadomień. Subskrypcja to obiekt PushSubscription
z przeglądarki (endpoint + klucze p256dh/auth)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.models import PushSubscription
from app.services import push_notifier

router = APIRouter(prefix="/api/push", tags=["push"])


class SubKeys(BaseModel):
    p256dh: str
    auth: str


class SubscribeRequest(BaseModel):
    endpoint: str
    keys: SubKeys


@router.get("/config")
def push_config(settings: Settings = Depends(get_settings)):
    """Frontend czyta z tego klucz publiczny VAPID (potrzebny do subskrypcji) i
    dowiaduje się, czy push jest w ogóle włączony na serwerze."""
    return {
        "enabled": push_notifier.push_configured(settings),
        "vapid_public_key": settings.vapid_public_key if settings.push_enabled else "",
    }


@router.post("/subscribe")
def subscribe(
    req: SubscribeRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if not push_notifier.push_configured(settings):
        raise HTTPException(status_code=503, detail="Push nie jest skonfigurowany na serwerze (brak kluczy VAPID).")

    existing = db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == req.endpoint)
    ).scalar_one_or_none()
    ua = request.headers.get("user-agent", "")[:255]
    if existing:
        existing.p256dh = req.keys.p256dh
        existing.auth = req.keys.auth
        existing.user_agent = ua
    else:
        db.add(
            PushSubscription(
                endpoint=req.endpoint,
                p256dh=req.keys.p256dh,
                auth=req.keys.auth,
                user_agent=ua,
            )
        )
    db.commit()
    return {"message": "Powiadomienia włączone na tym urządzeniu."}


@router.post("/unsubscribe")
def unsubscribe(req: SubscribeRequest, db: Session = Depends(get_db)):
    sub = db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == req.endpoint)
    ).scalar_one_or_none()
    if sub:
        db.delete(sub)
        db.commit()
    return {"message": "Powiadomienia wyłączone na tym urządzeniu."}


@router.post("/test")
def test_push(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    if not push_notifier.push_configured(settings):
        raise HTTPException(status_code=503, detail="Push nie jest skonfigurowany na serwerze.")
    sent = push_notifier.send_to_all(
        db,
        settings,
        title="🔔 GielDarek",
        body="Powiadomienia działają — tu wpadną kupna i sprzedaże.",
        tag="test",
    )
    if sent == 0:
        raise HTTPException(status_code=404, detail="Brak zapisanych urządzeń (najpierw włącz powiadomienia).")
    return {"message": f"Wysłano testowe powiadomienie na {sent} urządzenie/urządzeń."}
