"""Central risk-control state machine.

Responsibilities:
- track day/week starting portfolio value and trip a halt when the loss
  limit configured in Settings is breached
- enforce the trading whitelist and max single-position size
- expose pause/resume for the manual "big red button" in the dashboard

Automated (Opus-driven) trades are blocked while halted or paused. Manual
trades initiated by the human from the dashboard are never blocked here by
design — that is the whole point of keeping a manual override available.
"""

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import RiskEvent, SystemState

logger = logging.getLogger(__name__)

# See update_portfolio_value(): a candidate new all-time-high must be seen on
# this many total updates (the first sighting plus this many minus one more)
# at/above it before it's promoted to the real peak used by the drawdown
# halt. Tolerance allows trivial price-noise dips between the confirming
# reads without resetting the candidate.
PEAK_CONFIRMATION_UPDATES = 2
PEAK_CONFIRMATION_TOLERANCE = 0.999

# Strata w JEDNYM odczycie grubo ponad fizycznie możliwą (>60%) to nie ruch
# rynku, tylko BŁĄD WYCENY -- np. pozycje (krypto) chwilowo wypadły z sumy konta
# i konto odczytało się jako „sama gotówka" (~$350 z $100k = pozorne -99%). Na
# takim widmie NIE zatrzymujemy handlu, a istniejący widmowy halt sam się zdejmie,
# gdy wycena wróci. Realny limit (np. -20% dnia) trzyma się normalnie i zostaje
# lepki do ręcznego Wznów. Spot-konto majorsów nie traci 60% w jednym cyklu.
PHANTOM_LOSS_PCT = 60.0


def _halt_was_phantom(reason: str | None) -> bool:
    """Czy zapisany powód haltu niesie WIDMOWĄ stratę (>= PHANTOM_LOSS_PCT)? Powody
    mają stały format „... -<liczba>% ...", więc wyłuskujemy pierwszą liczbę po
    minusie. Realny limit (np. -20%) -> False (halt zostaje lepki); widmowe -99,6%
    -> True (kwalifikuje się do samo-zdjęcia po powrocie poprawnej wyceny)."""
    if not reason:
        return False
    m = re.search(r"-(\d+(?:[.,]\d+)?)\s*%", reason)
    if not m:
        return False
    try:
        return float(m.group(1).replace(",", ".")) >= PHANTOM_LOSS_PCT
    except ValueError:
        return False


@dataclass
class ValidationResult:
    approved: bool
    reason: str | None = None


def get_state(db: Session) -> SystemState:
    state = db.get(SystemState, 1)
    if state is None:
        today = date.today().isoformat()
        state = SystemState(
            id=1,
            day_start_date=today,
            week_start_date=today,
        )
        db.add(state)
        try:
            db.commit()
        except IntegrityError:
            # Another session (scheduler thread vs. an API request, both
            # hitting an empty table for the first time) already inserted the
            # singleton row concurrently -- back off and read what it wrote.
            db.rollback()
            state = db.get(SystemState, 1)
        else:
            db.refresh(state)
    return state


def _log_event(db: Session, event_type: str, details: str) -> None:
    db.add(RiskEvent(event_type=event_type, details=details))
    db.commit()


def record_deposit(db: Session, settings: Settings, amount_usd: float) -> dict:
    """Zapisz zewnętrzną WPŁATĘ (top-up) tak, by NIGDY nie czytała się jako zysk
    handlu ani jako przewaga nad SPY. Wpłata podnosi wartość konta, ale nie jest
    P&L, więc:
      * doliczamy ją do sumy wpłat (deposits_usd_lifetime),
      * przesuwamy okna dnia/tygodnia i szczyt obsunięcia o kwotę wpłaty
        (żeby „zysk dziś/tydzień" i drawdown jej nie policzyły),
      * dajemy tę samą gotówkę benchmarkowi SPY (jakby wpłacona w SPY dziś),
        żeby alfa nie skoczyła sztucznie — porównanie zostaje ciągłe.
    Kwota ujemna = wypłata (działa symetrycznie). Zwraca sumę wpłat."""
    import json

    from app.models import PortfolioSnapshot

    if amount_usd == 0:
        raise ValueError("Kwota wpłaty nie może być zerem.")
    state = get_state(db)
    state.deposits_usd_lifetime = (state.deposits_usd_lifetime or 0.0) + amount_usd
    # Wpłata to nie wynik handlu — przesuń baseline'y dnia/tygodnia i szczyt.
    if (state.day_start_value or 0) > 0:
        state.day_start_value += amount_usd
    if (state.week_start_value or 0) > 0:
        state.week_start_value += amount_usd
    if (state.peak_account_value or 0) > 0:
        state.peak_account_value = max(0.0, state.peak_account_value + amount_usd)
    # Benchmark SPY dostaje tę samą wpłatę po dzisiejszej cenie -> alfa się nie
    # zmienia w momencie wpłaty (rośnie dalej tylko z rynku).
    if (state.benchmark_start_price or 0) > 0 and (state.benchmark_start_value or 0) > 0:
        snap = (
            db.query(PortfolioSnapshot)
            .filter(PortfolioSnapshot.venue == "alpaca")
            .order_by(PortfolioSnapshot.timestamp.desc())
            .first()
        )
        spy_now = None
        if snap is not None:
            try:
                spy_now = json.loads(snap.prices_json or "{}").get(settings.benchmark_symbol)
            except (TypeError, ValueError):
                spy_now = None
        if spy_now and spy_now > 0:
            state.benchmark_start_value = max(
                0.0, state.benchmark_start_value + amount_usd * state.benchmark_start_price / spy_now
            )
    _log_event(db, "deposit", f"amount={amount_usd:.2f} lifetime={state.deposits_usd_lifetime:.2f}")
    db.commit()
    return {"deposits_usd_lifetime": round(state.deposits_usd_lifetime, 2)}


def update_portfolio_value(db: Session, settings: Settings, total_value_usdt: float) -> SystemState:
    """Call this every time we compute a fresh portfolio value. Rolls the
    day/week windows forward and trips the halt if a loss limit is breached."""
    state = get_state(db)
    today = date.today()
    today_str = today.isoformat()

    if state.day_start_date != today_str:
        state.day_start_date = today_str
        state.day_start_value = total_value_usdt

    if not state.week_start_date:
        state.week_start_date = today_str
        state.week_start_value = total_value_usdt
    else:
        week_start = date.fromisoformat(state.week_start_date)
        if today - week_start >= timedelta(days=7):
            state.week_start_date = today_str
            state.week_start_value = total_value_usdt

    if state.day_start_value == 0:
        state.day_start_value = total_value_usdt
    if state.week_start_value == 0:
        state.week_start_value = total_value_usdt

    day_loss_pct = (
        (state.day_start_value - total_value_usdt) / state.day_start_value * 100
        if state.day_start_value > 0
        else 0
    )
    week_loss_pct = (
        (state.week_start_value - total_value_usdt) / state.week_start_value * 100
        if state.week_start_value > 0
        else 0
    )

    # All-time peak (not the rolling day/week baseline) -- catches a slow,
    # multi-day bleed that never breaches the daily/weekly limit on any single
    # day but adds up to a real capital hole. A brand-new peak isn't
    # canonized on the spot: it first becomes a PENDING candidate and only
    # promotes to the real peak once corroborated by PEAK_CONFIRMATION_UPDATES
    # total updates at/above it. This exists because account_total_value()
    # combines this venue's live numbers with the other venue's last stored
    # snapshot -- both venues briefly holding positions at the same moment can
    # inflate the combined total for a few hours before one leg closes out,
    # and without this guard that transient high gets locked in as an
    # all-time peak the account's real, sustained value never reaches again
    # (a permanently unfair drawdown reference, not a real loss). The very
    # first-ever value is exempt -- there's no prior peak to protect yet.
    if state.peak_account_value <= 0:
        state.peak_account_value = total_value_usdt
        state.pending_peak_value = 0.0
        state.pending_peak_confirmations = 0
    elif total_value_usdt > state.peak_account_value:
        if (
            state.pending_peak_value > 0
            and total_value_usdt >= state.pending_peak_value * PEAK_CONFIRMATION_TOLERANCE
        ):
            state.pending_peak_confirmations += 1
        else:
            state.pending_peak_value = total_value_usdt
            state.pending_peak_confirmations = 1
        state.pending_peak_value = max(state.pending_peak_value, total_value_usdt)
        if state.pending_peak_confirmations >= PEAK_CONFIRMATION_UPDATES:
            state.peak_account_value = state.pending_peak_value
            state.pending_peak_value = 0.0
            state.pending_peak_confirmations = 0
    else:
        # Dropped back to (or below) the last confirmed peak -- any candidate
        # in progress wasn't sustained, so it doesn't count towards confirming.
        state.pending_peak_value = 0.0
        state.pending_peak_confirmations = 0
    drawdown_pct = (
        (state.peak_account_value - total_value_usdt) / state.peak_account_value * 100
        if state.peak_account_value > 0
        else 0
    )

    # Czy bieżący odczyt to WIDMO (błąd wyceny), a nie realna strata? Każda z
    # trzech „strat" grubo ponad fizycznie możliwą => pozycje wypadły z sumy konta.
    phantom_read = (
        day_loss_pct >= PHANTOM_LOSS_PCT
        or week_loss_pct >= PHANTOM_LOSS_PCT
        or drawdown_pct >= PHANTOM_LOSS_PCT
    )

    # SAMO-LECZENIE WIDMOWEGO haltu: jeśli jesteśmy zatrzymani, a świeża (poprawna)
    # wycena pokazuje, że straty NIE MA (wszystkie limity w normie) ORAZ halt był
    # wpisany z WIDMOWĄ wartością (>60% — patrz PHANTOM_LOSS_PCT), zdejmij go. Dzięki
    # temu istniejący fałszywy halt -99,6% schodzi sam po naprawie wyceny, a REALNY
    # limit (np. -20%) zostaje lepki do ręcznego Wznów (jego zapisana wartość < 60%).
    if (
        state.is_halted
        and _halt_was_phantom(state.halted_reason)
        and day_loss_pct < settings.daily_loss_limit_pct
        and week_loss_pct < settings.weekly_loss_limit_pct
        and (settings.max_drawdown_halt_pct <= 0 or drawdown_pct < settings.max_drawdown_halt_pct)
    ):
        cleared = state.halted_reason
        state.is_halted = False
        state.halted_reason = None
        _log_event(db, "halt_auto_cleared", f"Auto-zdjęto WIDMOWY halt po poprawnej wycenie: {cleared}")

    newly_halted = False
    if not state.is_halted and not phantom_read:
        if day_loss_pct >= settings.daily_loss_limit_pct:
            state.is_halted = True
            state.halted_reason = (
                f"Dzienny limit strat przekroczony: -{day_loss_pct:.1f}% "
                f"(limit {settings.daily_loss_limit_pct}%)"
            )
            _log_event(db, "daily_stop_triggered", state.halted_reason)
            newly_halted = True
        elif week_loss_pct >= settings.weekly_loss_limit_pct:
            state.is_halted = True
            state.halted_reason = (
                f"Tygodniowy limit strat przekroczony: -{week_loss_pct:.1f}% "
                f"(limit {settings.weekly_loss_limit_pct}%)"
            )
            _log_event(db, "weekly_stop_triggered", state.halted_reason)
            newly_halted = True
        elif settings.max_drawdown_halt_pct > 0 and drawdown_pct >= settings.max_drawdown_halt_pct:
            state.is_halted = True
            state.halted_reason = (
                f"Spadek od szczytu konta przekroczony: -{drawdown_pct:.1f}% "
                f"(limit {settings.max_drawdown_halt_pct}%, szczyt ${state.peak_account_value:,.2f})"
            )
            _log_event(db, "drawdown_stop_triggered", state.halted_reason)
            newly_halted = True
    elif phantom_read and not state.is_halted:
        logger.warning(
            "Pomijam WIDMOWY limit (dzień -%.1f%% / tydzień -%.1f%% / spadek -%.1f%%) — "
            "prawdopodobnie błąd wyceny (pozycje wypadły z sumy konta), nie realna strata",
            day_loss_pct, week_loss_pct, drawdown_pct,
        )

    db.commit()
    db.refresh(state)

    # Rekomendacja #8: gdy AUTO-STOP właśnie się załączył (limit dnia/tygodnia/
    # spadku od szczytu), wyślij natychmiastowy alarm push -- właściciel ma
    # wiedzieć od razu, że automat wstrzymał handel, bez zaglądania do apki.
    # Best-effort: import leniwy (unik cyklu), błąd pusha nigdy nie wywala cyklu.
    if newly_halted:
        try:
            from app.services import push_notifier

            push_notifier.send_alarm(
                db,
                settings,
                title="⛔ Automat ZATRZYMANY (limit strat)",
                body=state.halted_reason or "Przekroczony limit strat — handel automatyczny wstrzymany.",
                tag="risk-halt",
            )
        except Exception:  # pragma: no cover - powiadomienie nie może wywalić kontroli ryzyka
            pass

    return state


def _venue_paused(state: SystemState, venue: str) -> bool:
    if venue == "extended":
        return state.extended_paused
    if venue == "crypto":
        return state.crypto_paused
    return state.is_paused


def can_trade_automated(db: Session, venue: str = "alpaca") -> ValidationResult:
    state = get_state(db)
    if state.is_halted:  # loss-limit auto-stop is account-wide -> blocks both venues
        return ValidationResult(False, state.halted_reason or "Automat zatrzymany przez limit strat")
    if _venue_paused(state, venue):
        return ValidationResult(False, f"Automat ({venue}) zapauzowany ręcznie")
    return ValidationResult(True)


def validate_symbol_whitelist(settings: Settings, symbol: str, whitelist: list[str] | None = None) -> ValidationResult:
    """Whitelist-only check, used for manual trades. Manual overrides
    intentionally skip the pause/halt gate and the automated max_position_pct
    cap (the whole point of a manual override is discretion over size), but
    a fat-fingered or malicious symbol outside the whitelist is never a
    deliberate choice worth allowing."""
    allowed = whitelist if whitelist is not None else settings.whitelist_symbols
    if symbol not in allowed:
        return ValidationResult(False, f"{symbol} nie jest na whiteliście ({allowed})")
    return ValidationResult(True)


def validate_trade(
    *,
    settings: Settings,
    symbol: str,
    action: str,
    size_pct: float,
    whitelist: list[str] | None = None,
) -> ValidationResult:
    allowed = whitelist if whitelist is not None else settings.whitelist_symbols
    if action == "HOLD":
        return ValidationResult(True)

    if symbol not in allowed:
        return ValidationResult(False, f"{symbol} nie jest na whiteliście ({allowed})")

    if size_pct <= 0:
        return ValidationResult(False, "size_pct <= 0, nic do zrobienia")

    if action == "BUY" and size_pct > settings.max_position_pct:
        return ValidationResult(
            False,
            f"Żądana wielkość pozycji {size_pct:.1f}% przekracza limit {settings.max_position_pct}%",
        )

    return ValidationResult(True)


def pause(db: Session, venue: str = "alpaca") -> SystemState:
    state = get_state(db)
    if venue == "extended":
        state.extended_paused = True
    elif venue == "crypto":
        state.crypto_paused = True
    else:
        state.is_paused = True
    db.commit()
    _log_event(db, "manual_pause", f"Automat ({venue}) zatrzymany ręcznie z dashboardu")
    db.refresh(state)
    return state


def resume(db: Session, venue: str = "alpaca") -> SystemState:
    state = get_state(db)
    if venue == "extended":
        # Secondary leg: just unpause it, never touches the account-wide halt.
        state.extended_paused = False
    else:
        # The primary leg (alpaca) AND crypto each unpause themselves and clear
        # the ACCOUNT-WIDE loss-limit halt, re-baselining day/week/peak to the
        # current value on the next cycle -- otherwise a halt re-trips instantly
        # on the stale pre-loss baseline. Crypto MUST be able to clear the halt:
        # after the full pivot it is the only engine the user controls.
        if venue == "crypto":
            state.crypto_paused = False
        else:
            state.is_paused = False
        state.is_halted = False
        state.halted_reason = None
        state.day_start_date = ""
        state.week_start_date = ""
        state.peak_account_value = 0.0
        state.pending_peak_value = 0.0
        state.pending_peak_confirmations = 0
    db.commit()
    _log_event(db, "manual_resume", f"Automat ({venue}) wznowiony ręcznie z dashboardu")
    db.refresh(state)
    return state
