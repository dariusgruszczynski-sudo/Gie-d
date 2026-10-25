"""Substrat uczenia (#1/#2/#15): etykietowanie wyników + krzywa uczenia."""
import json
from datetime import UTC, datetime

from app.models import Decision, Trade, TradeAction, TradeMode
from app.services import learning


def _snap(symbol, trend="above", rsi=55):
    return json.dumps({symbol: {"technical": {"sma50_vs_sma200_1h": trend, "macd_signal": "bullish", "rsi_14": rsi, "volatility_pct_1h": 3.0}, "adx": 25.0, "change_period_pct": 4.0, "htf_trend_ok": True}})


def _open_buy(db, sym, when, price, qty, snap):
    d = Decision(timestamp=when, symbol=sym, action=TradeAction.BUY, size_pct=10.0, confidence=1.0,
                 reasoning="x", market_data_snapshot=snap, venue="crypto", executed=True)
    db.add(d); db.commit(); db.refresh(d)
    db.add(Trade(timestamp=when, symbol=sym, side="BUY", quantity=qty, price=price, usdt_value=qty*price,
                 mode=TradeMode.LIVE, venue="crypto", decision_id=d.id))
    db.commit()


def test_labeled_closes_joins_entry_features_to_outcome(db_session):
    """Każde zamknięcie niesie cechy wejścia (ze snapshotu decyzji otwierającej)
    i wynik (%/win) — surowiec do atrybucji/uczenia."""
    t0 = datetime(2026, 10, 20, tzinfo=UTC)
    _open_buy(db_session, "SOL/USD", t0, 100.0, 1.0, _snap("SOL/USD", rsi=58))
    db_session.add(Trade(timestamp=datetime(2026, 10, 21, tzinfo=UTC), symbol="SOL/USD", side="SELL",
                         quantity=1.0, price=120.0, usdt_value=120.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()

    rows = learning.labeled_closes(db_session, venue="crypto")
    assert len(rows) == 1
    r = rows[0]
    assert r["symbol"] == "SOL/USD" and r["win"] is True and r["pnl_pct"] == 20.0
    assert r["features"]["rsi"] == 58 and r["features"]["trend"] == "above" and r["features"]["htf_trend_ok"] is True


def test_labeled_closes_open_since_excludes_blowout(db_session):
    # Otwarta przed epoką (blowout), domknięta po -> wykluczona przy open_since.
    _open_buy(db_session, "AVAX/USD", datetime(2026, 10, 14, tzinfo=UTC), 1000.0, 1.0, _snap("AVAX/USD"))
    db_session.add(Trade(timestamp=datetime(2026, 10, 20, tzinfo=UTC), symbol="AVAX/USD", side="SELL",
                         quantity=1.0, price=100.0, usdt_value=100.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    rows = learning.labeled_closes(db_session, venue="crypto", open_since=datetime(2026, 10, 16, tzinfo=UTC))
    assert rows == []


def test_learning_curve_cohorts_and_trend(db_session, settings):
    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-16T00:00:00+00:00"})
    # 4 zamknięcia: 2 słabe, potem 2 mocne -> trend improving (cohort_size=2).
    day = 20
    for i, (buy, sell) in enumerate([(100, 101), (100, 102), (100, 115), (100, 120)]):
        sym = f"C{i}/USD"
        _open_buy(db_session, sym, datetime(2026, 10, day + i, tzinfo=UTC), float(buy), 1.0, _snap(sym))
        db_session.add(Trade(timestamp=datetime(2026, 10, day + i, 12, tzinfo=UTC), symbol=sym, side="SELL",
                             quantity=1.0, price=float(sell), usdt_value=float(sell), mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    lc = learning.learning_curve(db_session, s, venue="crypto", cohort_size=2)
    assert lc["total_closes"] == 4 and len(lc["cohorts"]) == 2
    assert lc["cohorts"][-1]["expectancy_pct"] > lc["cohorts"][0]["expectancy_pct"]
    assert lc["trend"] == "improving"
