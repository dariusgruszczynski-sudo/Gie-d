import time

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.auth import COOKIE_NAME, SessionAuthMiddleware, create_session_token, verify_session_token
from app.config import Settings

SECRET = "test-secret"


def test_valid_token_verifies():
    token = create_session_token("Darek", SECRET)
    assert verify_session_token(token, SECRET, {"Darek", "Pola"}) == "Darek"


def test_unknown_user_rejected():
    token = create_session_token("Ktos", SECRET)
    assert verify_session_token(token, SECRET, {"Darek"}) is None


def test_tampered_signature_rejected():
    token = create_session_token("Darek", SECRET)
    username, expiry, _sig = token.split(":")
    tampered = f"{username}:{expiry}:0000000000000000000000000000000000000000000000000000000000000000"
    assert verify_session_token(tampered, SECRET, {"Darek"}) is None


def test_wrong_secret_rejected():
    token = create_session_token("Darek", SECRET)
    assert verify_session_token(token, "different-secret", {"Darek"}) is None


def test_expired_token_rejected():
    message_time = int(time.time()) - 10
    # Build an already-expired token by hand (create_session_token always
    # signs a future expiry).
    import hashlib
    import hmac

    signature = hmac.new(SECRET.encode(), f"Darek:{message_time}".encode(), hashlib.sha256).hexdigest()
    token = f"Darek:{message_time}:{signature}"
    assert verify_session_token(token, SECRET, {"Darek"}) is None


def test_missing_token_rejected():
    assert verify_session_token(None, SECRET, {"Darek"}) is None


def test_malformed_token_rejected():
    assert verify_session_token("not-a-valid-token", SECRET, {"Darek"}) is None


def test_dashboard_credentials_parses_multiple_users():
    settings = Settings(dashboard_users="Darek:pass1,Pola:pass2")
    assert settings.dashboard_credentials == {"Darek": "pass1", "Pola": "pass2"}


def test_dashboard_credentials_empty_by_default():
    assert Settings().dashboard_credentials == {}


def _build_test_app(credentials: dict[str, str], secret: str = SECRET, share_token: str = "") -> Starlette:
    async def homepage(request):
        return PlainTextResponse("static shell ok")

    async def api_endpoint(request):
        return PlainTextResponse("api ok")

    async def login_endpoint(request):
        return PlainTextResponse("login ok")

    async def control_endpoint(request):
        return PlainTextResponse("control ok")

    app = Starlette(
        routes=[
            Route("/", homepage),
            Route("/api/status", api_endpoint),
            Route("/api/auth/login", login_endpoint),
            Route("/api/control/pause", control_endpoint, methods=["POST"]),
        ]
    )
    app.add_middleware(
        SessionAuthMiddleware,
        credentials=credentials,
        get_secret=lambda: secret,
        get_share_token=lambda: share_token,
    )
    return app


def test_middleware_fail_closed_when_unconfigured():
    """FAIL-CLOSED: brak zdefiniowanych użytkowników = /api zablokowane (503),
    nie otwarte dla każdego. Na żywej kasie otwarte sterowanie jest niedopuszczalne."""
    client = TestClient(_build_test_app({}))
    resp = client.get("/api/status")
    assert resp.status_code == 503


def test_middleware_fail_closed_blocks_control_when_unconfigured():
    client = TestClient(_build_test_app({}))
    assert client.post("/api/control/pause").status_code == 503


def test_middleware_fail_closed_still_serves_static_shell():
    """Even fail-closed, the static shell must load so the app can render a
    message telling the owner to configure DASHBOARD_USERS."""
    client = TestClient(_build_test_app({}))
    assert client.get("/").status_code == 200


def test_middleware_fail_closed_allows_readonly_share():
    """A configured read-only share link keeps working even with no login users
    -- it's GET-only dashboard data, never control."""
    client = TestClient(_build_test_app({}, share_token="s3cret-share"))
    assert client.get("/api/status?share=s3cret-share").status_code == 200


def test_middleware_blocks_api_without_cookie():
    client = TestClient(_build_test_app({"Darek": "secret"}))
    resp = client.get("/api/status")
    assert resp.status_code == 401


def test_middleware_allows_api_with_valid_cookie():
    client = TestClient(_build_test_app({"Darek": "secret"}))
    token = create_session_token("Darek", SECRET)
    client.cookies.set(COOKIE_NAME, token)
    resp = client.get("/api/status")
    assert resp.status_code == 200


def test_middleware_blocks_api_with_tampered_cookie():
    client = TestClient(_build_test_app({"Darek": "secret"}))
    client.cookies.set(COOKIE_NAME, "Darek:9999999999:deadbeef")
    resp = client.get("/api/status")
    assert resp.status_code == 401


def test_middleware_never_gates_static_shell_even_when_configured():
    """The static frontend (index.html/JS/CSS) must load unauthenticated so
    the custom in-app login screen can render -- otherwise the browser's own
    native Basic Auth popup would fire first, before any React code runs."""
    client = TestClient(_build_test_app({"Darek": "secret"}))
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.text == "static shell ok"


def test_middleware_never_gates_login_endpoint():
    """/api/auth/login must stay reachable without a cookie -- otherwise
    nobody could ever log in in the first place."""
    client = TestClient(_build_test_app({"Darek": "secret"}))
    resp = client.get("/api/auth/login")
    assert resp.status_code == 200


# ---- Read-only share link --------------------------------------------------


def test_share_token_allows_readonly_get():
    client = TestClient(_build_test_app({"Darek": "secret"}, share_token="s3cret-share"))
    resp = client.get("/api/status?share=s3cret-share")
    assert resp.status_code == 200
    assert resp.text == "api ok"


def test_share_token_blocks_control_post():
    """A share viewer can watch but never touch -- POST /api/control is blocked
    even with a valid share token."""
    client = TestClient(_build_test_app({"Darek": "secret"}, share_token="s3cret-share"))
    resp = client.post("/api/control/pause?share=s3cret-share")
    assert resp.status_code == 401


def test_wrong_share_token_rejected():
    client = TestClient(_build_test_app({"Darek": "secret"}, share_token="s3cret-share"))
    assert client.get("/api/status?share=nope").status_code == 401


def test_share_disabled_when_no_token_configured():
    client = TestClient(_build_test_app({"Darek": "secret"}, share_token=""))
    assert client.get("/api/status?share=anything").status_code == 401


def test_share_prefix_matching_respects_path_boundary():
    """Zawężenie tokenu RO: link podglądu wpuszcza dokładny prefiks lub jego
    pod-ścieżkę, ale NIE endpoint, który tylko DZIELI prefiks (np. /api/audit-log
    ~ /api/audit) -- gołe startswith by to rozszczelniło."""
    from app.auth import _path_matches_prefix

    prefixes = ("/api/status", "/api/audit")
    assert _path_matches_prefix("/api/status", prefixes) is True
    assert _path_matches_prefix("/api/audit", prefixes) is True
    assert _path_matches_prefix("/api/status/detail", prefixes) is True
    # Współdzielą tylko prefiks tekstowy -> muszą zostać ODRZUCONE.
    assert _path_matches_prefix("/api/audit-log", prefixes) is False
    assert _path_matches_prefix("/api/status-secret", prefixes) is False
