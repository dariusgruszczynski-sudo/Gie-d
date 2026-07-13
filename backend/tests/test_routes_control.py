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
