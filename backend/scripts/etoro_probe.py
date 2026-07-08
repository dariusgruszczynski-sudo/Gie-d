"""Read-only probe of the eToro public API to verify credentials and discover
the real request/response shapes before we build the full client against them.

Runs GET requests only -- it never places, cancels or modifies an order, so it
is safe to run against a live key. It figures out which auth-header combo works,
then hits a curated list of candidate endpoints (account/portfolio, instrument
metadata, candles) and prints the status + a snippet of each response.

Usage (on the VPS, where outbound network to eToro is open):

    cd ~/gie-d
    ETORO_API_KEY='<klucz publiczny>' ETORO_USER_KEY='<klucz prywatny>' \
        docker compose exec -T app python scripts/etoro_probe.py

Paste the whole output back so the client can be built against verified shapes.
"""

import json
import os
import sys
import uuid

import httpx

BASE = "https://public-api.etoro.com"
TIMEOUT = 20.0

API_KEY = os.environ.get("ETORO_API_KEY", "").strip()
USER_KEY = os.environ.get("ETORO_USER_KEY", "").strip()

if not API_KEY or not USER_KEY:
    print("BRAK KLUCZY: ustaw ETORO_API_KEY i ETORO_USER_KEY w środowisku.")
    sys.exit(1)


def _headers(api_key: str, user_key: str, bearer: str | None = None) -> dict:
    h = {
        "x-api-key": api_key,
        "x-user-key": user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept": "application/json",
    }
    if bearer:
        h["Authorization"] = f"Bearer {bearer}"
    return h


def _get(path: str, headers: dict) -> tuple[int, str]:
    try:
        resp = httpx.get(f"{BASE}{path}", headers=headers, timeout=TIMEOUT, follow_redirects=True)
    except Exception as exc:  # network/TLS/etc.
        return -1, f"EXC {type(exc).__name__}: {exc}"
    body = resp.text or ""
    try:
        body = json.dumps(resp.json(), ensure_ascii=False)
    except Exception:
        pass
    return resp.status_code, body[:600]


# 1) Find a working auth-header combo against a cheap, documented endpoint.
AUTH_PROBE = "/api/v1/agent-portfolios"
combos = [
    ("x-api-key=API, x-user-key=USER", _headers(API_KEY, USER_KEY)),
    ("swapped (x-api-key=USER, x-user-key=API)", _headers(USER_KEY, API_KEY)),
    ("+ Authorization: Bearer USER", _headers(API_KEY, USER_KEY, bearer=USER_KEY)),
    ("+ Authorization: Bearer API", _headers(API_KEY, USER_KEY, bearer=API_KEY)),
]

print("=" * 70)
print("1) AUTORYZACJA — próba kombinacji nagłówków na", AUTH_PROBE)
print("=" * 70)
working_headers = None
for label, headers in combos:
    code, snippet = _get(AUTH_PROBE, headers)
    ok = code and 200 <= code < 300
    print(f"[{code}] {label}")
    print(f"      {snippet}")
    if ok and working_headers is None:
        working_headers = headers
        print("      ^^ DZIAŁA — używam tej kombinacji do reszty prób")

if working_headers is None:
    print("\nŻadna kombinacja nie dała 2xx. Używam domyślnej (x-api-key=API) do")
    print("dalszych prób, żeby zobaczyć treść błędów (kod + komunikat eToro).")
    working_headers = _headers(API_KEY, USER_KEY)

# 2) Account / portfolio (live + demo) and instrument metadata + candles.
CANDIDATES = [
    "/api/v1/agent-portfolios",
    "/api/v1/user",
    "/api/v1/users/me",
    "/api/v1/trading/info/portfolio",
    "/api/v1/trading/info/demo/portfolio",
    "/api/v2/trading/info/portfolio",
    "/api/v2/trading/info/demo/portfolio",
    "/api/v1/trading/account",
    "/api/v1/trading/demo/account",
    "/api/v1/metadata/instruments",
    "/api/v1/market-data/instruments",
    "/api/v1/instruments",
    "/api/v1/metadata/instruments?symbols=BTC",
    "/api/v1/market-data/candles?symbols=BTC&interval=OneHour",
]

print("\n" + "=" * 70)
print("2) ENDPOINTY — salda / instrumenty / świece (tylko odczyt)")
print("=" * 70)
for path in CANDIDATES:
    # fresh x-request-id per call
    headers = dict(working_headers)
    headers["x-request-id"] = str(uuid.uuid4())
    code, snippet = _get(path, headers)
    print(f"\n[{code}] GET {path}")
    print(f"      {snippet}")

print("\n" + "=" * 70)
print("GOTOWE — wklej całość powyżej z powrotem.")
print("=" * 70)
