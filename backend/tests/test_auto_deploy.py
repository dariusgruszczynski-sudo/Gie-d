"""Pełne zainwestowanie + rotacja (auto-deploy): mechaniczny deploy leżącej
gotówki w najlepsze setupy i wymiana najsłabszej pozycji na wyraźnie lepszą,
z Claude jako wetem (nie kupuje nazwy oznaczonej SELL)."""

import pytest

from app.models import Trade, TradeMode
from app.services import market_hours, trading_engine
from app.services.claude_advisor import TradingDecision
from tests.test_trading_engine import (
    FakeAdvisor,
    FakeAlpaca,
    FakeMarketContext,
    FakeNews,
    _session_info,
)


@pytest.fixture(autouse=True)
def _regular_session(monkeypatch):
    """Rynek otwarty + brak earnings (jak w test_trading_engine) — inaczej cykl
    zwróciłby przed torem handlu."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.REGULAR)
    )
    monkeypatch.setattr(trading_engine.earnings_calendar, "get_days_until_earnings", lambda tickers: {})

# Bullish technicals -> entry_confluence score 3 (trend + MACD + RSI momentum).
BULL = {"rsi_14": 60, "macd_signal": "bullish", "sma50_vs_sma200_1h": "above", "volatility_pct_1h": 1.0}


def _auto(settings, **over):
    base = dict(
        auto_deploy_enabled=True,
        mechanical_entries_enabled=True,
        entry_min_score=1,
        auto_deploy_min_cash_usd=25.0,
        auto_deploy_rotation_margin=1,
        auto_deploy_rotation_max_pnl_pct=1.0,
        auto_deploy_max_rotations_per_cycle=2,
    )
    base.update(over)
    return settings.model_copy(update=base)


def test_candidate_score_ok_and_tiebreak(settings):
    s = settings.model_copy(update={"entry_min_score": 2})
    score, mom, ok = trading_engine._candidate_score(s, {"technical": BULL, "change_period_pct": 3.0})
    assert score == 3 and ok is True and mom == 3.0
    # RSI 50 only -> score 1 (momentum), below próg 2 -> not ok
    weak = trading_engine._candidate_score(
        s, {"technical": {"rsi_14": 50, "macd_signal": "bearish", "sma50_vs_sma200_1h": "below"}}
    )
    assert weak[0] == 1 and weak[2] is False


def test_wants_action_only_with_cash_and_slot(db_session, settings):
    s = _auto(settings, max_concurrent_positions=4)
    pf = {
        "usdt_balance": 500.0, "total_value_usdt": 500.0,
        "balances": {"USD": 500.0, "SPY": 0.0, "QQQ": 0.0},
        "prices": {"SPY": 500.0, "QQQ": 400.0},
    }
    assert trading_engine.auto_deploy_wants_action(db_session, s, pf, ["SPY", "QQQ"], "alpaca") is True
    # brak gotówki -> nic do rozmieszczenia
    pf_nocash = {**pf, "usdt_balance": 1.0}
    assert trading_engine.auto_deploy_wants_action(db_session, s, pf_nocash, ["SPY", "QQQ"], "alpaca") is False
    # wyłączony -> nigdy
    off = settings.model_copy(update={"auto_deploy_enabled": False})
    assert trading_engine.auto_deploy_wants_action(db_session, off, pf, ["SPY", "QQQ"], "alpaca") is False


def test_wants_action_periodic_rotation_check_when_full(db_session, settings):
    """Pełny portfel bez gotówki: i tak wymuś cykl, gdy ostatnia analiza starsza
    niż heartbeat — żeby ROTACJA była sprawdzana na czas (niezależnie od newsów)."""
    from datetime import UTC, datetime, timedelta

    from app.services import risk_manager

    s = _auto(settings, max_concurrent_positions=1, full_analysis_every_minutes=60)
    pf = {
        "usdt_balance": 1.0, "total_value_usdt": 800.0,
        "balances": {"USD": 1.0, "SPY": 2.0}, "prices": {"SPY": 400.0},
    }
    st = risk_manager.get_state(db_session)
    st.last_analysis_at = (datetime.now(UTC) - timedelta(minutes=90)).isoformat()
    db_session.commit()
    assert trading_engine.auto_deploy_wants_action(db_session, s, pf, ["SPY"], "alpaca") is True
    # świeża analiza -> nie wymuszaj (unikamy zbędnych cykli)
    st.last_analysis_at = datetime.now(UTC).isoformat()
    db_session.commit()
    assert trading_engine.auto_deploy_wants_action(db_session, s, pf, ["SPY"], "alpaca") is False


def test_auto_deploy_buys_when_claude_holds(db_session, settings, monkeypatch):
    """Sedno prośby: gotówka NIE leży — bot sam kupuje confluentny setup, mimo że
    Claude powiedział HOLD."""
    monkeypatch.setattr(trading_engine, "compute_technical_indicators", lambda closes: dict(BULL))
    s = _auto(settings, max_concurrent_positions=4, max_position_pct=90.0, risk_per_trade_pct=0.0,
              auto_deploy_max_position_pct=100.0)
    broker = FakeAlpaca(prices={"SPY": 500.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "czekam"))

    trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, FakeMarketContext())

    buys = [o for o in broker.orders if o.side == "BUY"]
    assert buys, "auto-deploy powinien kupić mimo HOLD od Claude"
    assert broker.balances["USD"] < 1000.0


def test_auto_deploy_spreads_across_names(db_session, settings, monkeypatch):
    """Anty-koncentracja: przy auto_deploy_max_position_pct=25 gotówka rozkłada się
    na kilka nazw, nie wpada w jedną. Z 4 confluentnymi nazwami -> ~4 wejścia."""
    monkeypatch.setattr(trading_engine, "compute_technical_indicators", lambda closes: dict(BULL))
    s = _auto(
        settings,
        trading_whitelist="SPY,QQQ,AAPL,NVDA",
        max_concurrent_positions=8,
        max_position_pct=90.0,
        risk_per_trade_pct=0.0,
        auto_deploy_max_position_pct=25.0,
    )
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "QQQ": 400.0, "AAPL": 200.0, "NVDA": 100.0},
        balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "AAPL": 0.0, "NVDA": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "czekam"))

    trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, FakeMarketContext())

    buys = [o for o in broker.orders if o.side == "BUY"]
    # Rozłożone na wiele nazw (nie jedna skoncentrowana pozycja); żadne wejście
    # nie przekracza ~25% konta (+ mały bufor na kolejność/round).
    assert len({o.symbol for o in buys}) >= 3
    assert all(o.usdt_value <= 260.0 for o in buys)


def test_auto_deploy_respects_claude_sell_veto(db_session, settings, monkeypatch):
    """Claude jako weto: nazwa oznaczona SELL nie jest kupowana przez auto-deploy."""
    monkeypatch.setattr(trading_engine, "compute_technical_indicators", lambda closes: dict(BULL))
    s = _auto(settings, trading_whitelist="SPY", max_concurrent_positions=4)
    broker = FakeAlpaca(prices={"SPY": 500.0}, balances={"USD": 1000.0, "SPY": 0.0})
    advisor = FakeAdvisor(TradingDecision("SELL", "SPY", 100, 0.8, "unikaj"))

    trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, FakeMarketContext())

    assert not any(o.side == "BUY" for o in broker.orders)


class SeriesAlpaca(FakeAlpaca):
    """Broker z osobną serią świec per symbol — pozwala policzyć REALNE wskaźniki
    (rosnąca seria => mocny setup, płaska => słaby)."""

    def __init__(self, series, prices, balances):
        super().__init__(prices=prices, balances=balances)
        self.series = series

    def get_klines(self, symbol, interval="1h", limit=24):
        closes = self.series[symbol][-limit:]
        return [[0, c, c, c, c, "1"] for c in closes]


def test_auto_rotation_swaps_weakest_for_better(db_session, settings):
    """Przy pełnym portfelu i braku gotówki: sprzedaje najsłabszą (płaską) pozycję
    i wchodzi w wyraźnie lepszy (rosnący) setup."""
    s = _auto(
        settings,
        trading_whitelist="SPY,QQQ",
        max_concurrent_positions=1,   # portfel „pełny" przy 1 pozycji
        min_hold_minutes=0,
        risk_per_trade_pct=0.0,
        regime_gate_enabled=False,
    )
    series = {"SPY": [400.0] * 200, "QQQ": [100.0 + i for i in range(200)]}
    broker = SeriesAlpaca(
        series=series,
        prices={"SPY": 400.0, "QQQ": 299.0},
        balances={"USD": 1.0, "SPY": 2.0, "QQQ": 0.0},  # brak gotówki, trzyma SPY
    )
    # Historia: SPY kupione @400 (baza -> pnl ~0, kwalifikuje się do wymiany).
    db_session.add(Trade(symbol="SPY", side="BUY", quantity=2.0, price=400.0,
                         usdt_value=800.0, mode=TradeMode.LIVE, is_manual=False, venue="alpaca"))
    db_session.commit()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "czekam"))

    trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, FakeMarketContext())

    sold_spy = [o for o in broker.orders if o.side == "SELL" and o.symbol == "SPY"]
    bought_qqq = [o for o in broker.orders if o.side == "BUY" and o.symbol == "QQQ"]
    assert sold_spy, "rotacja powinna sprzedać najsłabszą pozycję (SPY)"
    assert bought_qqq, "rotacja powinna wejść w lepszy setup (QQQ)"
