"""Seria equity: strategia vs trzymanie BTC vs DCA BTC (#2/#39 z backloga).

Stała linia odniesienia: „czy aktywny handel w ogóle bije NAJPROSTSZE alternatywy?"
- strategia: realna wartość konta ze snapshotów (total_value_usdt),
- hold_btc: gdyby cały kapitał startowy wrzucić w BTC w t0 i trzymać,
- dca_btc: gdyby ten sam kapitał rozłożyć równo (DCA) po wszystkich punktach okna.

Wszystkie trzy anchorowane na tym samym kapitale startowym v0, więc są wprost
porównywalne na jednym wykresie. CZYSTA kalkulacja po istniejących snapshotach —
zero dotknięcia hot-path, zero zmian w handlu.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class EquityPoint:
    ts: str
    strategy: float
    hold_btc: float | None
    dca_btc: float | None

    def as_dict(self) -> dict:
        return {
            "ts": self.ts,
            "strategy": round(self.strategy, 2),
            "hold_btc": None if self.hold_btc is None else round(self.hold_btc, 2),
            "dca_btc": None if self.dca_btc is None else round(self.dca_btc, 2),
        }


def equity_baselines(rows: Sequence[tuple[str, float, float | None]]) -> list[EquityPoint]:
    """rows: (ts_iso, total_value, btc_price|None) POSORTOWANE rosnąco po czasie.

    hold_btc: kotwiczymy na pierwszym punkcie z dodatnią ceną BTC (v0 @ p0), potem
      hold = v0 * price_t / p0 (None, dopóki nie ma ceny).
    dca_btc: kapitał v0 wdrażany równo w każdym punkcie z ceną — chunk = v0/n;
      w każdym takim punkcie dokupujemy chunk/price jednostek BTC; wartość =
      pozostała gotówka + jednostki * cena_teraz. Na końcu okna w pełni zainwestowane.
    """
    out: list[EquityPoint] = []
    priced = [r for r in rows if r[2] is not None and r[2] > 0]
    if not priced:
        # Brak jakiejkolwiek ceny BTC — tylko krzywa strategii, baseline'y puste.
        return [EquityPoint(ts=ts, strategy=v, hold_btc=None, dca_btc=None) for ts, v, _ in rows]

    v0 = priced[0][1]
    p0 = priced[0][2]
    n = len(priced)
    chunk = v0 / n if n > 0 else 0.0

    dca_cash = v0
    dca_units = 0.0
    for ts, total, price in rows:
        if price is not None and price > 0:
            hold = v0 * price / p0
            # DCA: dokup kolejną transzę w tym punkcie (o ile została gotówka).
            if dca_cash > 1e-9:
                invest = min(chunk, dca_cash)
                dca_units += invest / price
                dca_cash -= invest
            dca_val = dca_cash + dca_units * price
            out.append(EquityPoint(ts=ts, strategy=total, hold_btc=hold, dca_btc=dca_val))
        else:
            out.append(EquityPoint(ts=ts, strategy=total, hold_btc=None, dca_btc=None))
    return out


def series_summary(points: Sequence[EquityPoint]) -> dict:
    """Jednoliniowe podsumowanie do nagłówka: końcowy % strategii vs baseline'y."""
    if not points:
        return {"strategy_pct": None, "hold_btc_pct": None, "dca_btc_pct": None,
                "beats_hold": None, "beats_dca": None}

    def _pct(first: float | None, last: float | None) -> float | None:
        if first is None or last is None or first <= 0:
            return None
        return (last / first - 1.0) * 100.0

    s_first = points[0].strategy
    s_last = points[-1].strategy
    hold_vals = [p.hold_btc for p in points if p.hold_btc is not None]
    dca_vals = [p.dca_btc for p in points if p.dca_btc is not None]
    s_pct = _pct(s_first, s_last)
    h_pct = _pct(hold_vals[0], hold_vals[-1]) if hold_vals else None
    d_pct = _pct(dca_vals[0], dca_vals[-1]) if dca_vals else None
    return {
        "strategy_pct": None if s_pct is None else round(s_pct, 2),
        "hold_btc_pct": None if h_pct is None else round(h_pct, 2),
        "dca_btc_pct": None if d_pct is None else round(d_pct, 2),
        "beats_hold": None if (s_pct is None or h_pct is None) else s_pct > h_pct,
        "beats_dca": None if (s_pct is None or d_pct is None) else s_pct > d_pct,
    }
