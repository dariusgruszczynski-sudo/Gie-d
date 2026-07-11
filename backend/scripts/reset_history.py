#!/usr/bin/env python3
"""Clean-slate the dashboard's TRACKING history for a fresh start.

Wipes the app's OWN record -- decisions log, trades log, portfolio-value
snapshots (the chart), risk events -- and resets the Claude budget/token meters,
benchmark baseline, learned lessons and per-cycle state. The dashboard then
starts from zero.

It does NOT touch your real Alpaca account: no order is placed, cancelled or
even read here. Your live positions and cash stay exactly as they are -- the
next trading cycle simply re-snapshots them from scratch. Both engines are left
STOPPED after the reset, so nothing trades until you press START.

    docker compose exec -T app python scripts/reset_history.py --yes
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Decision, PortfolioSnapshot, RiskEvent, SystemState, Trade  # noqa: E402

# SystemState fields reset to a fresh install. session_secret is deliberately
# preserved (so open dashboard logins survive). Both engines left STOPPED.
RESET_STATE = {
    "claude_budget_month_key": "", "claude_spend_usd_this_month": 0.0,
    "claude_input_tokens_this_month": 0, "claude_output_tokens_this_month": 0,
    "day_start_date": "", "day_start_value": 0.0,
    "week_start_date": "", "week_start_value": 0.0,
    "last_check_prices_json": "{}", "last_full_analysis_date": "", "last_analysis_at": "",
    "stop_loss_cooldowns_json": "{}", "position_peaks_json": "{}",
    "partial_tp_taken_json": "{}", "stop_loss_streak_json": "{}",
    "seen_ticker_headlines_json": "{}",
    "crypto_check_prices_json": "{}", "crypto_position_peaks_json": "{}",
    "crypto_stop_loss_cooldowns_json": "{}", "crypto_seen_ticker_headlines_json": "{}",
    "crypto_analysis_state_json": "{}", "crypto_partial_tp_taken_json": "{}",
    "crypto_stop_loss_streak_json": "{}",
    "benchmark_start_date": "", "benchmark_start_price": 0.0, "benchmark_start_value": 0.0,
    "lessons_json": "[]", "last_self_review_date": "",
    "market_regime_json": "{}", "crypto_market_regime_json": "{}",
    "is_paused": True, "crypto_paused": True, "is_halted": False, "halted_reason": None,
}


def main() -> None:
    if "--yes" not in sys.argv:
        print("To wyczyści CAŁĄ historię aplikacji (decyzje, transakcje-log, wykres, licznik tokenów/budżetu).")
        print("NIE rusza konta Alpaca — Twoje pozycje i gotówka zostają nietknięte.")
        print("Uruchom z --yes, aby potwierdzić:")
        print("    docker compose exec -T app python scripts/reset_history.py --yes")
        return

    init_db()
    db = SessionLocal()
    try:
        # Delete trades BEFORE decisions (trades FK-reference decisions).
        n_tr = db.query(Trade).delete()
        n_dec = db.query(Decision).delete()
        n_snap = db.query(PortfolioSnapshot).delete()
        n_re = db.query(RiskEvent).delete()
        state = db.get(SystemState, 1)
        if state is not None:
            for key, value in RESET_STATE.items():
                setattr(state, key, value)
        db.commit()
        print("=" * 64)
        print(f"Wyczyszczono: transakcje(log)={n_tr}, decyzje={n_dec}, "
              f"snapshoty={n_snap}, zdarzenia_ryzyka={n_re}")
        print("Zresetowano: licznik tokenów/budżetu, baseline benchmarku, lekcje, stan cykli.")
        print("Oba silniki są STOP — naciśnij START, gdy gotowy. Konto Alpaca NIETKNIĘTE.")
        print("=" * 64)
    finally:
        db.close()


if __name__ == "__main__":
    main()
