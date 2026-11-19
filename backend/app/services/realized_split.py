"""Rozdział zrealizowanego P&L: „nowa era" vs „zaszłości" (#40 z backloga).

Nadzór 2026-11-19 obnażył mylące mieszanie: UI pokazywało realized −$378k (w 61%
jeden blowout HYPE sprzed epoki), a obecna strategia ma ~$0 — to dwie różne historie
wrzucone do jednej liczby. Tu rozdzielamy je JAWNIE po dacie epoki (stats_since):
- epoch_usd: zrealizowane na SPRZEDAŻACH od epoki (wynik OBECNEJ strategii),
- legacy_usd: zrealizowane na sprzedażach PRZED epoką (zaszłości/blowout),
- all_usd: suma (kontrola spójności).

Average-cost walk per symbol (ta sama metoda, co w scorecard/dzienniku). Preferuje
zapisane pnl_usd z trejdu; gdy brak — liczy (cena − śr.koszt) × ilość. CZYSTA
funkcja — bez DB, zero dotknięcia hot-path, zero zmian w handlu.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable


def _f(x: object, default: float = 0.0) -> float:
    try:
        return float(x)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def realized_split(trades: Iterable[dict], epoch_iso: str | None) -> dict:
    """trades: dicty z polami symbol/side/quantity/price/timestamp/pnl_usd.
    epoch_iso: granica epoki (ISO). None => wszystko liczone jako „nowa era"
    (brak epoki = nie ma czego odcinać)."""
    pos: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0])  # [qty, cost]
    epoch_usd = legacy_usd = 0.0
    epoch_n = legacy_n = 0

    for r in sorted(trades, key=lambda x: x.get("timestamp") or ""):
        sym = r.get("symbol") or ""
        side = (r.get("side") or "").upper()
        qty = abs(_f(r.get("quantity")))
        px = _f(r.get("price"))
        ts = r.get("timestamp") or ""
        if side == "BUY":
            pos[sym][0] += qty
            pos[sym][1] += qty * px
        elif side == "SELL":
            held, cost = pos[sym]
            avg = cost / held if held > 0 else px
            pnl = r.get("pnl_usd")
            realized = _f(pnl) if pnl is not None else (px - avg) * qty
            is_epoch = (epoch_iso is None) or (ts >= epoch_iso)
            if is_epoch:
                epoch_usd += realized
                epoch_n += 1
            else:
                legacy_usd += realized
                legacy_n += 1
            if held > 0:
                take = min(qty, held)
                pos[sym][0] -= take
                pos[sym][1] -= avg * take

    return {
        "epoch_usd": round(epoch_usd, 2),
        "legacy_usd": round(legacy_usd, 2),
        "all_usd": round(epoch_usd + legacy_usd, 2),
        "epoch_count": epoch_n,
        "legacy_count": legacy_n,
        "epoch": epoch_iso,
    }
