import json

from app.services import risk_manager, self_review, trading_engine
from tests.test_trading_engine import FakeAlpaca


def _make_trade(db, settings, symbol="SPY", side="BUY"):
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 10000.0, "SPY": 5.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db, settings, broker, symbol=symbol, side=side, usdt_amount=100.0)


def test_self_review_stores_parsed_lessons_and_marks_date(db_session, settings):
    _make_trade(db_session, settings)

    def fake_generate(s, prompt):
        assert "TRANSAKCJE" in prompt and "SPY" in prompt
        return "- MSTR breakouty konczyly sie stop-lossem, unikac\n- Wejscia na GLD przy rosnacym VIX dzialaly\n", 0.01, 120, 60

    lessons = self_review.run_self_review(db_session, settings, generate=fake_generate)

    assert len(lessons) == 2
    assert lessons[0]["lesson"].startswith("MSTR breakouty")
    state = risk_manager.get_state(db_session)
    assert state.last_self_review_date != ""
    assert json.loads(state.lessons_json)[0]["lesson"].startswith("MSTR")


def test_self_review_failure_keeps_previous_lessons(db_session, settings):
    _make_trade(db_session, settings)
    state = risk_manager.get_state(db_session)
    state.lessons_json = json.dumps([{"date": "2026-07-01", "lesson": "Stara lekcja o trzymaniu SPY"}])
    db_session.commit()

    def boom(s, prompt):
        raise RuntimeError("API down")

    lessons = self_review.run_self_review(db_session, settings, generate=boom)

    assert len(lessons) == 1
    assert lessons[0]["lesson"] == "Stara lekcja o trzymaniu SPY"


def test_self_review_skips_without_trades(db_session, settings):
    called = {"n": 0}

    def fake_generate(s, prompt):
        called["n"] += 1
        return "- cokolwiek", 0.01, 10, 5

    lessons = self_review.run_self_review(db_session, settings, generate=fake_generate)

    assert lessons == []
    assert called["n"] == 0  # no Claude spend when there's nothing to review


def test_lessons_capped_at_max(db_session, settings):
    _make_trade(db_session, settings)
    state = risk_manager.get_state(db_session)
    state.lessons_json = json.dumps(
        [{"date": "2026-07-01", "lesson": f"Stara lekcja numer {i}"} for i in range(self_review.MAX_LESSONS_KEPT)]
    )
    db_session.commit()

    def fake_generate(s, prompt):
        return "- Nowa swieza lekcja z tego tygodnia o rotacji", 0.01, 30, 15

    lessons = self_review.run_self_review(db_session, settings, generate=fake_generate)

    assert len(lessons) == self_review.MAX_LESSONS_KEPT
    assert lessons[0]["lesson"].startswith("Nowa swieza")


def test_lessons_reach_claude_decision_context(db_session, settings):
    from app.services.claude_advisor import TradingDecision
    from tests.test_trading_engine import FakeAdvisor, FakeNews

    state = risk_manager.get_state(db_session)
    state.lessons_json = json.dumps([{"date": "2026-07-04", "lesson": "Nie kupuj MSTR po dwoch stop-lossach"}])
    db_session.commit()

    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Czekam."))
    trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    assert advisor.last_kwargs["performance_context"]["lessons_learned"] == [
        "Nie kupuj MSTR po dwoch stop-lossach"
    ]


def test_playbook_seed_is_fed_to_claude_context(db_session, settings):
    """Stała baza zachowań (playbook) trafia do kontekstu decyzji Claude jako
    your_performance.playbook -- niezależnie od tego, czy są już nauczone lekcje."""
    from app.services import playbook, trading_engine

    portfolio = {"total_value_usdt": 1000.0, "usdt_balance": 1000.0, "balances": {}, "prices": {}}
    ctx = trading_engine.build_performance_context(db_session, settings, portfolio, venue="alpaca", whitelist=["SPY"])
    assert ctx["playbook"] == playbook.SEED_PLAYBOOK
    assert len(ctx["playbook"]) >= 10  # realny playbook, nie pusty placeholder
