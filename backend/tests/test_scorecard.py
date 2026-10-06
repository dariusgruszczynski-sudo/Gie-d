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


def test_crypto_scorecard_benchmarks_btc_and_counts_crypto_trades(db_session, settings):
    """Krypto bije „trzymaj BTC" (nie SPY) i liczy trafność z transakcji krypto.
    Baseline bierze się z najstarszego snapshotu krypto, więc nie koliduje z akcjami."""
    import json

    from app.models import PortfolioSnapshot
    from tests.test_trading_engine import FakeAlpaca

    # Najstarszy snapshot krypto = punkt odniesienia: BTC @50k, konto $1000.
    db_session.add(PortfolioSnapshot(
        total_value_usdt=1000.0, usdt_balance=1000.0,
        balances_json="{}", prices_json=json.dumps({"BTC/USD": 50000.0}),
        failed_symbols_json="[]", venue="crypto",
    ))
    db_session.commit()

    crypto_settings = settings.model_copy(update={"crypto_enabled": True})
    broker = FakeAlpaca(prices={"BTC/USD": 50000.0}, balances={"USD": 10000.0})
    trading_engine.execute_manual_trade(db_session, crypto_settings, broker, symbol="BTC/USD", side="BUY", usdt_amount=500.0, venue="crypto", whitelist=["BTC/USD"])
    broker.prices["BTC/USD"] = 60000.0
    held = trading_engine.compute_portfolio(db_session, crypto_settings, broker, venue="crypto", whitelist=["BTC/USD"])
    trading_engine.execute_manual_trade(
        db_session, crypto_settings, broker, symbol="BTC/USD", side="SELL",
        quantity=held["balances"]["BTC/USD"], venue="crypto", whitelist=["BTC/USD"],
    )  # +~20% win

    # BTC podwaja się do 100k: trzymanie dałoby 1000*(100k/50k)=2000.
    card = scorecard.compute_scorecard(
        db_session, crypto_settings, {"total_value_usdt": 1200.0, "prices": {"BTC/USD": 100000.0}}, venue="crypto",
    )
    assert card["benchmark_symbol"] == "BTC/USD"
    assert card["benchmark_value"] == 2000.0
    assert card["wins"] == 1
    assert card["losses"] == 0
    assert card["win_rate_pct"] == 100.0


def test_crypto_stats_exclude_legacy_slashless_trades(db_session, settings):
    """Zaszłości: starsze krypto-trejdy w formacie slash-less (np. 'ADAUSD' z innego
    eksperymentu) NIE mogą zanieczyszczać staty żywego runu (pary 'BTC/USD')."""
    from datetime import UTC, datetime, timedelta

    from app.models import Trade, TradeMode

    t0 = datetime(2026, 10, 4, tzinfo=UTC)
    # Legacy slash-less: kup+sprzedaj ze STRATĄ (nie powinno się liczyć).
    db_session.add(Trade(timestamp=t0, symbol="ADAUSD", side="BUY", quantity=10, price=1.0, usdt_value=10.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=t0 + timedelta(hours=1), symbol="ADAUSD", side="SELL", quantity=10, price=0.5, usdt_value=5.0, mode=TradeMode.LIVE, venue="crypto"))
    # Bieżący run (para): kup+sprzedaj z ZYSKIEM (jedyne, co ma się liczyć).
    db_session.add(Trade(timestamp=t0 + timedelta(hours=2), symbol="BTC/USD", side="BUY", quantity=0.01, price=60000.0, usdt_value=600.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(Trade(timestamp=t0 + timedelta(hours=3), symbol="BTC/USD", side="SELL", quantity=0.01, price=66000.0, usdt_value=660.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()

    realized, wins, losses = scorecard._walk_realized(db_session, venue="crypto")
    assert wins == 1 and losses == 0  # tylko zamknięcie BTC/USD
    assert round(realized, 2) == 60.0  # +$60 z BTC, bez -$5 z ADA
    hist = scorecard.realized_history(db_session, venue="crypto")
    assert [h["symbol"] for h in hist] == ["BTC/USD"]  # legacy ADAUSD pominięty


def test_scorecard_degrades_without_baseline(db_session, settings):
    card = scorecard.compute_scorecard(db_session, settings, {"total_value_usdt": 0.0, "prices": {}})
    assert card["benchmark_value"] is None
    assert card["alpha_pct"] is None
    assert card["win_rate_pct"] is None
