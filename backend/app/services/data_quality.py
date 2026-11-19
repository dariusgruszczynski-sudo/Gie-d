"""Jakość danych świecowych (#34 backlog). Czysto obliczeniowe: odrzuca serie OHLC
z zerami/ujemnymi cenami/niespójnościami/za krótkie. Na cienkim venue (alty na
Alpace) feedy bywają dziurawe — śmieciowe świece dają śmieciowe sygnały i fałszywe
wejścia. Lepiej POMINĄĆ symbol niż handlować na szumie."""


def ohlc_quality(rows, *, min_bars: int = 50, max_bad_frac: float = 0.02) -> dict:
    """Zwraca {ok, reason, bars, bad_bars}. Wiersz = [t, o, h, l, c, v]. 'Zła' świeca:
    nieparsowalna, cena <= 0 albo high < low. ok, gdy dość świec i <= max_bad_frac złych."""
    rows = rows or []
    bars = len(rows)
    if bars < min_bars:
        return {"ok": False, "reason": f"za mało świec ({bars} < {min_bars})", "bars": bars, "bad_bars": bars}
    bad = 0
    for r in rows:
        try:
            o, h, lo, c = float(r[1]), float(r[2]), float(r[3]), float(r[4])
        except (TypeError, ValueError, IndexError):
            bad += 1
            continue
        if o <= 0 or h <= 0 or lo <= 0 or c <= 0 or h < lo:
            bad += 1
    frac = bad / bars if bars else 1.0
    ok = frac <= max_bad_frac
    return {"ok": ok, "reason": "ok" if ok else f"{bad}/{bars} świec zepsutych", "bars": bars, "bad_bars": bad}
