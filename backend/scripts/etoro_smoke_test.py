#!/usr/bin/env python3
"""Live smoke test for the fixed eToro v2 order flow: open a tiny position, then
close it -- proving BOTH directions work before the bot is trusted to trade.

⚠️  THIS PLACES REAL ORDERS on the live eToro account (default $10 BTC round
trip; the spread costs a few cents). It opens a long, reads it back from the
portfolio, then closes exactly what was opened. If the CLOSE step fails, it says
so loudly so you can close the leftover position by hand in the eToro app.

    docker compose exec -T app python scripts/etoro_smoke_test.py
    docker compose exec -T app python scripts/etoro_smoke_test.py EURUSD 15
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings  # noqa: E402
from app.services.etoro_client import EToroAPIError, EToroClient  # noqa: E402


def main() -> None:
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "BTC"
    usd = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    b = EToroClient(get_settings())

    print("=" * 68)
    print(f"SMOKE TEST eToro — otwieram ${usd:.0f} {symbol}, potem zamykam (REALNE)")
    print("=" * 68)
    print("Saldo przed:", b.get_account_balances())

    try:
        r = b.place_order_for_session(symbol, "BUY", usdt_amount=usd)
        print(f"\n✅ OTWARTO: order={r.order_id} units={r.quantity:.8f} @ {r.price:.4f}")
    except EToroAPIError as e:
        print(f"\n❌ OTWARCIE NIEUDANE: {e}")
        return

    time.sleep(5)
    bal = b.get_account_balances()
    print("Saldo po otwarciu:", bal)
    held = float(bal.get(symbol, 0.0))
    if held <= 0:
        print(f"\n⚠️  Brak pozycji {symbol} w saldzie — zlecenie mogło nie wejść. "
              "Sprawdź w aplikacji eToro przed dalszymi testami.")
        return

    try:
        r2 = b.place_order_for_session(symbol, "SELL", quantity=held)
        print(f"\n✅ ZAMKNIĘTO: order={r2.order_id} units={r2.quantity:.8f}")
    except EToroAPIError as e:
        print(f"\n❌ ZAMKNIĘCIE NIEUDANE — ZAMKNIJ POZYCJĘ RĘCZNIE W APLIKACJI eToro! {e}")
        return

    time.sleep(5)
    print("Saldo po zamknięciu:", b.get_account_balances())
    print("\n" + "=" * 68)
    print("KONIEC. Jeśli oba kroki ✅ i saldo wróciło ~do samego USD → NAPRAWIONE.")
    print("=" * 68)


if __name__ == "__main__":
    main()
