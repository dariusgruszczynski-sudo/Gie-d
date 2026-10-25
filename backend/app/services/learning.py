"""Substrat uczenia (#1/#2/#15 roadmapy): łączy CECHY WEJŚCIA (ze snapshotu
decyzji otwierającej pozycję) z WYNIKIEM zamknięcia (%/win), i liczy KRZYWĄ
UCZENIA — czy expectancy/trafność rośnie w czasie. To fundament pod atrybucję
edge (#3) i automatyczną adaptację (#4): bez trwałego połączenia „co widziałem
przy wejściu → ile na tym zarobiłem" cała pętla uczenia liczyłaby szum.

Czysto odczytowe, bez efektów ubocznych. Czysty baseline: `open_since` liczy
tylko pozycje OTWARTE po epoce (wycina blowout — spójnie ze scorecardem)."""

import json
from collections import defaultdict
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Decision, Trade


def _aware(ts):
    if ts is None:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def _entry_features(snapshot_json: str, symbol: str) -> dict:
    """Wyciąga kompaktowy wektor cech, który silnik WIDZIAŁ przy wejściu, ze
    snapshotu market_data decyzji otwierającej (bramki wejścia #6/#8/#9 + technikalia)."""
    try:
        md = (json.loads(snapshot_json or "{}") or {}).get(symbol) or {}
    except (TypeError, ValueError):
        return {}
    tech = md.get("technical") or {}
    return {
        "trend": tech.get("sma50_vs_sma200_1h"),
        "macd": tech.get("macd_signal"),
        "rsi": tech.get("rsi_14"),
        "vol_pct": tech.get("volatility_pct_1h"),
        "adx": md.get("adx"),
        "change_period_pct": md.get("change_period_pct"),
        "htf_trend_ok": md.get("htf_trend_ok"),
    }


def labeled_closes(db: Session, *, venue: str | None = "crypto", open_since=None) -> list[dict]:
    """Dla KAŻDEJ zamkniętej pozycji: cechy wejścia (z decyzji otwierającej lot) +
    wynik (pnl_pct, win) + czasy. Average-cost walk z trackingiem lotu i decyzji
    otwierającej. Najstarsze pierwsze. To etykietowany dataset do uczenia."""
    trades = db.execute(select(Trade).order_by(Trade.timestamp.asc())).scalars().all()
    dec_ids = {t.decision_id for t in trades if t.decision_id}
    decs: dict[int, Decision] = {}
    if dec_ids:
        for d in db.execute(select(Decision).where(Decision.id.in_(dec_ids))).scalars().all():
            decs[d.id] = d

    qty: dict[str, float] = defaultdict(float)
    cost: dict[str, float] = defaultdict(float)
    lot_open: dict[str, object] = {}
    lot_dec: dict[str, object] = {}
    out: list[dict] = []

    for t in trades:
        sym = t.symbol
        if t.side.upper() == "BUY":
            if qty[sym] <= 1e-12:
                lot_open[sym] = _aware(t.timestamp)
                lot_dec[sym] = t.decision_id
            qty[sym] += t.quantity
            cost[sym] += t.usdt_value
        else:  # SELL
            held = qty[sym]
            if held <= 1e-12:
                continue
            avg = cost[sym] / held
            sell_qty = min(t.quantity, held)
            cost_usd = avg * sell_qty
            pnl = (t.price - avg) * sell_qty
            keep = True
            if venue is not None and getattr(t, "venue", "alpaca") != venue:
                keep = False
            if venue == "crypto" and "/" not in sym:
                keep = False
            if open_since is not None:
                lo = lot_open.get(sym)
                keep = keep and lo is not None and lo >= open_since
            if keep:
                d = decs.get(lot_dec.get(sym))
                lo = lot_open.get(sym)
                out.append({
                    "symbol": sym,
                    "opened_at": lo.isoformat() if lo else None,
                    "sold_at": _aware(t.timestamp).isoformat() if t.timestamp else None,
                    "pnl_pct": round(pnl / cost_usd * 100, 2) if cost_usd > 0 else None,
                    "win": pnl >= 0,
                    "features": _entry_features(d.market_data_snapshot if d else "{}", sym),
                })
            cost[sym] -= cost_usd
            qty[sym] -= sell_qty
            if qty[sym] <= 1e-12:
                qty[sym] = 0.0
                cost[sym] = 0.0
                lot_open.pop(sym, None)
                lot_dec.pop(sym, None)
    return out


def feature_attribution(closes: list[dict]) -> list[dict]:
    """ATRYBUCJA EDGE (#3): dla każdej cechy wejścia i jej wartości — ile trejdów,
    trafność i średni wynik %. Pokazuje, KTÓRE sygnały realnie przewidują wygrane,
    a które dodają szum. Proste zliczanie (nie model), ale uczciwe i czytelne.
    Cechy ciągłe (rsi/adx/vol/change) binujemy na proste przedziały."""
    def _bucket(key, val):
        if val is None:
            return None
        if key in ("trend", "macd", "htf_trend_ok"):
            return str(val)
        try:
            v = float(val)
        except (TypeError, ValueError):
            return str(val)
        if key == "rsi":
            return "rsi<35" if v < 35 else ("rsi35-50" if v < 50 else ("rsi50-70" if v < 70 else "rsi>=70"))
        if key == "adx":
            return "adx<20" if v < 20 else ("adx20-30" if v < 30 else "adx>=30")
        if key == "vol_pct":
            return "vol<3" if v < 3 else ("vol3-6" if v < 6 else "vol>=6")
        if key == "change_period_pct":
            return "chg<0" if v < 0 else ("chg0-5" if v < 5 else "chg>=5")
        return str(val)

    agg: dict[tuple, dict] = {}
    for c in closes:
        pnl = c.get("pnl_pct")
        if pnl is None:
            continue
        for key, val in (c.get("features") or {}).items():
            b = _bucket(key, val)
            if b is None:
                continue
            a = agg.setdefault((key, b), {"feature": key, "value": b, "n": 0, "wins": 0, "sum_pct": 0.0})
            a["n"] += 1
            a["wins"] += 1 if c.get("win") else 0
            a["sum_pct"] += pnl
    out = []
    for a in agg.values():
        if a["n"] < 1:
            continue
        out.append({
            "feature": a["feature"], "value": a["value"], "n": a["n"],
            "win_rate": round(a["wins"] / a["n"] * 100, 1),
            "avg_pct": round(a["sum_pct"] / a["n"], 2),
        })
    # Najpierw najmocniejszy edge (po avg_pct), tylko sensowne próbki na górze.
    out.sort(key=lambda r: (r["avg_pct"]), reverse=True)
    return out


def learning_curve(db: Session, settings, *, venue: str = "crypto", cohort_size: int = 10) -> dict:
    """KRZYWA UCZENIA (#15): dzieli zamknięcia (od epoki) na kohorty po
    cohort_size trejdów i liczy per-kohorta expectancy (śr. %/trejd) + trafność.
    `trend` = czy OSTATNIA kohorta bije PIERWSZĄ na expectancy (improving/flat/
    degrading). None gdy < 2 kohort — za wcześnie na trend."""
    from app.services import risk_manager, scorecard

    state = risk_manager.get_state(db)
    epoch, epoch_raw = scorecard.effective_epoch(state, settings, venue=venue)
    closes = labeled_closes(db, venue=venue, open_since=epoch)
    closes.sort(key=lambda c: c["sold_at"] or "")

    cohorts: list[dict] = []
    for i in range(0, len(closes), cohort_size):
        chunk = closes[i:i + cohort_size]
        pnl = [c["pnl_pct"] for c in chunk if c["pnl_pct"] is not None]
        if not pnl:
            continue
        cohorts.append({
            "from": chunk[0]["sold_at"],
            "to": chunk[-1]["sold_at"],
            "n": len(chunk),
            "expectancy_pct": round(sum(pnl) / len(pnl), 2),
            "win_rate": round(sum(1 for c in chunk if c["win"]) / len(chunk) * 100, 1),
        })

    trend = None
    if len(cohorts) >= 2:
        first, last = cohorts[0]["expectancy_pct"], cohorts[-1]["expectancy_pct"]
        trend = "improving" if last > first else ("flat" if last == first else "degrading")

    return {
        "cohorts": cohorts,
        "trend": trend,
        "total_closes": len(closes),
        "since": epoch_raw or None,
        "cohort_size": cohort_size,
        "attribution": feature_attribution(closes),
    }
