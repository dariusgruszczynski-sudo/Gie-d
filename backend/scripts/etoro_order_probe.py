#!/usr/bin/env python3
"""SAFE discovery probe for the correct eToro order endpoint + body schema.

Our live order path (/api/v1/trading/execution/orders) returns 404 RouteNotFound,
so every eToro BUY silently fails. eToro's real order API is v2 and its exact
path/body for THIS token type isn't publicly documented, so this probe finds it
empirically -- WITHOUT placing a real trade.

SAFETY: every candidate is POSTed with a DELIBERATELY INVALID instrument
(999999999) and amount 0, so even if a path + schema is perfectly correct, eToro
rejects it at validation and NOTHING executes. We only read the status code +
error body:
  404 -> route does not exist (wrong path)
  400 / 422 -> route EXISTS; the error body reveals the expected fields
  403 -> route exists but this token lacks permission
Run it, paste the whole output back.

    docker compose exec -T \
      -e ETORO_API_KEY=... -e ETORO_USER_KEY=... \
      app python scripts/etoro_order_probe.py
(or, if the keys are already in .env on the server, just:)
    docker compose exec -T app python scripts/etoro_order_probe.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from app.config import get_settings  # noqa: E402

BASE = "https://public-api.etoro.com"
BAD_INSTRUMENT = 999999999  # guarantees rejection -> no real order can execute

# Candidate order endpoints (v2 first) + a body shape to try against each.
# Two documented body shapes so a validation error reveals which one the route
# wants. Both use the invalid instrument + amount 0.
SHAPE_DOC = {
    "action": "open", "transaction": "buy", "instrumentId": BAD_INSTRUMENT,
    "orderType": "mkt", "leverage": 1, "amount": 0, "orderCurrency": "usd",
}
SHAPE_SIMPLE = {"instrumentId": BAD_INSTRUMENT, "isBuy": True, "amount": 0, "leverage": 1}

CANDIDATES = [
    ("/api/v2/trading/execution/orders", SHAPE_DOC),
    ("/api/v2/trading/execution/orders", SHAPE_SIMPLE),
    ("/api/v2/trading/execution/market-open-orders/by-amount", SHAPE_DOC),
    ("/api/v2/trading/execution/market-open-orders/by-units", SHAPE_DOC),
    ("/api/v2/trading/execution/limit-orders", SHAPE_DOC),
    ("/api/v1/trading/execution/market-open-orders/by-amount", SHAPE_DOC),
    ("/api/v1/trading/execution/orders", SHAPE_SIMPLE),  # current path (baseline 404)
]

# OPEN is confirmed (/api/v2/trading/execution/orders, action=open, transaction=Buy).
# The remaining unknown is CLOSE (our SELL / stop-loss), which on eToro's
# position model needs a positionId, not units. Probe close-route candidates
# with a BOGUS positionId (999999999) -> a route that exists answers "position
# not found" / a validation error (NOT 404 RouteNotFound), and closes NOTHING
# because no such position exists.
BAD_POSITION = 999999999
CLOSE_CANDIDATES = [
    # Same unified endpoint, action=close (mirrors action=open).
    ("POST", "/api/v2/trading/execution/orders",
     {"action": "close", "transaction": "Sell", "positionId": BAD_POSITION, "orderType": "mkt", "amount": 0}),
    ("POST", "/api/v2/trading/execution/close-orders", {"positionId": BAD_POSITION}),
    ("POST", "/api/v2/trading/execution/market-close-orders/by-position", {"positionId": BAD_POSITION}),
    ("POST", "/api/v2/trading/execution/close-position", {"positionId": BAD_POSITION}),
    ("DELETE", f"/api/v2/trading/positions/{BAD_POSITION}", None),
    ("DELETE", f"/api/v2/trading/execution/orders/{BAD_POSITION}", None),
]


def main() -> None:
    s = get_settings()
    if not s.etoro_api_key or not s.etoro_user_key:
        print("BRAK kluczy eToro (ETORO_API_KEY / ETORO_USER_KEY). Przerywam.")
        return
    headers = {
        "x-api-key": s.etoro_api_key,
        "x-user-key": s.etoro_user_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    print("=" * 72)
    print("SAFE PROBE — instrument 999999999 + amount 0 => zlecenie NIE wykona się")
    print("Szukam adresu, który zwraca 400/422/403 (istnieje) zamiast 404 (brak).")
    print("=" * 72)
    with httpx.Client(base_url=BASE, timeout=20.0) as http:
        print("\n--- OTWIERANIE (open) ---")
        for path, body in CANDIDATES:
            h = dict(headers, **{"x-request-id": str(uuid.uuid4())})
            shape = "doc" if "action" in body else "simple"
            try:
                r = http.post(path, headers=h, json=body)
                mark = "  <-- ISTNIEJE" if r.status_code != 404 else ""
                print(f"\n[{r.status_code}] POST {path}  (body={shape}){mark}")
                print(f"      {r.text[:400]}")
            except Exception as e:  # noqa: BLE001
                print(f"\n[ERR] POST {path}  (body={shape}): {type(e).__name__}: {e}")

        print("\n--- ZAMYKANIE (close, positionId={}) ---".format(BAD_POSITION))
        for method, path, body in CLOSE_CANDIDATES:
            h = dict(headers, **{"x-request-id": str(uuid.uuid4())})
            try:
                r = http.request(method, path, headers=h, json=body)
                mark = "  <-- ISTNIEJE" if r.status_code != 404 else ""
                print(f"\n[{r.status_code}] {method} {path}{mark}")
                print(f"      {r.text[:400]}")
            except Exception as e:  # noqa: BLE001
                print(f"\n[ERR] {method} {path}: {type(e).__name__}: {e}")
    print("\n" + "=" * 72)
    print("GOTOWE — wklej całość. Adres z kodem != 404 to nasz endpoint;")
    print("treść błędu (nie 'RouteNotFound') pokaże schemat / że pozycji nie ma.")
    print("=" * 72)


if __name__ == "__main__":
    main()
