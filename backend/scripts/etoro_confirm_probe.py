#!/usr/bin/env python3
"""Find eToro's ORDER-CONFIRM step -- the missing half of the two-phase order.

The POST /api/v2/trading/execution/orders now returns 200 with a body that is a
dead giveaway:  {"token": "...", "orderId": ..., "referenceId": "..."}.  A token
+ referenceId that never touches the portfolio means the order is only PREPARED;
it needs a second CONFIRM/COMMIT call keyed by that token. GET on the order
resource returns 405 (route exists, wrong method) -- so *some* method confirms.

This script discovers that method deterministically instead of guessing:
  1. OPTIONS both order routes + read the `Allow` header (lists real methods).
  2. Place ONE real $10 order and dump ALL response headers (a Location / next
     header is the REST convention for "confirm here") plus the body.
  3. Using the real token/orderId/referenceId, try the handful of confirm shapes
     the Allow header implies -- AFTER EACH ONE re-read the portfolio and STOP
     the moment a position appears, so at most ONE real fill happens. (eToro
     tokens are typically single-use, so a wrong guess just invalidates.)

⚠️ May open ONE real $10 BTC position if a confirm shape works -- that's the
goal. Close it by hand in the app afterwards. Run:

    docker compose exec -T app python scripts/etoro_confirm_probe.py
"""

import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx  # noqa: E402

from app.config import get_settings  # noqa: E402

BASE = "https://public-api.etoro.com"
ORDERS = "/api/v2/trading/execution/orders"


def _h(s) -> dict:
    return {
        "x-api-key": s.etoro_api_key,
        "x-user-key": s.etoro_user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _positions(http, s) -> int:
    r = http.request("GET", "/api/v1/trading/info/portfolio", headers=_h(s))
    if r.status_code >= 400:
        return -1
    cp = r.json().get("clientPortfolio", {})
    return len(cp.get("positions") or []) + len(cp.get("orders") or []) + len(cp.get("entryOrders") or [])


def _call(http, s, method, path, body=None):
    r = http.request(method, path, headers=_h(s), json=body)
    allow = r.headers.get("allow") or r.headers.get("Allow") or ""
    print(f"\n[{r.status_code}] {method} {path}"
          f"{('   Allow: ' + allow) if allow else ''}")
    print(f"      {r.text[:400]}")
    return r


def main() -> None:
    s = get_settings()
    with httpx.Client(base_url=BASE, timeout=20.0) as http:
        print("=" * 72)
        print("KROK 1 — jakie metody dopuszcza zasób zlecenia? (OPTIONS + Allow)")
        print("=" * 72)
        _call(http, s, "OPTIONS", ORDERS)
        _call(http, s, "OPTIONS", f"{ORDERS}/999999999")
        # GET -> 405 also carries Allow; belt and braces.
        _call(http, s, "GET", f"{ORDERS}/999999999")

        print("\n" + "=" * 72)
        print("KROK 2 — składam 1 realne zlecenie $10 BTC, pełne NAGŁÓWKI + body")
        print("=" * 72)
        before = _positions(http, s)
        body = {
            "action": "open", "transaction": "Buy", "instrumentId": 100000,
            "orderType": "mkt", "leverage": 1, "amount": 10.0, "orderCurrency": "usd",
        }
        r = http.request("POST", ORDERS, headers=_h(s), json=body)
        print(f"\n[{r.status_code}] POST {ORDERS}")
        print("  NAGŁÓWKI odpowiedzi:")
        for k, v in r.headers.items():
            print(f"    {k}: {v}")
        print("  BODY:", r.text[:400])
        if r.status_code >= 400:
            print("\nPOST nie przeszedł — stop.")
            return
        p = r.json()
        oid = p.get("orderId")
        tok = p.get("token")
        ref = p.get("referenceId")
        print(f"\n  -> orderId={oid} token={tok} referenceId={ref}")

        print("\n" + "=" * 72)
        print("KROK 3 — próby POTWIERDZENIA tym tokenem (stop, gdy pojawi się pozycja)")
        print(f"        pozycji przed: {before}")
        print("=" * 72)
        # Ordered from most to least likely. Each re-checks the portfolio and
        # breaks on the first that materialises an order/position.
        attempts = [
            ("PUT", f"{ORDERS}/{oid}", {"token": tok}),
            ("PUT", f"{ORDERS}/{oid}", {"token": tok, "action": "confirm"}),
            ("POST", f"{ORDERS}/{oid}/confirm", {"token": tok}),
            ("POST", f"{ORDERS}/{oid}/execute", {"token": tok}),
            ("POST", f"{ORDERS}/confirm", {"token": tok, "orderId": oid, "referenceId": ref}),
            ("POST", "/api/v2/trading/execution/order-confirmations",
             {"token": tok, "orderId": oid, "referenceId": ref}),
        ]
        for method, path, b in attempts:
            _call(http, s, method, path, b)
            time.sleep(3)
            now = _positions(http, s)
            print(f"      pozycji teraz: {now}")
            if now > before:
                print(f"\n✅✅ POTWIERDZENIE DZIAŁA: {method} {path}  body={json.dumps(b)}")
                print("    (zlecenie weszło — zamknij pozycję ręcznie w aplikacji eToro)")
                return
        print("\n❌ Żadna próba potwierdzenia nie utworzyła pozycji.")
        print("   -> albo confirm ma inny kształt (patrz Allow/nagłówki wyżej),")
        print("      albo konto nie może handlować tym API (weryfikacja/typ tokena).")
    print("\n" + "=" * 72)
    print("GOTOWE — wklej całość (nagłówki z KROKU 2 i Allow z KROKU 1 są kluczowe).")
    print("=" * 72)


if __name__ == "__main__":
    main()
