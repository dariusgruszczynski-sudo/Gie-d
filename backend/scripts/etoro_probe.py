"""Smoke-test the EToroClient against the live eToro API (read-only).

Exercises the client's verified read paths end-to-end -- instrument-id
resolution, live price (rates), candles (external OHLC source), and account
balances -- so we confirm the whole read layer works from the VPS before wiring
eToro into the trading engine. Places NO orders.

Usage (on the VPS):
    cd ~/gie-d
    ETORO_API_KEY='<pub>' ETORO_USER_KEY='<priv>' \
      docker compose exec -T -e ETORO_API_KEY -e ETORO_USER_KEY \
      app python scripts/etoro_probe.py
"""

from app.config import Settings
from app.services.etoro_client import EToroClient

settings = Settings()  # reads ETORO_API_KEY / ETORO_USER_KEY from the environment
client = EToroClient(settings)

print("=" * 60)
print("CENY (get_price -> środek ask/bid)")
print("=" * 60)
for sym in ["BTC", "ETH", "SOL", "EURUSD"]:
    try:
        print(f"  {sym:7} id={client.instrument_id(sym):>7}  cena={client.get_price(sym)}")
    except Exception as exc:
        print(f"  {sym:7} BŁĄD: {exc}")

print("\n" + "=" * 60)
print("ŚWIECE (get_klines -> zewnętrzne OHLC do wskaźników)")
print("=" * 60)
for sym in ["BTC", "ETH", "SOL", "EURUSD"]:
    try:
        rows = client.get_klines(sym, "1h", 200)
        last = rows[-1][4] if rows else None
        print(f"  {sym:7} barów={len(rows):>3}  ostatnie zamknięcie={last}")
    except Exception as exc:
        print(f"  {sym:7} BŁĄD: {exc}")

print("\n" + "=" * 60)
print("SALDO (get_account_balances)")
print("=" * 60)
try:
    print("  ", client.get_account_balances())
except Exception as exc:
    print("  BŁĄD:", exc)

print("\nGOTOWE — wklej całość.")
