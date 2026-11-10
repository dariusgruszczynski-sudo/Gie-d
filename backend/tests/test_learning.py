"""Substrat uczenia (#1/#2/#15): etykietowanie wyników + krzywa uczenia."""
import json
from datetime import UTC, datetime, timedelta

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


def test_labeled_closes_r_multiple_matches_entry_risk(db_session, settings):
    """pnl_R = wynik / ryzyko-początkowe, liczone jak w backteście
    (koszt * stop_pct/100, stop ze zmienności widzianej przy wejściu). Z settings
    etykieta R musi być obecna i równa pnl/risk0; bez settings — None."""
    from app.services.trading_engine import dynamic_stop_loss_pct

    t0 = datetime(2026, 10, 20, tzinfo=UTC)
    _open_buy(db_session, "SOL/USD", t0, 100.0, 1.0, _snap("SOL/USD"))  # vol_pct=3.0 w _snap
    db_session.add(Trade(timestamp=datetime(2026, 10, 21, tzinfo=UTC), symbol="SOL/USD", side="SELL",
                         quantity=1.0, price=120.0, usdt_value=120.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()

    sp = dynamic_stop_loss_pct(settings, 3.0)
    expected_r = round(20.0 / (100.0 * sp / 100.0), 2)  # pnl=20, risk0=koszt*stop%/100

    with_s = learning.labeled_closes(db_session, venue="crypto", settings=settings)
    assert with_s[0]["pnl_R"] == expected_r
    assert with_s[0]["schema_version"] == learning.FEATURE_SCHEMA_VERSION

    without_s = learning.labeled_closes(db_session, venue="crypto")  # brak settings
    assert without_s[0]["pnl_R"] is None
    assert without_s[0]["schema_version"] == learning.FEATURE_SCHEMA_VERSION


def test_learning_curve_reports_expectancy_r(db_session, settings):
    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-16T00:00:00+00:00"})
    for i, (buy, sell) in enumerate([(100, 110), (100, 120)]):
        sym = f"R{i}/USD"
        _open_buy(db_session, sym, datetime(2026, 10, 20 + i, tzinfo=UTC), float(buy), 1.0, _snap(sym))
        db_session.add(Trade(timestamp=datetime(2026, 10, 20 + i, 12, tzinfo=UTC), symbol=sym, side="SELL",
                             quantity=1.0, price=float(sell), usdt_value=float(sell), mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    lc = learning.learning_curve(db_session, s, venue="crypto", cohort_size=2)
    assert lc["schema_version"] == learning.FEATURE_SCHEMA_VERSION
    assert lc["expectancy_R"] is not None and lc["expectancy_R"] > 0
    assert lc["cohorts"][0]["expectancy_R"] is not None


def test_export_feature_store_flat_versioned(db_session, settings):
    """Eksport: płaski, wersjonowany dataset — stałe kolumny, cechy z prefiksem
    feat_, metryki wyniku (%/R/win) i schema_version na każdym wierszu."""
    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-01T00:00:00+00:00"})
    t0 = datetime(2026, 10, 20, tzinfo=UTC)
    _open_buy(db_session, "SOL/USD", t0, 100.0, 1.0, _snap("SOL/USD"))
    db_session.add(Trade(timestamp=datetime(2026, 10, 21, tzinfo=UTC), symbol="SOL/USD", side="SELL",
                         quantity=1.0, price=120.0, usdt_value=120.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    store = learning.export_feature_store(db_session, s, venue="crypto")
    assert store["n"] == 1 and store["schema_version"] == learning.FEATURE_SCHEMA_VERSION
    assert store["columns"] == learning.EXPORT_COLUMNS
    r = store["rows"][0]
    assert r["symbol"] == "SOL/USD" and r["pnl_pct"] == 20.0 and r["win"] is True
    assert r["feat_trend"] == "above" and r["feat_rsi"] == 55 and r["feat_htf_trend_ok"] is True
    assert r["pnl_R"] is not None  # settings podane -> R policzone


def test_oos_validation_insufficient_data(db_session, settings):
    """Za mało zamknięć -> status insufficient_data (nie udajemy walidacji na szumie)."""
    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-01T00:00:00+00:00"})
    t0 = datetime(2026, 10, 20, tzinfo=UTC)
    _open_buy(db_session, "SOL/USD", t0, 100.0, 1.0, _snap("SOL/USD"))
    db_session.add(Trade(timestamp=datetime(2026, 10, 21, tzinfo=UTC), symbol="SOL/USD", side="SELL",
                         quantity=1.0, price=120.0, usdt_value=120.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    out = learning.oos_edge_validation(db_session, s, venue="crypto")
    assert out["status"] == "insufficient_data" and out["total_closes"] == 1


def test_oos_validation_edge_holds_out_of_sample(db_session, settings):
    """Edge z trainu (trend=above) utrzymuje się OOS: trejdy pasujące biją bazę.
    Układ: 8 wygranych (above, +20%) vs 16 przegranych (below, -15%) -> średnia
    globalna ujemna, więc TYLKO selektywny kubełek trend=above przechodzi jako
    edge; potwierdza on się na nieoglądanych danych (holds=True)."""
    s = settings.model_copy(update={"crypto_stats_epoch_default": "2026-10-01T00:00:00+00:00"})
    for i in range(24):
        winner = (i % 3 == 0)
        trend = "above" if winner else "below"
        sell = 120.0 if winner else 85.0  # +20% / -15%
        sym = f"W{i}/USD"
        when = datetime(2026, 10, 15, 0, 0, tzinfo=UTC) + timedelta(hours=i)
        _open_buy(db_session, sym, when, 100.0, 1.0, _snap(sym, trend=trend))
        db_session.add(Trade(timestamp=when + timedelta(minutes=30), symbol=sym, side="SELL",
                             quantity=1.0, price=sell, usdt_value=sell, mode=TradeMode.LIVE, venue="crypto"))
    db_session.commit()
    out = learning.oos_edge_validation(db_session, s, venue="crypto", split_frac=0.6, min_n=3)
    assert out["status"] == "ok" and out["total_closes"] == 24
    assert "trend=above" in out["edge_buckets"]
    assert out["oos_edge_avg_pct"] > out["oos_baseline_avg_pct"]
    assert out["holds"] is True


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
