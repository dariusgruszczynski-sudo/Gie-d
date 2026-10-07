"""SYMULACJA mechanizmów P(zysk) na SYNTETYCZNYCH świecach (dane giełd są
blokowane w tym środowisku -> realny backtest odpala się na prodzie:
`run_backtest.py --venue crypto`). Tu przepuszczamy run_cycle przez
kontrolowane serie cen i sprawdzamy, że NOWE bramki wejścia działają:
wybicie (Donchian) + siła trendu (ADX) + reżim HTF wpuszczają w trendzie,
a blokują w rynku bocznym / risk-off; piramidowanie dokłada do wygranej.

Uruchom z narracją:  pytest tests/test_sim_mechanisms.py -s
"""

from app.models import Trade, TradeMode
from app.services import market_hours, trading_engine
from app.services.claude_advisor import TradingDecision
from tests.test_auto_deploy import SeriesAlpaca
from tests.test_trading_engine import FakeAdvisor, FakeMarketContext, FakeNews, _session_info

BULL = {"rsi_14": 60, "macd_signal": "bullish", "sma50_vs_sma200_1h": "above", "volatility_pct_1h": 1.0}


def _open_market(mp):
    mp.setattr(trading_engine.market_hours, "get_session_info", lambda b: _session_info(market_hours.REGULAR))
    mp.setattr(trading_engine.earnings_calendar, "get_days_until_earnings", lambda t: {})
    mp.setattr(trading_engine, "compute_technical_indicators", lambda closes: dict(BULL))


def _sim_settings(settings, **over):
    base = dict(
        auto_deploy_enabled=True, mechanical_entries_enabled=True, entry_min_score=1,
        auto_deploy_min_cash_usd=25.0, risk_per_trade_pct=0.0, max_position_pct=90.0,
        auto_deploy_max_position_pct=40.0, max_concurrent_positions=8, min_hold_minutes=0,
        trading_whitelist="SPY,QQQ",
        # 10 mechanizmów ON (strona wejść/reżimu/ryzyka)
        regime_filter_enabled=True, regime_filter_symbol="SPY", regime_filter_ma_period=50,
        breakout_entry_enabled=True, breakout_lookback=20, min_adx=12.0,
        pyramid_enabled=True, pyramid_min_gain_pct=5.0, pyramid_max_position_pct=40.0,
        max_total_exposure_pct=0.0, loss_streak_pause=0,
    )
    base.update(over)
    return settings.model_copy(update=base)


def test_sim_entry_passes_in_uptrend_breakout(db_session, settings, monkeypatch):
    """TREND + WYBICIE: SPY (proxy reżimu) i QQQ w mocnym trendzie, bieżąca cena
    to nowe maksimum -> reżim risk-on, ADX wysoki, wybicie -> WCHODZI."""
    _open_market(monkeypatch)
    s = _sim_settings(settings)
    # rosnące serie: nowe maksimum na końcu (wybicie), silny jednokierunkowy trend (ADX wysoki)
    series = {"SPY": [300.0 + i for i in range(200)], "QQQ": [200.0 + i for i in range(200)]}
    broker = SeriesAlpaca(series=series,
                          prices={"SPY": series["SPY"][-1], "QQQ": series["QQQ"][-1]},
                          balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.run_cycle(db_session, s, broker, FakeNews(),
                             FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "czekam")), FakeMarketContext())
    buys = sorted({o.symbol for o in broker.orders if o.side == "BUY"})
    print(f"\n[SYM-1 trend+wybicie] kupione: {buys}  | zlecenia: {len(broker.orders)}")
    assert buys, "w trendzie z wybiciem i wysokim ADX bot powinien wejść"


def test_sim_entry_blocked_in_risk_off_regime(db_session, settings, monkeypatch):
    """REŻIM RISK-OFF: SPY (proxy) pod swoją SMA50 -> bramka reżimu HTF wstrzymuje
    WSZYSTKIE nowe wejścia, choćby QQQ ładnie rósł. Bot siedzi w gotówce."""
    _open_market(monkeypatch)
    s = _sim_settings(settings)
    # SPY spada (cena < SMA50 -> risk-off); QQQ rośnie (sam w sobie kuszący)
    series = {"SPY": [400.0 - i for i in range(200)], "QQQ": [200.0 + i for i in range(200)]}
    broker = SeriesAlpaca(series=series,
                          prices={"SPY": series["SPY"][-1], "QQQ": series["QQQ"][-1]},
                          balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.run_cycle(db_session, s, broker, FakeNews(),
                             FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "czekam")), FakeMarketContext())
    buys = [o for o in broker.orders if o.side == "BUY"]
    print(f"\n[SYM-2 risk-off] kupione: {sorted({o.symbol for o in buys})}  (oczekiwane: puste)")
    assert not buys, "reżim risk-off powinien wstrzymać nowe wejścia"


def test_sim_pyramiding_adds_to_winner(db_session, settings, monkeypatch):
    """PIRAMIDOWANIE: trzymamy wygrywające QQQ (kupione @200, teraz 260 = +30%),
    cena robi nowe wybicie -> bot DOKŁADA do zwycięzcy (nie do straty)."""
    _open_market(monkeypatch)
    # wąski portfel, ale piramida zwolniona z limitu równoległych pozycji
    s = _sim_settings(settings, trading_whitelist="SPY,QQQ", max_concurrent_positions=2,
                      pyramid_max_position_pct=80.0, auto_deploy_max_position_pct=40.0)
    # QQQ silny trend do nowego maksimum (260); SPY rośnie (reżim risk-on)
    series = {"SPY": [300.0 + i for i in range(200)], "QQQ": [200.0 + i * 0.3 for i in range(199)] + [260.0]}
    broker = SeriesAlpaca(series=series,
                          prices={"SPY": series["SPY"][-1], "QQQ": 260.0},
                          balances={"USD": 500.0, "SPY": 0.0, "QQQ": 1.0})  # trzyma 1 QQQ
    # historia: QQQ kupione @200 -> baza 200, teraz 260 = +30% (wygrany)
    db_session.add(Trade(symbol="QQQ", side="BUY", quantity=1.0, price=200.0, usdt_value=200.0,
                         mode=TradeMode.LIVE, is_manual=False, venue="alpaca"))
    db_session.commit()
    trading_engine.run_cycle(db_session, s, broker, FakeNews(),
                             FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "czekam")), FakeMarketContext())
    qqq_buys = [o for o in broker.orders if o.side == "BUY" and o.symbol == "QQQ"]
    print(f"\n[SYM-3 piramida] dokładki QQQ: {len(qqq_buys)}  (oczekiwane: >=1)")
    assert qqq_buys, "piramidowanie powinno dołożyć do wygrywającego QQQ na nowym wybiciu"
