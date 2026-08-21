"""Cookie-based session gate for the API. A no-op when Settings.dashboard_users
is empty, so deployments that don't set it keep working exactly as before.

Deliberately NOT HTTP Basic Auth: browsers intercept 401 + WWW-Authenticate
responses to fetch()/XHR at the network layer to show their own native
credential prompt -- even for background API calls, not just page loads --
which hangs forever in a headless/scripted context and would still likely
surface an unwanted native dialog in a real browser, defeating a custom
login screen entirely. A signed session cookie set by POST /api/auth/login
avoids that mechanism completely: no WWW-Authenticate header is ever sent.

Only /api/* is gated -- NOT the static frontend shell (index.html/JS/CSS),
so the page can always load and render the custom login screen. /api/auth/login
itself is also exempt, since it must be reachable before a session exists."""

import hashlib
import hmac
import time

from starlette.responses import Response

COOKIE_NAME = "gie_d_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 1 week

_EXEMPT_PATHS = {"/api/auth/login"}

# Read-only share link: a request carrying a valid ?share=<token> may GET only
# these dashboard endpoints (no controls, no auth, no trading). Everything else
# -- every POST, /api/control/*, /api/push/*, /api/auth/* -- stays blocked, so a
# shared link can watch but never touch.
_SHARE_READONLY_PREFIXES = (
    "/api/status",
    "/api/portfolio",
    "/api/trades",
    "/api/decisions",
    "/api/events",
    "/api/claude-edge",
    "/api/widget",
    "/api/position-plans",
    "/api/history",
    "/api/audit",
)


def _extract_query_param(query_string: bytes, name: str) -> str | None:
    from urllib.parse import parse_qs

    values = parse_qs(query_string.decode("latin-1")).get(name)
    return values[0] if values else None


def _sign(username: str, expiry: int, secret: str) -> str:
    message = f"{username}:{expiry}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def create_session_token(username: str, secret: str) -> str:
    expiry = int(time.time()) + SESSION_TTL_SECONDS
    signature = _sign(username, expiry, secret)
    return f"{username}:{expiry}:{signature}"


def verify_session_token(token: str | None, secret: str, valid_usernames: set[str]) -> str | None:
    if not token:
        return None
    parts = token.split(":")
    if len(parts) != 3:
        return None
    username, expiry_str, signature = parts
    if username not in valid_usernames:
        return None
    try:
        expiry = int(expiry_str)
    except ValueError:
        return None
    if expiry < time.time():
        return None
    expected_signature = _sign(username, expiry, secret)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    return username


def _extract_cookie(cookie_header: str, name: str) -> str | None:
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(f"{name}="):
            return part[len(name) + 1 :]
    return None


def _path_matches_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    """Zaostrzone dopasowanie: token RO wpuszcza TYLKO ścieżkę dokładnie równą
    prefiksowi albo jego pod-ścieżkę (prefix + "/"). Gołe `startswith` wpuściłoby
    też przyszły endpoint, który przypadkiem DZIELI prefiks (np. /api/audit-log
    ~ /api/audit), rozszczelniając link podglądu -- ta granica temu zapobiega."""
    return any(path == p or path.startswith(p + "/") for p in prefixes)


class SessionAuthMiddleware:
    def __init__(self, app, credentials: dict[str, str], get_secret, get_share_token=None):
        self.app = app
        self.credentials = credentials
        self.get_secret = get_secret
        # Callable returning the current read-only share token ("" = disabled).
        self.get_share_token = get_share_token or (lambda: "")

    def _share_ok(self, scope, path: str) -> bool:
        """Read-only share link: valid token + GET + an allowed dashboard path."""
        share_token = self.get_share_token()
        if not share_token:
            return False
        provided = _extract_query_param(scope.get("query_string", b""), "share")
        return bool(
            provided
            and hmac.compare_digest(provided, share_token)
            and scope.get("method", "GET") == "GET"
            and _path_matches_prefix(path, _SHARE_READONLY_PREFIXES)
        )

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        exempt = not path.startswith("/api") or path in _EXEMPT_PATHS
        if scope["type"] != "http" or exempt:
            await self.app(scope, receive, send)
            return

        # FAIL-CLOSED (żywa kasa): gdy NIE ustawiono żadnego użytkownika panelu
        # (DASHBOARD_USERS puste), sterowanie botem stałoby otworem dla każdego,
        # kto zna adres -- na realnych środkach to niedopuszczalne. Zamiast po
        # cichu ufać każdemu (dawne zachowanie "brak loginu = brak bramki"),
        # blokujemy wszystko poza czytelnym linkiem RO i zwracamy 503 z jasną
        # diagnozą, żeby błędna/pusta konfiguracja była WIDOCZNA, nie ukryta.
        if not self.credentials:
            if self._share_ok(scope, path):
                await self.app(scope, receive, send)
                return
            response = Response(
                status_code=503,
                content='{"detail":"Panel niezabezpieczony: ustaw DASHBOARD_USERS (login:hasło) w .env i zrestartuj. Sterowanie zablokowane do czasu konfiguracji."}',
                media_type="application/json",
            )
            await response(scope, receive, send)
            return

        headers = dict(scope["headers"])
        cookie_header = headers.get(b"cookie", b"").decode("latin-1")
        token = _extract_cookie(cookie_header, COOKIE_NAME)
        username = verify_session_token(token, self.get_secret(), set(self.credentials.keys()))
        if username is not None:
            await self.app(scope, receive, send)
            return

        if self._share_ok(scope, path):
            await self.app(scope, receive, send)
            return

        response = Response(
            status_code=401,
            content='{"detail":"Wymagane logowanie"}',
            media_type="application/json",
        )
        await response(scope, receive, send)
