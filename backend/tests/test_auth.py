import base64

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.auth import BasicAuthMiddleware, check_basic_auth
from app.config import Settings


def _basic_header(user: str, pw: str) -> str:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return f"Basic {token}"


def test_valid_credentials_pass():
    assert check_basic_auth(_basic_header("Darek", "secret123"), {"Darek": "secret123"}) is True


def test_wrong_password_rejected():
    assert check_basic_auth(_basic_header("Darek", "wrong"), {"Darek": "secret123"}) is False


def test_unknown_user_rejected():
    assert check_basic_auth(_basic_header("Ktos", "secret123"), {"Darek": "secret123"}) is False


def test_missing_header_rejected():
    assert check_basic_auth(None, {"Darek": "secret123"}) is False


def test_malformed_header_rejected():
    assert check_basic_auth("Basic not-valid-base64!!!", {"Darek": "secret123"}) is False


def test_dashboard_credentials_parses_multiple_users():
    settings = Settings(dashboard_users="Darek:pass1,Pola:pass2")
    assert settings.dashboard_credentials == {"Darek": "pass1", "Pola": "pass2"}


def test_dashboard_credentials_empty_by_default():
    assert Settings().dashboard_credentials == {}


def _build_test_app(credentials: dict[str, str]) -> Starlette:
    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(BasicAuthMiddleware, credentials=credentials)
    return app


def test_middleware_allows_all_when_unconfigured():
    client = TestClient(_build_test_app({}))
    assert client.get("/").status_code == 200


def test_middleware_blocks_without_auth_header():
    client = TestClient(_build_test_app({"Darek": "secret"}))
    resp = client.get("/")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_middleware_allows_with_correct_credentials():
    client = TestClient(_build_test_app({"Darek": "secret"}))
    resp = client.get("/", auth=("Darek", "secret"))
    assert resp.status_code == 200


def test_middleware_blocks_wrong_password():
    client = TestClient(_build_test_app({"Darek": "secret"}))
    resp = client.get("/", auth=("Darek", "wrong"))
    assert resp.status_code == 401
