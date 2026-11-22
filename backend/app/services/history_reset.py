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

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Decision, PortfolioSnapshot, RiskEvent, SystemState, Trade

logger = logging.getLogger(__name__)

# Wersja czystego startu Kraken. Bump = jednorazowe ponowne przepuszczenie migracji
# (re-bazowanie punktów odniesienia + zdjęcie lepkich haltów). Patrz kraken_clean_slate.
_SLATE_VERSION = "2026-11-22-heal-fallback"

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


# Wersja pełnego przepięcia na Kraken. Bump = przepuść wycięcie RAZ jeszcze.
_CUTOVER_VERSION = "2026-11-22-kraken-only-v2-allsnaps"


def kraken_full_cutover(db: Session) -> dict | None:
    """PEŁNE PRZEPIĘCIE NA KRAKEN (decyzja właściciela „nie wracam do Alpaki").
    Wycina CAŁĄ historię ery Alpaca/extended (snapshoty, decyzje, transakcje tych
    nóg) i re-bazuje punkty odniesienia ryzyka, ale — w odróżnieniu od reset_tracking —
    ZOSTAWIA dane nogi KRYPTO (otwarta pozycja NIGHT/EUR, jej koszt i decyzje) oraz
    LEKCJE. Zdejmuje lepki halt „spadek od szczytu" oparty na widmowym szczycie Alpaca.
    Idempotentny (znacznik wersji). Zwraca podsumowanie albo None, gdy pominięto.

    Dlaczego osobno od kraken_clean_slate: clean-slate kasuje WSZYSTKO (w tym otwartą
    pozycję krypto), więc z żywą pozycją jest niebezpieczny. To wycięcie jest celowane
    w nogi akcji — nic z żywego konta Kraken nie ginie."""
    state = db.get(SystemState, 1)
    if state is None:
        return None
    if (getattr(state, "kraken_cutover_at", "") or "").strip() == _CUTOVER_VERSION:
        return None  # już wycięte na tej wersji
    from app.config import get_settings
    if getattr(get_settings(), "crypto_venue", "alpaca") != "kraken":
        return None  # tylko dla trybu Kraken

    dead_venues = ("alpaca", "extended")
    # Transakcje PRZED decyzjami (FK: trades -> decisions). Tylko nogi akcji.
    n_tr = db.query(Trade).filter(Trade.venue.in_(dead_venues)).delete(synchronize_session=False)
    n_dec = db.query(Decision).filter(Decision.venue.in_(dead_venues)).delete(synchronize_session=False)
    # Snapshoty: KASUJEMY WSZYSTKIE (każda noga). To tylko historia wykresu, NIE
    # pozycje (te są w trades + saldzie brokera). Powód: zostały STARE snapshoty
    # krypto z ery Alpaca (gotówka ~$594k, pozycje ~$14k) — _latest_snapshot('crypto')
    # i account_total_value brały je jako „konto Kraken" i reanimowały widmo $608k/
    # szczyt $840k. Pierwszy cykl Kraken zapisze świeży snapshot €120.
    n_snap = db.query(PortfolioSnapshot).delete(synchronize_session=False)
    # Re-baza ryzyka do realu (0 => następny cykl krypto ustawi szczyt = konto Kraken).
    state.peak_account_value = 0.0
    state.pending_peak_value = 0.0
    state.pending_peak_confirmations = 0
    state.day_start_value = 0.0
    state.day_start_date = ""
    state.week_start_value = 0.0
    state.week_start_date = ""
    state.benchmark_start_date = ""
    state.benchmark_start_price = 0.0
    state.benchmark_start_value = 0.0
    # Zdejmij lepki fałszywy halt spadku-od-szczytu (widmo Alpaca $840k).
    if state.is_halted and (state.halted_reason or "").startswith("Spadek od szczytu"):
        state.is_halted = False
        state.halted_reason = None
    # Noga akcji wyłączona i zapauzowana; krypto zostaje aktywne.
    state.is_paused = True
    state.extended_paused = True
    state.crypto_paused = False
    state.kraken_cutover_at = _CUTOVER_VERSION
    db.commit()
    logger.warning(
        "KRAKEN PEŁNE PRZEPIĘCIE: wycięto erę Alpaca/extended (trades=%s decisions=%s "
        "snapshots=%s), re-baza ryzyka, zdjęto widmowy halt. Krypto + lekcje nietknięte.",
        n_tr, n_dec, n_snap,
    )
    return {"trades": n_tr, "decisions": n_dec, "snapshots": n_snap, "kraken_cutover_at": _CUTOVER_VERSION}


def kraken_clean_slate(db: Session) -> dict | None:
    """JEDNORAZOWY czysty start przy migracji Alpaca->Kraken. Odpala się RAZ (gdy
    crypto_venue=='kraken' i znacznik pusty), na starcie aplikacji. Czyści historię
    ery Alpaca (reset_tracking: transakcje/decyzje/snapshoty/zdarzenia, re-bazuje
    szczyt, ZDEJMUJE fałszywy HALT z -100%), ale — inaczej niż ręczny reset —
    ZOSTAWIA nogę krypto WŁĄCZONĄ (crypto_paused=False) i ustawia epokę pomiaru na
    teraz (start Kraken). Lekcje zachowane. Idempotentny: znacznik blokuje powtórkę.
    Zwraca podsumowanie albo None, gdy pominięto."""
    state = db.get(SystemState, 1)
    if state is None:
        return None
    # Wersjonowany znacznik: bump = przepuść czysty start RAZ jeszcze. Powód bumpu
    # „heal-fallback": nieistniejący już fallback na Alpacę zatruł punkty odniesienia
    # (day/week/peak) i zostawił lepkie halty (-100% dnia, rozjazd rekoncyliacji) na
    # koncie Kraken z €120. Ponowny czysty start re-bazuje je i zdejmuje halt. 0
    # transakcji => nic realnego nie ginie.
    # UWAGA: gdy jest już OTWARTA pozycja na żywo, NIE bumpuj tej wersji — reset_tracking
    # kasuje trades/decisions, a to zabrałoby bazę kosztową otwartej pozycji. Lepki halt
    # „spadek od szczytu" zdejmuj wtedy przez kraken_heal_peak (niżej), który NIE rusza
    # historii transakcji.
    if (getattr(state, "kraken_slate_reset_at", "") or "").strip() == _SLATE_VERSION:
        return None  # już na aktualnej wersji — nie powtarzamy
    from app.config import get_settings
    if getattr(get_settings(), "crypto_venue", "alpaca") != "kraken":
        return None  # czysty start tylko dla migracji na Kraken
    r = reset_tracking(db, wipe_lessons=False)
    state = db.get(SystemState, 1)
    now = datetime.now(UTC).isoformat()
    # reset_tracking pauzuje OBA silniki; nogę krypto na Kraken zostawiamy AKTYWNĄ,
    # żeby paper ruszył od razu (equities i tak nieużywane -> is_paused zostaje True).
    state.crypto_paused = False
    state.stats_epoch = now               # pomiar od startu Kraken
    state.kraken_slate_reset_at = _SLATE_VERSION  # znacznik wersji: nie powtarzaj
    db.commit()
    logger.warning(
        "KRAKEN CZYSTY START: wyczyszczono erę Alpaca (trades=%s decisions=%s "
        "snapshots=%s risk_events=%s), zdjęto HALT, epoka=%s, krypto AKTYWNE (paper).",
        r["trades"], r["decisions"], r["snapshots"], r["risk_events"], now,
    )
    return {**r, "kraken_slate_reset_at": now}
