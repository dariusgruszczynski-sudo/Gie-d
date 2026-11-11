"""Ocena SHADOW-LLM (go/no-go dla LLM): czysto odczytowa analiza zalogowanych
rekomendacji Claude (bez handlu) — czy jego BUY-e wyprzedzają jego własne HOLD-y
na zwrocie FORWARD. To uczciwy test przewagi: jeśli po włączeniu LLM mielibyśmy
kupować dokładnie to, co Claude wskazał, czy wyszlibyśmy lepiej niż sama mechanika,
która w tych cyklach nic nie robiła lub trzymała?

Metoda: dla każdej rekomendacji z ceną wejścia szukamy ceny tego samego symbolu
~horizon_h później (z kolejnego wpisu shadow dla tego symbolu) i liczymy zwrot %.
Porównujemy średni zwrot forward BUY vs HOLD. Brak modelu — proste, czytelne,
nie do podkręcenia. Przy małej próbce zwraca insufficient_data (nie udajemy
wiedzy na garści punktów)."""

from datetime import UTC, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import LlmShadowRec


def _aware(ts):
    if ts is None:
        return None
    return ts if ts.tzinfo else ts.replace(tzinfo=UTC)


def shadow_report(db: Session, settings, *, venue: str = "crypto",
                  horizon_hours: int = 24, min_scored: int = 5) -> dict:
    """Raport przewagi SHADOW-LLM. Zwraca m.in. średni zwrot forward BUY vs HOLD
    i flagę buy_beats_hold (czy rekomendacje kupna Claude realnie wyprzedzają to,
    co odpuścił). status=disabled/insufficient_data/ok."""
    enabled = bool(getattr(settings, "crypto_llm_shadow_enabled", False))
    recs = db.execute(
        select(LlmShadowRec).where(LlmShadowRec.venue == venue).order_by(LlmShadowRec.timestamp.asc())
    ).scalars().all()
    total = len(recs)
    base = {
        "status": "ok",
        "enabled": enabled,
        "venue": venue,
        "horizon_hours": horizon_hours,
        "total_recs": total,
        "last_rec_at": _aware(recs[-1].timestamp).isoformat() if recs else None,
        "since": _aware(recs[0].timestamp).isoformat() if recs else None,
    }
    if total == 0:
        return {**base, "status": "disabled" if not enabled else "insufficient_data",
                "scored_buys": 0, "scored_holds": 0}

    # Ścieżka ceny per symbol (posortowana) — do wyszukania ceny forward.
    by_sym: dict[str, list[tuple] ] = {}
    for r in recs:
        if r.symbol and r.price_at and r.price_at > 0:
            by_sym.setdefault(r.symbol, []).append((_aware(r.timestamp), r.price_at))

    def _fwd_return(sym, t0, p0):
        """Zwrot % symbolu od t0 do pierwszego wpisu >= t0+horizon. None, gdy brak
        późniejszego punktu (rekomendacja zbyt świeża, by ją ocenić)."""
        cutoff = t0 + timedelta(hours=horizon_hours)
        for ts, px in by_sym.get(sym, []):
            if ts >= cutoff and px > 0:
                return (px - p0) / p0 * 100.0
        return None

    buys, holds = [], []
    for r in recs:
        if not r.symbol or not r.price_at or r.price_at <= 0:
            continue
        fwd = _fwd_return(r.symbol, _aware(r.timestamp), r.price_at)
        if fwd is None:
            continue
        act = (r.action or "HOLD").upper()
        if act == "BUY":
            buys.append(fwd)
        elif act == "HOLD":
            holds.append(fwd)

    def _avg(xs):
        return round(sum(xs) / len(xs), 2) if xs else None

    buy_avg = _avg(buys)
    hold_avg = _avg(holds)
    out = {
        **base,
        "scored_buys": len(buys),
        "scored_holds": len(holds),
        "buy_avg_fwd_pct": buy_avg,
        "buy_win_rate": round(sum(1 for x in buys if x > 0) / len(buys) * 100, 1) if buys else None,
        "hold_avg_fwd_pct": hold_avg,
        "buy_beats_hold": (buy_avg is not None and hold_avg is not None and buy_avg > hold_avg),
    }
    if len(buys) < min_scored:
        out["status"] = "insufficient_data"
        out["min_scored"] = min_scored
    return out
