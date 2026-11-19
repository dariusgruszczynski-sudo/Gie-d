"""Jakość świec (#34): odrzuca dziurawe/za krótkie serie OHLC."""
from app.services import data_quality


def _good(n):
    return [[i * 3600, 100.0, 101.0, 99.0, 100.5, 1000] for i in range(n)]


def test_ohlc_quality_accepts_clean_series():
    q = data_quality.ohlc_quality(_good(60), min_bars=50)
    assert q["ok"] is True and q["bad_bars"] == 0 and q["bars"] == 60


def test_ohlc_quality_rejects_too_short():
    q = data_quality.ohlc_quality(_good(10), min_bars=50)
    assert q["ok"] is False and "za mało" in q["reason"]


def test_ohlc_quality_rejects_zeros_and_inverted():
    rows = _good(60)
    rows[0][4] = 0.0          # zerowa cena zamknięcia
    rows[1][2], rows[1][3] = 98.0, 102.0  # high < low
    for i in range(2, 6):
        rows[i][1] = -1.0     # ujemne ceny -> >2% złych
    q = data_quality.ohlc_quality(rows, min_bars=50)
    assert q["ok"] is False and q["bad_bars"] >= 6
