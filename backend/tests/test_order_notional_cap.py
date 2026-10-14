"""Twardy sufit notional/zlecenie (Alpaca odrzuca > $200k): BUY i SELL dzielone
na kawałki ≤ max_order_notional_usd, zamiast dostać 403 i nie wejść/nie wyjść."""

from app.services import trading_engine
from tests.test_trading_engine import FakeAlpaca


def _settings(settings):
    return settings.model_copy(update={"max_order_notional_usd": 190000.0})


def test_buy_notional_clamped_below_alpaca_limit(db_session, settings, monkeypatch):
    monkeypatch.setattr(trading_engine.email_reporter, "send_trade_alert", lambda *a, **k: None)
    monkeypatch.setattr(trading_engine.push_notifier, "send_trade_push", lambda *a, **k: None)
    broker = FakeAlpaca(prices={"SPY": 500.0}, balances={"USD": 1_000_000.0, "SPY": 0.0})
    pf = {"usdt_balance": 1_000_000.0, "prices": {"SPY": 500.0}, "balances": {"USD": 1_000_000.0}}

    trade = trading_engine._execute_trade(
        db=db_session, broker=broker, settings=_settings(settings), symbol="SPY",
        action="BUY", size_pct=100.0, portfolio=pf, decision=None, is_manual=True,
    )
    # 100% z $1M = $1M, ale zlecenie przycięte do $190k (pod limit Alpaki $200k).
    assert trade.usdt_value <= 190000.0 + 1e-6
    assert abs(trade.usdt_value - 190000.0) < 1.0


def test_sell_notional_clamped_below_alpaca_limit(db_session, settings, monkeypatch):
    monkeypatch.setattr(trading_engine.email_reporter, "send_trade_alert", lambda *a, **k: None)
    monkeypatch.setattr(trading_engine.push_notifier, "send_trade_push", lambda *a, **k: None)
    broker = FakeAlpaca(prices={"SPY": 500.0}, balances={"USD": 0.0, "SPY": 1000.0})
    # Pozycja 1000 × $500 = $500k; pełne wyjście przycięte do $190k w tym cyklu.
    pf = {"usdt_balance": 0.0, "prices": {"SPY": 500.0}, "balances": {"SPY": 1000.0}}

    trade = trading_engine._execute_trade(
        db=db_session, broker=broker, settings=_settings(settings), symbol="SPY",
        action="SELL", size_pct=100.0, portfolio=pf, decision=None, is_manual=True,
    )
    assert trade.usdt_value <= 190000.0 + 1e-6
    assert abs(trade.usdt_value - 190000.0) < 1.0
