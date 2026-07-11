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

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import RiskEvent, SystemState


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

    if not state.is_halted:
        if day_loss_pct >= settings.daily_loss_limit_pct:
            state.is_halted = True
            state.halted_reason = (
                f"Dzienny limit strat przekroczony: -{day_loss_pct:.1f}% "
                f"(limit {settings.daily_loss_limit_pct}%)"
            )
            _log_event(db, "daily_stop_triggered", state.halted_reason)
        elif week_loss_pct >= settings.weekly_loss_limit_pct:
            state.is_halted = True
            state.halted_reason = (
                f"Tygodniowy limit strat przekroczony: -{week_loss_pct:.1f}% "
                f"(limit {settings.weekly_loss_limit_pct}%)"
            )
            _log_event(db, "weekly_stop_triggered", state.halted_reason)

    db.commit()
    db.refresh(state)
    return state


def _venue_paused(state: SystemState, venue: str) -> bool:
    return state.crypto_paused if venue == "crypto" else state.is_paused


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
    if venue == "crypto":
        state.crypto_paused = True
    else:
        state.is_paused = True
    db.commit()
    _log_event(db, "manual_pause", f"Automat ({venue}) zatrzymany ręcznie z dashboardu")
    db.refresh(state)
    return state


def resume(db: Session, venue: str = "alpaca") -> SystemState:
    state = get_state(db)
    if venue == "crypto":
        state.crypto_paused = False
    else:
        state.is_paused = False
        # The loss-limit halt is account-wide; clear it on the main (Alpaca)
        # resume and force the day/week loss baselines to re-initialize to the
        # current portfolio value on the next update_portfolio_value() call --
        # otherwise a halt tripped earlier today re-trips itself on the very
        # next cycle, since the old (pre-loss) baseline is still in place.
        state.is_halted = False
        state.halted_reason = None
        state.day_start_date = ""
        state.week_start_date = ""
    db.commit()
    _log_event(db, "manual_resume", f"Automat ({venue}) wznowiony ręcznie z dashboardu")
    db.refresh(state)
    return state
