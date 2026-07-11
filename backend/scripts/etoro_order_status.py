#!/usr/bin/env python3
"""Deep diagnostic for the "order accepted but never fills" eToro bug.

The v2 OPEN order returns an orderId (e.g. 1527760637) yet NO position appears,
credit is unchanged, and positions/orders/entryOrders are all empty. So the POST
is accepted but the order never executes. This script finds out WHY -- it:

  1. places ONE tiny real order and prints the *entire* raw JSON response
     (our client throws everything except orderId away, hiding the status
     field that says "pending"/"rejected"/"requiresConfirmation"/...);
  2. immediately polls the portfolio a few times (in case the fill is async);
  3. looks the order up by its id across every plausible status/history route
     so we learn where eToro parks it and what state it's in.

⚠️ Places ONE real order (default $10 BTC). If it *does* fill, close it by hand
in the eToro app. Run:

    docker compose exec -T app python scripts/etoro_order_status.py
    docker compose exec -T app python scripts/etoro_order_status.py BTC 10
    # look up an existing order id without placing a new one:
    docker compose exec -T app python scripts/etoro_order_status.py --lookup 1527760637
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


def _headers(s) -> dict:
    return {
        "x-api-key": s.etoro_api_key,
        "x-user-key": s.etoro_user_key,
        "x-request-id": str(uuid.uuid4()),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _show(http, s, method, path, **kwargs):
    try:
        r = http.request(method, path, headers=_headers(s), **kwargs)
        mark = "  <-- ISTNIEJE" if r.status_code != 404 else ""
        print(f"\n[{r.status_code}] {method} {path}{mark}")
        print(f"      {r.text[:600]}")
        return r
    except Exception as e:  # noqa: BLE001
        print(f"\n[ERR] {method} {path}: {type(e).__name__}: {e}")
        return None


# Every read-only place eToro might park a just-placed order, plus per-id lookups.
def _lookup(http, s, order_id: str):
    print("\n" + "=" * 72)
    print(f"SZUKAM zlecenia id={order_id} w endpointach statusu/historii")
    print("=" * 72)
    for path in [
        f"/api/v2/trading/execution/orders/{order_id}",
        f"/api/v1/trading/execution/orders/{order_id}",
        f"/api/v2/trading/orders/{order_id}",
        f"/api/v1/trading/info/orders/{order_id}",
    ]:
        _show(http, s, "GET", path)
    print("\n--- listy zleceń / historia (bez id) ---")
    for path in [
        "/api/v2/trading/execution/orders",
        "/api/v1/trading/info/orders",
        "/api/v1/trading/info/entry-orders",
        "/api/v1/trading/info/history",
        "/api/v1/trading/info/pending-orders",
    ]:
        _show(http, s, "GET", path)


def main() -> None:
    s = get_settings()
    if not s.etoro_api_key or not s.etoro_user_key:
        print("BRAK kluczy eToro. Przerywam.")
        return

    with httpx.Client(base_url=BASE, timeout=20.0) as http:
        if len(sys.argv) > 1 and sys.argv[1] == "--lookup":
            _lookup(http, s, sys.argv[2])
            return

        symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "BTC"
        usd = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
        # BTC=100000 is a KNOWN_ID; keep this list in sync with etoro_client.
        iid = {"BTC": 100000, "ETH": 100001, "SOL": 100063, "EURUSD": 1}.get(symbol, 100000)

        body = {
            "action": "open",
            "transaction": "Buy",
            "instrumentId": iid,
            "orderType": "mkt",
            "leverage": 1,
            "amount": round(usd, 2),
            "orderCurrency": "usd",
        }
        print("=" * 72)
        print(f"SKŁADAM 1 realne zlecenie: ${usd:.0f} {symbol} (id={iid})")
        print("Body:", json.dumps(body))
        print("=" * 72)
        r = _show(http, s, "POST", "/api/v2/trading/execution/orders", json=body)
        if r is None or r.status_code >= 400:
            print("\nPOST nie przeszedł — nie ma czego szukać.")
            return

        # Full raw response -- THIS is what our client discards. A status field
        # here (pending/rejected/reason) usually explains the silent no-fill.
        try:
            payload = r.json()
            print("\n>>> PEŁNA odpowiedź POST (surowa):")
            print(json.dumps(payload, indent=2)[:2000])
        except Exception:  # noqa: BLE001
            payload = {}
        order_id = str(payload.get("orderId") or payload.get("id") or payload.get("positionId") or "")

        # Async fill? Poll the portfolio a few times.
        print("\n--- portfel po zleceniu (3 próby co 4s) ---")
        for i in range(3):
            time.sleep(4)
            pr = http.request("GET", "/api/v1/trading/info/portfolio", headers=_headers(s))
            cp = pr.json().get("clientPortfolio", {}) if pr.status_code < 400 else {}
            print(f"[{i+1}] credit={cp.get('credit')} "
                  f"positions={len(cp.get('positions') or [])} "
                  f"orders={len(cp.get('orders') or [])} "
                  f"entryOrders={len(cp.get('entryOrders') or [])}")

        if order_id:
            _lookup(http, s, order_id)
    print("\n" + "=" * 72)
    print("GOTOWE — wklej całość. Szukamy pola statusu w odpowiedzi POST i tego,")
    print("gdzie (jeśli w ogóle) eToro trzyma to zlecenie.")
    print("=" * 72)


if __name__ == "__main__":
    main()
