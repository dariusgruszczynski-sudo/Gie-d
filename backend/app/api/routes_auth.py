import secrets

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel

from app.auth import COOKIE_NAME, SESSION_TTL_SECONDS, create_session_token
from app.config import Settings, get_settings
from app.session_secret import get_session_secret

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest, response: Response, settings: Settings = Depends(get_settings)):
    expected = settings.dashboard_credentials.get(req.username)
    if expected is None or not secrets.compare_digest(req.password, expected):
        raise HTTPException(status_code=401, detail="Nieprawidłowy login lub hasło")

    token = create_session_token(req.username, get_session_secret())
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
    )
    return {"message": "Zalogowano"}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"message": "Wylogowano"}
