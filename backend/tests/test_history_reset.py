"""Reset do czysta (history_reset.reset_tracking): czyści log + zdejmuje HALT +
re-bazuje szczyt, ZACHOWUJE lekcje domyślnie, kasuje je tylko z wipe_lessons."""

from app.models import Decision, TradeAction, TriggerType
from app.services import risk_manager
from app.services.history_reset import reset_tracking

_LESSONS = '[{"date": "2026-10-14", "lesson": "force-trade/serial re-entry krwawi"}]'


def _seed(db):
    state = risk_manager.get_state(db)
    state.is_halted = True
    state.halted_reason = "Dzienny limit strat przekroczony"
    state.is_paused = False
    state.crypto_paused = False
    state.peak_account_value = 99753.0
    state.lessons_json = _LESSONS
    db.add(Decision(symbol="BTC/USD", action=TradeAction.BUY, size_pct=10.0, confidence=1.0,
                    reasoning="seed", triggered_by=TriggerType.SCHEDULED_DAILY, executed=True, venue="crypto"))
    db.commit()


def test_reset_keeps_lessons_clears_halt_rebaselines_peak(db_session):
    _seed(db_session)
    r = reset_tracking(db_session)
    assert r["decisions"] >= 1 and r["lessons_wiped"] is False
    s = risk_manager.get_state(db_session)
    assert s.is_halted is False and s.halted_reason is None      # HALT zdjęty
    assert s.is_paused is True and s.crypto_paused is True        # silniki w STOP
    assert s.peak_account_value == 0.0                           # szczyt re-bazuje
    assert s.lessons_json == _LESSONS                            # NAUKA zachowana
    assert db_session.query(Decision).count() == 0              # log wyczyszczony


def test_reset_wipe_lessons_flag_erases_learning(db_session):
    _seed(db_session)
    reset_tracking(db_session, wipe_lessons=True)
    assert risk_manager.get_state(db_session).lessons_json == "[]"
