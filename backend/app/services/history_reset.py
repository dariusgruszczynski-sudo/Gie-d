"""Czyszczenie WŁASNEJ historii aplikacji na czysty start (jedno źródło prawdy
dla skryptu CLI `scripts/reset_history.py` i przycisku „Reset do czysta" w apce).

Kasuje log decyzji/transakcji, snapshoty wykresu i zdarzenia ryzyka; resetuje
liczniki budżetu/tokenów, baseline benchmarku, SZCZYT konta (drawdown re-bazuje),
stan cykli; ZDEJMUJE loss-limit HALT i zostawia oba silniki w STOP. Lekcje
(lessons_json) są ZACHOWANE domyślnie — reset salda paper nie powinien zdmuchiwać
NAUKI; wipe_lessons=True kasuje też lekcje.

NIE rusza konta Alpaca: żadne zlecenie nie jest składane ani odczytywane. Ujemną
gotówkę/pozycje cofa dopiero RESET PAPER po stronie Alpaki — ta funkcja czyści
tylko lustro aplikacji i musi iść PO resecie konta."""

from sqlalchemy.orm import Session

from app.models import Decision, PortfolioSnapshot, RiskEvent, SystemState, Trade

# Pola SystemState przywracane do stanu świeżej instalacji. session_secret jest
# CELOWO pomijany (żeby otwarte sesje logowania przetrwały). Oba silniki -> STOP.
RESET_STATE: dict = {
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
    "last_self_review_date": "",
    "market_regime_json": "{}", "crypto_market_regime_json": "{}",
    # Szczyt konta re-bazuje się od świeżego salda (po resecie paper ~100k), żeby
    # drawdown/halt nie liczył od starego szczytu zdmuchniętego konta. 0 => następny
    # cykl ustawi peak = bieżąca wartość (patrz risk_manager).
    "peak_account_value": 0.0,
    "is_paused": True, "crypto_paused": True, "is_halted": False, "halted_reason": None,
}


def reset_tracking(db: Session, *, wipe_lessons: bool = False) -> dict:
    """Czyści historię aplikacji i resetuje stan. Zwraca liczby skasowanych wierszy.
    NIE dotyka konta Alpaca. Lekcje zachowane, chyba że wipe_lessons=True."""
    # Transakcje PRZED decyzjami (FK: trades -> decisions).
    n_tr = db.query(Trade).delete()
    n_dec = db.query(Decision).delete()
    n_snap = db.query(PortfolioSnapshot).delete()
    n_re = db.query(RiskEvent).delete()
    state = db.get(SystemState, 1)
    if state is not None:
        for key, value in RESET_STATE.items():
            setattr(state, key, value)
        if wipe_lessons:
            state.lessons_json = "[]"
    db.commit()
    return {
        "trades": n_tr, "decisions": n_dec, "snapshots": n_snap,
        "risk_events": n_re, "lessons_wiped": wipe_lessons,
    }
