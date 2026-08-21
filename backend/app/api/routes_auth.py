import logging
import secrets
import threading
import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import COOKIE_NAME, SESSION_TTL_SECONDS, create_session_token
from app.config import Settings, get_settings
from app.db import get_db
from app.services import audit, push_notifier
from app.session_secret import get_session_secret

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# --- Wykrywanie prób włamania (nieautoryzowany dostęp) ----------------------
# Prosty licznik nieudanych logowań per-IP w oknie czasowym. Gdy w krótkim
# czasie posypie się seria błędnych haseł, wysyłamy JEDEN alarm push (potem
# cisza aż do cooldownu), żeby właściciel wiedział, że ktoś próbuje wejść do
# sterowania botem. In-memory (resetuje się przy restarcie) -- to sygnał
# bezpieczeństwa, nie księgowość; trwały ślad i tak ląduje w audit_log.
_FAIL_WINDOW_S = 15 * 60
_ALARM_COOLDOWN_S = 30 * 60
_fail_lock = threading.Lock()
_fail_times: dict[str, list[float]] = {}
_last_alarm_at: dict[str, float] = {}


def _record_failure(ip: str, threshold: int) -> int:
    """Dopisz nieudaną próbę i zwróć liczbę prób w oknie. Czyści stare wpisy."""
    now = time.time()
    with _fail_lock:
        times = [t for t in _fail_times.get(ip, []) if now - t <= _FAIL_WINDOW_S]
        times.append(now)
        _fail_times[ip] = times
        # Sprzątanie innych IP, żeby słownik nie puchł w nieskończoność.
        for other in list(_fail_times.keys()):
            if other != ip and not any(now - t <= _FAIL_WINDOW_S for t in _fail_times[other]):
                _fail_times.pop(other, None)
        return len(times)


def _should_alarm(ip: str) -> bool:
    now = time.time()
    with _fail_lock:
        if now - _last_alarm_at.get(ip, 0.0) < _ALARM_COOLDOWN_S:
            return False
        _last_alarm_at[ip] = now
        return True


def _clear_failures(ip: str) -> None:
    with _fail_lock:
        _fail_times.pop(ip, None)


def _is_https(request: Request) -> bool:
    """Czy klient przyszedł po HTTPS -- także zza reverse-proxy (Caddy kończy TLS
    i przekazuje X-Forwarded-Proto). Steruje flagą Secure na ciasteczku sesji:
    w prod (HTTPS) ciasteczko jest Secure, w lokalnym dev po http nadal działa."""
    proto = request.headers.get("x-forwarded-proto", "")
    if proto:
        return proto.split(",")[0].strip() == "https"
    return request.url.scheme == "https"


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    ip = audit.client_ip(request)
    expected = settings.dashboard_credentials.get(req.username)
    if expected is None or not secrets.compare_digest(req.password, expected):
        count = _record_failure(ip, settings.security_alert_failed_logins)
        audit.record(db, "login-fail", detail=f"user={req.username[:32]} próba #{count}", request=request, outcome="error")
        # Próg przekroczony -> jeden alarm push (z cooldownem), żeby nie spamować.
        if settings.security_alert_enabled and count >= settings.security_alert_failed_logins and _should_alarm(ip):
            try:
                push_notifier.send_alarm(
                    db, settings,
                    title="🔐 Nieudane logowania do panelu",
                    body=f"{count} błędnych prób z {ip or 'nieznanego IP'} w ostatnich 15 min. Jeśli to nie Ty — sprawdź.",
                    tag="security-login",
                )
            except Exception:  # pragma: no cover - alarm nie może wywalić logowania
                logger.warning("Alarm o nieudanych logowaniach nie poszedł", exc_info=True)
        raise HTTPException(status_code=401, detail="Nieprawidłowy login lub hasło")

    _clear_failures(ip)
    token = create_session_token(req.username, get_session_secret())
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        secure=_is_https(request),
        max_age=SESSION_TTL_SECONDS,
    )
    audit.record(db, "login", detail=f"user={req.username[:32]}", request=request)
    return {"message": "Zalogowano"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Wylogowano"}
