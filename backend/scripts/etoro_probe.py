"""Read-only probe of the eToro public API -- final round: find the candle
(OHLC history) endpoint, and confirm live rates for real spot crypto + forex
instrument IDs.

GET only -- never places/cancels/modifies an order. Safe against a live key.

Known so far:
  auth  = headers x-api-key(public) + x-user-key(private)
  rates = GET /api/v1/market-data/instruments/rates?instrumentIds=<id>  (ask/bid)
  ids   = Bitcoin 100000, Ethereum 100001, Solana 100063, EUR/USD 1 (typeID 10=crypto, 1=forex)

Usage (on the VPS):
    cd ~/gie-d
    ETORO_API_KEY='<pub>' ETORO_USER_KEY='<priv>' \
      docker compose exec -T -e ETORO_API_KEY -e ETORO_USER_KEY \
      app python scripts/etoro_probe.py
"""

import json
import os
import sys
import uuid

import httpx

BASE = "https://public-api.etoro.com"
TIMEOUT = 25.0

API_KEY = os.environ.get("ETORO_API_KEY", "").strip()
USER_KEY = os.environ.get("ETORO_USER_KEY", "").strip()

if not API_KEY or not USER_KEY:
    print("BRAK KLUCZY: ustaw ETORO_API_KEY i ETORO_USER_KEY w środowisku.")
    sys.exit(1)


def _headers() -> dict:
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Accept": "application/json",
    }


def _get(path: str):
    try:
        resp = httpx.get(f"{BASE}{path}", headers=_headers(), timeout=TIMEOUT, follow_redirects=True)
    except Exception as exc:
        return -1, f"EXC {type(exc).__name__}: {exc}"
    try:
        return resp.status_code, resp.json()
    except Exception:
        return resp.status_code, (resp.text or "")[:400]


def _snip(obj, n=450):
    try:
        return json.dumps(obj, ensure_ascii=False)[:n]
    except Exception:
        return str(obj)[:n]


BTC = 100000  # spot Bitcoin
EURUSD = 1    # forex

# 1) Confirm live rates for real spot crypto + forex (315 earlier was a stale future).
print("=" * 70)
print("1) RATES dla realnych ID (spot BTC 100000, EUR/USD 1)")
print("=" * 70)
for iid in (BTC, EURUSD):
    code, data = _get(f"/api/v1/market-data/instruments/rates?instrumentIds={iid}")
    print(f"[{code}] rates instrumentIds={iid}: {_snip(data, 400)}")

# 2) Hunt the candles endpoint -- try the /instruments/ sibling of /rates plus variants.
print("\n" + "=" * 70)
print("2) ŚWIECE — szeroka macierz endpointów/parametrów (BTC 100000)")
print("=" * 70)

bases = [
    "/api/v1/market-data/instruments/candles",
    "/api/v1/market-data/candles/instruments",
    "/api/v1/market-data/instrument/candles",
    "/api/v1/market-data/instruments/history",
    "/api/v1/market-data/instruments/rates/history",
    "/api/v1/market-data/candle",
]
param_sets = [
    f"instrumentIds={BTC}&interval=OneHour&candlesNumber=200",
    f"instrumentIds={BTC}&period=OneHour&count=200",
    f"instrumentIds={BTC}&candlePeriod=OneHour&candlesNumber=200",
    f"instrumentIds={BTC}&interval=OneHour",
]
path_style = [
    f"/api/v1/market-data/instruments/{BTC}/candles?interval=OneHour&candlesNumber=200",
    f"/api/v1/market-data/instruments/candles/{BTC}?interval=OneHour&candlesNumber=200",
    f"/api/v1/market-data/candles/{BTC}?period=OneHour&count=200",
]

tried = 0
for base in bases:
    for ps in param_sets:
        path = f"{base}?{ps}"
        code, data = _get(path)
        tried += 1
        # Only print non-404s in full; summarize 404s tersely to keep it readable.
        if code == 404:
            print(f"[404] {path}")
        else:
            print(f"\n[{code}] {path}\n    {_snip(data, 500)}")
for path in path_style:
    code, data = _get(path)
    if code == 404:
        print(f"[404] {path}")
    else:
        print(f"\n[{code}] {path}\n    {_snip(data, 500)}")

print("\n" + "=" * 70)
print(f"GOTOWE — sprawdzono {tried + len(path_style)} wariantów. Wklej całość.")
print("=" * 70)
