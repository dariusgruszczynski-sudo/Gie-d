import json
from datetime import datetime, timedelta, timezone

from app.models import Decision, TradeAction, TriggerType
from app.services import shadow_analysis


def _decision(ts, market_data, venue="alpaca"):
    return Decision(
        timestamp=ts,
        symbol="SPY",
        action=TradeAction.HOLD,
        size_pct=0.0,
        confidence=0.5,
        reasoning="test",
        market_data_snapshot=json.dumps(market_data),
        triggered_by=TriggerType.SCHEDULED_DAILY,
        executed=False,
        venue=venue,
    )


def _tech(trend="above", macd="bullish", rsi=60.0, vol=1.5):
    return {"sma50_vs_sma200_1h": trend, "macd_signal": macd, "rsi_14": rsi, "volatility_pct_1h": vol}


def test_claude_edge_replays_mechanical_entry_and_stop_loss(db_session, settings):
    """A mechanically-qualifying signal followed by a price drop past the stop
    must show up as one closed shadow trade with a negative return."""
    now = datetime.now(timezone.utc)
    db_session.add(_decision(now, {"SPY": {"price": 100.0, "technical": _tech()}}))
    db_session.add(_decision(
        now + timedelta(hours=1),
        {"SPY": {"price": 90.0, "technical": _tech()}},  # -10% -> past any reasonable stop
    ))
    db_session.commit()

    result = shadow_analysis.compute_claude_edge(db_session, settings, venue="alpaca")

    assert result["cycles_analyzed"] == 2
    assert result["mechanical_only"]["closed_trades"] == 1
    assert result["mechanical_only"]["losses"] == 1
    assert result["mechanical_only"]["avg_return_pct"] < 0


def test_claude_edge_no_entry_when_signal_weak(db_session, settings):
    """A weak/mixed technical read (no confluence) must never open a shadow
    position -- zero trades, not a crash."""
    now = datetime.now(timezone.utc)
    weak = {"sma50_vs_sma200_1h": "below", "macd_signal": "bearish", "rsi_14": 40.0, "volatility_pct_1h": 1.5}
    db_session.add(_decision(now, {"SPY": {"price": 100.0, "technical": weak}}))
    db_session.commit()

    result = shadow_analysis.compute_claude_edge(db_session, settings, venue="alpaca")

    assert result["mechanical_only"]["closed_trades"] == 0
    assert result["mechanical_only"]["win_rate_pct"] is None


def test_claude_edge_ignores_other_venue_decisions(db_session, settings):
    now = datetime.now(timezone.utc)
    db_session.add(_decision(now, {"BTCUSD": {"price": 50000.0, "technical": _tech()}}, venue="crypto"))
    db_session.commit()

    result = shadow_analysis.compute_claude_edge(db_session, settings, venue="alpaca")
    assert result["cycles_analyzed"] == 0


def test_claude_edge_with_claude_side_reflects_actual_trades(db_session, settings):
    from app.models import Trade, TradeMode

    now = datetime.now(timezone.utc)
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="BUY", quantity=1, price=100.0, usdt_value=100.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.add(Trade(
        timestamp=now, symbol="SPY", side="SELL", quantity=1, price=105.0, usdt_value=105.0,
        mode=TradeMode.LIVE, venue="alpaca",
    ))
    db_session.commit()

    result = shadow_analysis.compute_claude_edge(db_session, settings, venue="alpaca")

    assert result["with_claude"]["closed_trades"] == 1
    assert result["with_claude"]["wins"] == 1
    assert result["with_claude"]["realized_usd"] == 5.0
