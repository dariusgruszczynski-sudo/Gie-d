"""HTTP Basic Auth gate for the whole app (dashboard + API). A no-op when
Settings.dashboard_users is empty, so deployments that don't set it keep
working exactly as before -- the dashboard otherwise has no login."""

import base64
import secrets

from starlette.responses import Response


def check_basic_auth(header_value: str | None, credentials: dict[str, str]) -> bool:
    if not header_value or not header_value.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header_value[6:]).decode("utf-8")
    except Exception:
        return False
    username, _, password = decoded.partition(":")
    expected = credentials.get(username)
    return expected is not None and secrets.compare_digest(password, expected)


class BasicAuthMiddleware:
    def __init__(self, app, credentials: dict[str, str]):
        self.app = app
        self.credentials = credentials

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not self.credentials:
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        raw_header = headers.get(b"authorization")
        header_value = raw_header.decode("latin-1") if raw_header else None

        if check_basic_auth(header_value, self.credentials):
            await self.app(scope, receive, send)
            return

        response = Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="Gie-d"'})
        await response(scope, receive, send)
