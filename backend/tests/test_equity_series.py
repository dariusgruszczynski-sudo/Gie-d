"""Seria equity (#2/#39): strategia vs hold-BTC vs DCA-BTC — porównywalne krzywe."""
from app.services.equity_series import equity_baselines, series_summary


def test_hold_btc_tracks_price_ratio():
    # v0=1000 @ BTC 100; BTC rośnie do 200 -> hold-BTC podwaja do 2000.
    rows = [("t0", 1000.0, 100.0), ("t1", 1050.0, 150.0), ("t2", 900.0, 200.0)]
    pts = equity_baselines(rows)
    assert pts[0].hold_btc == 1000.0
    assert pts[1].hold_btc == 1500.0
    assert pts[2].hold_btc == 2000.0
    # strategia = surowa wartość konta
    assert [p.strategy for p in pts] == [1000.0, 1050.0, 900.0]


def test_dca_fully_invested_at_end_and_anchored():
    rows = [("t0", 1000.0, 100.0), ("t1", 1000.0, 100.0)]
    pts = equity_baselines(rows)
    # Przy stałej cenie DCA == hold == v0 (zero zysku/straty).
    assert pts[0].dca_btc == 1000.0
    assert pts[1].dca_btc == 1000.0
    # n=2 transze po 500; po t1 gotówka wyczerpana (w pełni zainwestowane).


def test_dca_differs_from_hold_when_price_moves():
    # DCA kupuje połowę drożej -> mniej jednostek niż hold od t0.
    rows = [("t0", 1000.0, 100.0), ("t1", 1000.0, 200.0)]
    pts = equity_baselines(rows)
    # hold: wszystko @100 -> t1 wartość 2000.
    assert pts[1].hold_btc == 2000.0
    # DCA: 500 @100 (5 szt) + 500 @200 (2.5 szt) = 7.5 szt * 200 = 1500.
    assert pts[1].dca_btc == 1500.0
    assert pts[1].dca_btc < pts[1].hold_btc


def test_no_btc_price_leaves_baselines_none():
    rows = [("t0", 1000.0, None), ("t1", 1100.0, None)]
    pts = equity_baselines(rows)
    assert all(p.hold_btc is None and p.dca_btc is None for p in pts)
    assert [p.strategy for p in pts] == [1000.0, 1100.0]


def test_summary_beats_flags():
    rows = [("t0", 1000.0, 100.0), ("t1", 1300.0, 110.0)]
    pts = equity_baselines(rows)
    s = series_summary(pts)
    # strategia +30%, hold-BTC +10% -> bije hold.
    assert s["strategy_pct"] == 30.0
    assert s["hold_btc_pct"] == 10.0
    assert s["beats_hold"] is True


def test_summary_empty():
    s = series_summary([])
    assert s["strategy_pct"] is None and s["beats_hold"] is None
