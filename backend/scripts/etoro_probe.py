"""Read-only probe of the eToro public API to discover the exact request/
response shapes before building the full client against them.

Runs GET requests only -- it never places, cancels or modifies an order, so it
is safe against a live key. Auth combo is already confirmed
(x-api-key=public, x-user-key=private); this round discovers:
  - the crypto instrument IDs (BTC/ETH/SOL) from the instrument catalogue,
  - the live account cash/positions shape,
  - which price/quote endpoint works,
  - which candle/history endpoint works.

Usage (on the VPS, where outbound network to eToro is open):

    cd ~/gie-d
    ETORO_API_KEY='<klucz publiczny>' ETORO_USER_KEY='<klucz prywatny>' \
        docker compose exec -T \
          -e ETORO_API_KEY -e ETORO_USER_KEY \
          app python scripts/etoro_probe.py

Paste the whole output back.
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
        return resp.status_code, (resp.text or "")[:600]


def _snippet(obj, n: int = 700) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)[:n]
    except Exception:
        return str(obj)[:n]


# 1) Instrument catalogue -> crypto IDs + the crypto instrumentTypeID.
print("=" * 70)
print("1) INSTRUMENTY — szukam krypto (BTC/ETH/SOL) w katalogu")
print("=" * 70)
code, data = _get("/api/v1/market-data/instruments")
instruments = data.get("instrumentDisplayDatas", []) if isinstance(data, dict) else []
print(f"[{code}] /api/v1/market-data/instruments  (liczba instrumentów: {len(instruments)})")

WANTED = ("BTC", "BITCOIN", "ETH", "ETHEREUM", "SOL", "SOLANA")
crypto_hits = []
type_ids = {}
for it in instruments:
    name = (it.get("instrumentDisplayName") or "").upper()
    tid = it.get("instrumentTypeID")
    type_ids[tid] = type_ids.get(tid, 0) + 1
    if any(w == name or w in name.split() or name.startswith(w) for w in WANTED):
        crypto_hits.append((it.get("instrumentID"), it.get("instrumentDisplayName"), tid))

print("  Trafienia krypto (instrumentID, nazwa, typeID):")
for c in crypto_hits[:60]:
    print("   ", c)
print("  Rozkład instrumentTypeID (typeID: ile):", dict(sorted(type_ids.items(), key=lambda x: -x[1])[:12]))

probe_id = crypto_hits[0][0] if crypto_hits else 1  # fall back to EUR/USD id=1

# 2) Live portfolio shape (cash + positions).
print("\n" + "=" * 70)
print("2) PORTFEL NA ŻYWO — saldo + kształt pozycji")
print("=" * 70)
code, data = _get("/api/v1/trading/info/portfolio")
print(f"[{code}] /api/v1/trading/info/portfolio")
print("   ", _snippet(data, 1200))

# 3) Price / quote endpoint candidates (using a real crypto id).
print("\n" + "=" * 70)
print(f"3) CENY — kandydaci na endpoint (instrumentID={probe_id})")
print("=" * 70)
price_paths = [
    f"/api/v1/market-data/rates?instrumentIds={probe_id}",
    f"/api/v1/market-data/prices?instrumentIds={probe_id}",
    f"/api/v1/market-data/live-prices?instrumentIds={probe_id}",
    f"/api/v1/market-data/closing-prices?instrumentIds={probe_id}",
    f"/api/v1/market-data/instruments/{probe_id}",
    f"/api/v1/trading/info/rate?instrumentIds={probe_id}",
    f"/api/v1/market-data/instruments/rates?instrumentIds={probe_id}",
]
for p in price_paths:
    code, data = _get(p)
    print(f"\n[{code}] GET {p}")
    print("   ", _snippet(data, 500))

# 4) Candle / history endpoint candidates.
print("\n" + "=" * 70)
print(f"4) ŚWIECE — kandydaci na endpoint (instrumentID={probe_id})")
print("=" * 70)
candle_paths = [
    f"/api/v1/market-data/candles?instrumentIds={probe_id}&interval=OneHour&count=200",
    f"/api/v1/market-data/candles?instrumentId={probe_id}&period=OneHour&limit=200",
    f"/api/v1/market-data/candles/{probe_id}?interval=OneHour",
    f"/api/v1/market-data/candles?instrumentIds={probe_id}&interval=OneHour",
    f"/api/v1/market-data/history/candles?instrumentIds={probe_id}&interval=OneHour",
    f"/api/v1/candles?instrumentIds={probe_id}&interval=OneHour",
]
for p in candle_paths:
    code, data = _get(p)
    print(f"\n[{code}] GET {p}")
    print("   ", _snippet(data, 500))

print("\n" + "=" * 70)
print("GOTOWE — wklej całość powyżej z powrotem.")
print("=" * 70)
