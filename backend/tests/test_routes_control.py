import pytest
from fastapi import HTTPException

from app.api import routes_control
from tests.test_trading_engine import FakeAlpaca


def test_sell_all_sells_exact_held_qty(db_session, settings, monkeypatch):
    """SELL ALL liquidates the EXACT quantity the account holds (read live from
    the broker) -- even for an off-whitelist adopted name -- so there's no
    'insufficient qty' from a dollar amount rounding to more shares than held."""
    broker = FakeAlpaca(prices={"XLE": 56.0, "SPY": 500.0}, balances={"USD": 100.0, "XLE": 1.5})
    monkeypatch.setattr(routes_control, "_broker_for", lambda venue, s: (broker, s.whitelist_symbols, False))

    trade = routes_control.sell_all(symbol="XLE", venue="alpaca", db=db_session, settings=settings)

    assert trade["symbol"] == "XLE"
    assert trade["side"] == "SELL"
    assert abs(trade["quantity"] - 1.5) < 1e-9  # the full held qty
    assert broker.balances["XLE"] < 1e-9  # position fully closed


def test_sell_all_404_when_nothing_held(db_session, settings, monkeypatch):
    broker = FakeAlpaca(prices={"XLE": 56.0}, balances={"USD": 100.0})
    monkeypatch.setattr(routes_control, "_broker_for", lambda venue, s: (broker, s.whitelist_symbols, False))

    with pytest.raises(HTTPException) as ei:
        routes_control.sell_all(symbol="XLE", venue="alpaca", db=db_session, settings=settings)
    assert ei.value.status_code == 404


def test_set_plan_and_widget_metric_persist(db_session):
    from app.api import routes_control
    from app.services import risk_manager

    routes_control.set_plan(monthly_deposit=300, goal=20000, db=db_session)
    routes_control.set_widget_metric(metric="day", db=db_session)
    state = risk_manager.get_state(db_session)
    assert state.monthly_deposit_plan == 300.0
    assert state.goal_amount == 20000.0
    assert state.widget_metric == "day"


def test_set_plan_clamps_negative_to_zero(db_session):
    from app.api import routes_control

    out = routes_control.set_plan(monthly_deposit=-5, goal=-1, db=db_session)
    assert out == {"monthly_deposit": 0.0, "goal": 0.0}


def test_widget_primary_follows_metric(db_session, settings):
    import json as _json

    from app.api.routes_dashboard import get_widget
    from app.models import PortfolioSnapshot
    from app.services import risk_manager

    db_session.add(PortfolioSnapshot(
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        total_value_usdt=1200.0, usdt_balance=900.0,
        balances_json=_json.dumps({"SPY": 3.0}), prices_json=_json.dumps({"SPY": 100.0}), venue="alpaca"))
    risk_manager.get_state(db_session).widget_metric = "account"
    db_session.commit()

    body = get_widget(db=db_session, settings=settings)
    assert body["widget_metric"] == "account"
    assert body["primary"]["metric"] == "account"
    assert body["primary"]["label"] == "Na koncie"
