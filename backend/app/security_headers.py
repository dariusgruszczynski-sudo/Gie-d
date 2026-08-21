"""Nagłówki bezpieczeństwa doklejane do KAŻDEJ odpowiedzi HTTP.

- Strict-Transport-Security (HSTS): każe przeglądarce trzymać się HTTPS przez
  rok (Caddy i tak kończy TLS i przekierowuje http->https; HSTS domyka to po
  stronie klienta, żeby żaden przyszły request nie poszedł czystym http). Nad
  http przeglądarki ten nagłówek ignorują, więc jest bezpieczny także w dev.
- X-Content-Type-Options / X-Frame-Options / Referrer-Policy: tanie, standardowe
  utwardzenie (bez sniffowania typów, bez osadzania panelu w obcej ramce,
  ograniczony referrer).

Lekki ASGI-middleware (jak SessionAuthMiddleware) -- opakowuje `send`, żeby
wstrzyknąć nagłówki do startu odpowiedzi, bez narzutu BaseHTTPMiddleware."""

_HEADERS = [
    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"same-origin"),
]


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                present = {k.lower() for k, _ in headers}
                for key, value in _HEADERS:
                    if key not in present:
                        headers.append((key, value))
            await send(message)

        await self.app(scope, receive, send_with_headers)
