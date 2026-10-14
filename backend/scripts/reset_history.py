#!/usr/bin/env python3
"""Clean-slate the dashboard's TRACKING history for a fresh start.

Wipes the app's OWN record -- decisions log, trades log, portfolio-value
snapshots (the chart), risk events -- and resets the Claude budget/token meters,
benchmark baseline, account-peak (drawdown re-bases) and per-cycle state. It also
CLEARS a loss-limit HALT (is_halted -> False). Learned lessons are PRESERVED by
default (a paper-balance reset shouldn't wipe the learning); pass --wipe-lessons
to clear those too. The dashboard then starts from zero.

It does NOT touch your real Alpaca account: no order is placed, cancelled or
even read here. Your live positions and cash stay exactly as they are -- the
next trading cycle simply re-snapshots them from scratch. So this ALONE will NOT
fix a blown balance (e.g. negative cash): reset the paper account on Alpaca first
(app.alpaca.markets -> paper -> Reset) to restore cash and flatten positions, THEN
run this to clean the app's mirror. Both engines are left STOPPED after the reset.

    docker compose exec -T app python scripts/reset_history.py --yes
    # add --wipe-lessons only if you also want to erase learned lessons
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal, init_db  # noqa: E402
from app.services.history_reset import reset_tracking  # noqa: E402


def main() -> None:
    if "--yes" not in sys.argv:
        print("To wyczyści CAŁĄ historię aplikacji (decyzje, transakcje-log, wykres, licznik tokenów/budżetu).")
        print("NIE rusza konta Alpaca — Twoje pozycje i gotówka zostają nietknięte.")
        print("Uruchom z --yes, aby potwierdzić:")
        print("    docker compose exec -T app python scripts/reset_history.py --yes")
        print("    # dodaj --wipe-lessons, jeśli chcesz skasować też nauczone lekcje")
        return

    init_db()
    db = SessionLocal()
    try:
        r = reset_tracking(db, wipe_lessons="--wipe-lessons" in sys.argv)
        lessons_note = "WYMAZANE" if r["lessons_wiped"] else "ZACHOWANE (nauka zostaje)"
        print("=" * 64)
        print(f"Wyczyszczono: transakcje(log)={r['trades']}, decyzje={r['decisions']}, "
              f"snapshoty={r['snapshots']}, zdarzenia_ryzyka={r['risk_events']}")
        print(f"Zresetowano: licznik tokenów/budżetu, baseline benchmarku, szczyt konta, "
              f"HALT zdjęty, stan cykli. Lekcje: {lessons_note}.")
        print("Oba silniki są STOP — naciśnij START, gdy gotowy.")
        print("UWAGA: to NIE resetuje konta Alpaca. Ujemną gotówkę/pozycje cofa dopiero")
        print("RESET PAPER w panelu Alpaca (app.alpaca.markets -> paper -> Reset).")
        print("=" * 64)
    finally:
        db.close()


if __name__ == "__main__":
    main()
