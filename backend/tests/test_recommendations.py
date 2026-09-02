"""Testy rekomendacji z audytu 2026-09-02 (#1-#10 + B + C).

Skupione, jednostkowe testy nowych zachowań: dławienie re-analizy (#3),
sizing conviction adaptowany przewagą (#4), zlecenia marketable-LIMIT na
nazwach o szerokim spreadzie (B), linia przewagi w raporcie tygodnia (#6),
alarm push przy auto-halcie (#8) i dziennik decyzji w historii (C).
"""

from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.models import Trade, TradeMode
from app.services import push_notifier, risk_manager, scorecard, trading_engine


def _s(**over) -> Settings:
    base = dict(
        anthropic_api_key="k",
        alpaca_api_key="k",
        alpaca_api_secret="s",
        trading_whitelist="SPY,QQQ",
        stats_epoch_default="",
    )
    base.update(over)
    return Settings(_env_file=None, **base)


def _buy(db, sym, qty, price, ts):
    db.add(Trade(timestamp=ts, symbol=sym, side="BUY", quantity=qty, price=price,
                 usdt_value=qty * price, mode=TradeMode.LIVE, venue="alpaca"))


def _sell(db, sym, qty, price, ts):
    db.add(Trade(timestamp=ts, symbol=sym, side="SELL", quantity=qty, price=price,
                 usdt_value=qty * price, mode=TradeMode.LIVE, venue="alpaca"))


# --- #4: conviction skalowany świeżą przewagą -----------------------------

def test_conviction_edge_scale_bounds():
    s = _s(conviction_edge_adaptive_enabled=True, conviction_edge_min_payoff=2.0, conviction_edge_full_payoff=4.0)
    assert trading_engine.conviction_edge_scale(s, 1.5) == 0.0     # słaba przewaga -> brak wzmacniania
    assert trading_engine.conviction_edge_scale(s, 4.0) == 1.0     # mocna -> pełne
    assert trading_engine.conviction_edge_scale(s, 3.0) == 0.5     # w połowie
    assert trading_engine.conviction_edge_scale(s, None) == 1.0    # brak danych -> bez zmiany


def test_conviction_edge_scale_disabled_is_neutral():
    s = _s(conviction_edge_adaptive_enabled=False)
    assert trading_engine.conviction_edge_scale(s, 1.0) == 1.0


def test_conviction_multiplier_shrinks_on_weak_edge():
    s = _s(conviction_sizing_enabled=True, conviction_size_max_mult=2.0,
           min_buy_confidence=0.6, progressive_confidence_cap=0.9,
           conviction_edge_adaptive_enabled=True,
           conviction_edge_min_payoff=2.0, conviction_edge_full_payoff=4.0)
    # pełna pewność: bazowy boost = 2.0x
    assert trading_engine.conviction_multiplier(s, 0.9, edge_payoff=None) == 2.0
    # słaba przewaga ściąga mnożnik do 1.0 (samo wzmacnianie wyzerowane)
    assert trading_engine.conviction_multiplier(s, 0.9, edge_payoff=1.0) == 1.0
    # nigdy poniżej 1.0 -- bazowy rozmiar nietknięty
    assert trading_engine.conviction_multiplier(s, 0.9, edge_payoff=0.1) >= 1.0


def test_recent_edge_payoff_walks_ledger(db_session):
    s = _s(conviction_edge_lookback_trades=10)
    base = datetime(2026, 8, 20, tzinfo=UTC)
    # dwie wygrane po +$10 i jedna strata -$5 -> payoff = 10 / 5 = 2.0
    _buy(db_session, "SPY", 1, 100, base)
    _sell(db_session, "SPY", 1, 110, base + timedelta(days=1))
    _buy(db_session, "SPY", 1, 100, base + timedelta(days=2))
    _sell(db_session, "SPY", 1, 110, base + timedelta(days=3))
    _buy(db_session, "QQQ", 1, 100, base + timedelta(days=4))
    _sell(db_session, "QQQ", 1, 95, base + timedelta(days=5))
    db_session.commit()
    payoff = trading_engine.recent_edge_payoff(db_session, s, venue="alpaca")
    assert payoff == 2.0


def test_recent_edge_payoff_none_without_both_sides(db_session):
    s = _s()
    base = datetime(2026, 8, 20, tzinfo=UTC)
    _buy(db_session, "SPY", 1, 100, base)
    _sell(db_session, "SPY", 1, 110, base + timedelta(days=1))  # tylko wygrana
    db_session.commit()
    assert trading_engine.recent_edge_payoff(db_session, s, venue="alpaca") is None


# --- #3: dławienie re-analizy ---------------------------------------------

def test_price_move_throttled_within_gap(db_session):
    s = _s(price_move_trigger_pct=2.0, claude_min_reanalysis_minutes=20, full_analysis_every_minutes=0)
    state = risk_manager.get_state(db_session)
    trading_engine._mark_analysis_done_today(db_session)  # last_full_date = dziś (wyklucza dzienny fallback)
    # świeża analiza minutę temu
    trading_engine._set_analysis_marks(state, "alpaca", datetime.now(UTC).date().isoformat(),
                                       (datetime.now(UTC) - timedelta(minutes=1)).isoformat())
    db_session.commit()
    # kotwica
    trading_engine.check_trigger(db_session, s, {"SPY": 100.0, "QQQ": 400.0})
    # ruch 3% w oknie 20 min -> zdławiony
    triggered, _ = trading_engine.check_trigger(db_session, s, {"SPY": 103.0, "QQQ": 400.0})
    assert triggered is False


def test_price_move_fires_after_gap(db_session):
    s = _s(price_move_trigger_pct=2.0, claude_min_reanalysis_minutes=20, full_analysis_every_minutes=0)
    state = risk_manager.get_state(db_session)
    trading_engine._mark_analysis_done_today(db_session)
    # ostatnia analiza 30 min temu (poza oknem dławienia)
    trading_engine._set_analysis_marks(state, "alpaca", datetime.now(UTC).date().isoformat(),
                                       (datetime.now(UTC) - timedelta(minutes=30)).isoformat())
    db_session.commit()
    trading_engine.check_trigger(db_session, s, {"SPY": 100.0, "QQQ": 400.0})
    triggered, reason = trading_engine.check_trigger(db_session, s, {"SPY": 103.0, "QQQ": 400.0})
    assert triggered is True
    assert reason == trading_engine.TriggerType.PRICE_MOVE


# --- B: marketable-LIMIT na nazwach o szerokim spreadzie ------------------

def _limit_spy_client(monkeypatch):
    """Prawdziwy AlpacaClient z podmienionym get_price/_submit_order -- testuje
    realne rozgałęzienie place_order_for_session bez sieci."""
    from app.services.alpaca_client import AlpacaClient

    client = AlpacaClient(_s())
    submitted: list[dict] = []
    prices = {"TLT": 90.0, "SPY": 500.0}

    def fake_submit(symbol, side, *, notional=None, qty=None, order_type="market",
                    limit_price=None, extended_hours=False):
        submitted.append({"symbol": symbol, "type": order_type, "qty": qty,
                          "notional": notional, "limit_price": limit_price})
        return {"id": "1", "side": side, "status": "filled",
                "filled_qty": str(qty or (notional / prices[symbol])),
                "filled_avg_price": str(limit_price or prices[symbol])}

    monkeypatch.setattr(client, "get_price", lambda s: prices[s])
    monkeypatch.setattr(client, "_submit_order", fake_submit)
    return client, submitted


def test_prefer_limit_uses_marketable_limit_when_shares_fit(monkeypatch):
    client, submitted = _limit_spy_client(monkeypatch)
    # $300 na TLT@90 -> 3 całe akcje: idzie LIMIT z buforem
    client.place_order_for_session(
        "TLT", "BUY", session="regular", usdt_amount=300.0, prefer_limit=True, limit_buffer_pct=0.3
    )
    assert submitted[-1]["type"] == "limit"
    assert submitted[-1]["qty"] == 3.0
    assert submitted[-1]["limit_price"] == round(90.0 * 1.003, 2)


def test_prefer_limit_falls_back_to_market_when_slice_below_one_share(monkeypatch):
    client, submitted = _limit_spy_client(monkeypatch)
    # $50 na TLT@90 -> < 1 akcja: spada na market/notional (ułamki)
    client.place_order_for_session(
        "TLT", "BUY", session="regular", usdt_amount=50.0, prefer_limit=True, limit_buffer_pct=0.3
    )
    assert submitted[-1]["type"] == "market"
    assert submitted[-1]["notional"] == 50.0


# --- #6: linia przewagi w raporcie tygodnia --------------------------------

def test_weekly_edge_line_warns_below_floor():
    s = _s(conviction_edge_lookback_trades=10, edge_alert_payoff_floor=2.5)
    closes = [
        {"pnl_usd": 3.0, "sold_at": "2026-08-25T10:00:00+00:00"},
        {"pnl_usd": -3.0, "sold_at": "2026-08-26T10:00:00+00:00"},  # payoff 1.0x < 2.5
    ]
    line = push_notifier._weekly_edge_line(s, closes)
    assert line is not None
    assert "payoff" in line
    assert "słabnie" in line


def test_weekly_edge_line_none_without_both_sides():
    s = _s()
    closes = [{"pnl_usd": 3.0, "sold_at": "2026-08-25T10:00:00+00:00"}]
    assert push_notifier._weekly_edge_line(s, closes) is None


# --- #8: alarm push przy auto-halcie ---------------------------------------

def test_halt_sends_push_alarm(db_session, monkeypatch):
    s = _s(daily_loss_limit_pct=5.0)
    alarms = []
    monkeypatch.setattr(push_notifier, "send_alarm",
                        lambda db, settings, *, title, body, tag="alarm": alarms.append((title, tag)) or 1)
    risk_manager.update_portfolio_value(db_session, s, 1000.0)  # baseline dnia
    state = risk_manager.update_portfolio_value(db_session, s, 900.0)  # -10% > 5% limit
    assert state.is_halted is True
    assert len(alarms) == 1
    assert alarms[0][1] == "risk-halt"


# --- C: dziennik decyzji w historii ----------------------------------------

def test_realized_history_carries_entry_thesis_and_outcome(db_session):
    from app.models import Decision, TradeAction, TriggerType

    dec = Decision(symbol="SPY", action=TradeAction.BUY, size_pct=10, confidence=0.9,
                   reasoning="Wejście: mocny trend + przebicie oporu.",
                   triggered_by=TriggerType.PRICE_MOVE, executed=True, venue="alpaca")
    db_session.add(dec)
    db_session.commit()
    base = datetime(2026, 8, 20, tzinfo=UTC)
    b = Trade(timestamp=base, symbol="SPY", side="BUY", quantity=1.0, price=100.0,
              usdt_value=100.0, mode=TradeMode.LIVE, venue="alpaca", decision_id=dec.id)
    db_session.add(b)
    _sell(db_session, "SPY", 1.0, 110.0, base + timedelta(days=2))
    db_session.commit()

    hist = scorecard.realized_history(db_session, venue="alpaca")
    assert len(hist) == 1
    row = hist[0]
    assert row["entry_thesis"] == "Wejście: mocny trend + przebicie oporu."
    assert row["thesis_worked"] is True
    assert row["pnl_usd"] == 10.0
