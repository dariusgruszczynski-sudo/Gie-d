from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_auth import router
from app.auth import COOKIE_NAME, verify_session_token
from app.config import Settings, get_settings


def _make_client(settings: Settings, secret: str = "test-secret"):
    from app import session_secret

    session_secret._session_secret = secret

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_login_with_correct_credentials_sets_cookie():
    settings = Settings(dashboard_users="Darek:Dareczek123!!!")
    client = _make_client(settings)

    resp = client.post("/api/auth/login", json={"username": "Darek", "password": "Dareczek123!!!"})

    assert resp.status_code == 200
    token = resp.cookies.get(COOKIE_NAME)
    assert token is not None
    assert verify_session_token(token, "test-secret", {"Darek"}) == "Darek"


def test_login_with_wrong_password_rejected():
    settings = Settings(dashboard_users="Darek:Dareczek123!!!")
    client = _make_client(settings)

    resp = client.post("/api/auth/login", json={"username": "Darek", "password": "wrong"})

    assert resp.status_code == 401
    assert resp.cookies.get(COOKIE_NAME) is None


def test_login_with_unknown_user_rejected():
    settings = Settings(dashboard_users="Darek:Dareczek123!!!")
    client = _make_client(settings)

    resp = client.post("/api/auth/login", json={"username": "Ktos", "password": "Dareczek123!!!"})

    assert resp.status_code == 401


def test_logout_clears_cookie():
    settings = Settings(dashboard_users="Darek:Dareczek123!!!")
    client = _make_client(settings)

    resp = client.post("/api/auth/logout")

    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert COOKIE_NAME in set_cookie
