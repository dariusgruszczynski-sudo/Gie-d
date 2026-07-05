from app.services import scorecard, trading_engine


def _buy(db, settings, broker, symbol, usdt):
    trading_engine.execute_manual_trade(db, settings, broker, symbol=symbol, side="BUY", usdt_amount=usdt)


def test_benchmark_baseline_set_once_and_alpha_tracks(db_session, settings):
    # settings.benchmark_symbol defaults to SPY.
    portfolio_start = {"total_value_usdt": 1000.0, "prices": {"SPY": 100.0, "QQQ": 400.0}}
    scorecard.update_benchmark_baseline(db_session, settings, portfolio_start)

    # SPY doubles; if we'd just held, our value would double too.
    portfolio_now = {"total_value_usdt": 1500.0, "prices": {"SPY": 200.0, "QQQ": 400.0}}
    card = scorecard.compute_scorecard(db_session, settings, portfolio_now)

    assert card["benchmark_value"] == 2000.0  # 1000 * (200/100)
    # We're at 1500 vs 2000 buy-and-hold -> underperforming by 500 (-25%).
    assert card["alpha_usd"] == -500.0
    assert card["alpha_pct"] == -25.0


def test_baseline_not_overwritten_on_later_cycles(db_session, settings):
    scorecard.update_benchmark_baseline(db_session, settings, {"total_value_usdt": 1000.0, "prices": {"SPY": 100.0}})
    scorecard.update_benchmark_baseline(db_session, settings, {"total_value_usdt": 1200.0, "prices": {"SPY": 150.0}})
    card = scorecard.compute_scorecard(db_session, settings, {"total_value_usdt": 1200.0, "prices": {"SPY": 150.0}})
    # Baseline stayed at 100/1000, so benchmark now = 1000 * 150/100 = 1500.
    assert card["benchmark_value"] == 1500.0


def test_realized_pnl_and_win_rate(db_session, settings):
    from tests.test_trading_engine import FakeAlpaca

    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 10000.0, "SPY": 0.0, "QQQ": 0.0})
    _buy(db_session, settings, broker, "SPY", 100.0)  # 1 share @100
    broker.prices["SPY"] = 120.0
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="SELL", quantity=1.0)  # +20 win

    _buy(db_session, settings, broker, "QQQ", 400.0)  # 1 share @400
    broker.prices["QQQ"] = 380.0
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="QQQ", side="SELL", quantity=1.0)  # -20 loss

    card = scorecard.compute_scorecard(db_session, settings, {"total_value_usdt": 10000.0, "prices": {"SPY": 120.0}})
    assert card["realized_pnl_usd"] == 0.0  # +20 and -20
    assert card["wins"] == 1
    assert card["losses"] == 1
    assert card["win_rate_pct"] == 50.0


def test_scorecard_degrades_without_baseline(db_session, settings):
    card = scorecard.compute_scorecard(db_session, settings, {"total_value_usdt": 0.0, "prices": {}})
    assert card["benchmark_value"] is None
    assert card["alpha_pct"] is None
    assert card["win_rate_pct"] is None
