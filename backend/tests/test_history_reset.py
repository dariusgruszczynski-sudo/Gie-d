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


def test_kraken_full_cutover_purges_alpaca_keeps_crypto_and_lessons(db_session, monkeypatch):
    """PEŁNE PRZEPIĘCIE: wycina erę Alpaca/extended (snapshoty/decyzje/transakcje),
    re-bazuje ryzyko i zdejmuje widmowy halt, ale ZOSTAWIA dane krypto (otwarta
    pozycja) i lekcje. Idempotentny po znaczniku wersji."""
    from app.models import PortfolioSnapshot, Trade
    from app.services.history_reset import _CUTOVER_VERSION, kraken_full_cutover

    # crypto_venue musi być 'kraken' (domyślne), inaczej cutover pomija.
    state = risk_manager.get_state(db_session)
    state.is_halted = True
    state.halted_reason = "Spadek od szczytu konta przekroczony: -100.0% (limit 55.0%, szczyt $840,728.19)"
    state.peak_account_value = 840_728.19
    state.lessons_json = _LESSONS
    state.kraken_cutover_at = ""
    # Decyzje: 1 akcyjna (do wycięcia) + 1 krypto (zostaje).
    d_alp = Decision(symbol="SPY", action=TradeAction.BUY, size_pct=5.0, confidence=1.0,
                     reasoning="alp", triggered_by=TriggerType.SCHEDULED_DAILY, executed=True, venue="alpaca")
    d_cry = Decision(symbol="NIGHT/EUR", action=TradeAction.BUY, size_pct=10.0, confidence=1.0,
                     reasoning="cry", triggered_by=TriggerType.NEWS_EVENT, executed=True, venue="crypto")
    db_session.add_all([d_alp, d_cry])
    db_session.flush()
    db_session.add_all([
        Trade(symbol="SPY", side="BUY", quantity=1.0, price=100.0, usdt_value=100.0, mode="paper", venue="alpaca", decision_id=d_alp.id),
        Trade(symbol="NIGHT/EUR", side="BUY", quantity=272.0, price=0.044, usdt_value=11.98, mode="live", venue="crypto", decision_id=d_cry.id),
        PortfolioSnapshot(total_value_usdt=840000.0, usdt_balance=840000.0, venue="alpaca"),
        PortfolioSnapshot(total_value_usdt=119.82, usdt_balance=107.75, venue="crypto"),
    ])
    db_session.commit()

    r = kraken_full_cutover(db_session)
    assert r is not None and r["trades"] == 1 and r["snapshots"] == 1
    s = risk_manager.get_state(db_session)
    assert s.is_halted is False and s.halted_reason is None            # widmowy halt zdjęty
    assert s.peak_account_value == 0.0                                 # ryzyko re-bazowane
    assert s.crypto_paused is False                                    # krypto zostaje aktywne
    assert s.lessons_json == _LESSONS                                  # lekcje zachowane
    # Akcje wycięte, krypto zostaje.
    assert db_session.query(Trade).filter(Trade.venue == "alpaca").count() == 0
    assert db_session.query(Trade).filter(Trade.venue == "crypto").count() == 1
    assert db_session.query(Decision).filter(Decision.venue == "alpaca").count() == 0
    assert db_session.query(Decision).filter(Decision.venue == "crypto").count() == 1
    assert db_session.query(PortfolioSnapshot).filter(PortfolioSnapshot.venue == "alpaca").count() == 0
    assert db_session.query(PortfolioSnapshot).filter(PortfolioSnapshot.venue == "crypto").count() == 1
    assert s.kraken_cutover_at == _CUTOVER_VERSION
    # Idempotentny: drugie wywołanie nic nie robi.
    assert kraken_full_cutover(db_session) is None
