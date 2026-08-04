"""GielDarek -- diagnostyka wyników na żywo (read-only).

Uruchom na serwerze:
    docker compose exec -T app python scripts/diag.py

Odpowiada na dwa pytania:
  1. Jak idzie? (P&L zrealizowany + papierowy, trafność, pozycje, krzywa)
  2. Czy limit wejść realnie WIĄŻE? (ile świeżych wejść dziennie vs cap) oraz
     DLACZEGO wejść jest mało (odrzucenia: reżim / pewność / cap / blackout).

Nic nie zleca -- czyta tylko bazę i liczy to samo, co dashboard.
"""
import collections
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Pozwól odpalać zarówno `python -m scripts.diag`, jak i `python scripts/diag.py`
# z katalogu /app -- w tym drugim przypadku pakiet `app` nie jest na ścieżce.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Decision, PortfolioSnapshot, Trade  # noqa: E402
from app.services import scorecard  # noqa: E402
from app.services.trading_engine import average_cost_basis, position_opened_at  # noqa: E402


def _fmt(x):
    return f"${x:,.2f}"


def _realized_since(trades, cutoff):
    """Zrealizowany P&L i trafność liczone TYLKO dla sprzedaży po `cutoff`
    (ale z poprawną średnią ceną walkowaną od początku historii). Pozwala oddzielić
    wynik NOWEJ, zdyscyplinowanej strategii od starego churnu."""
    qty_by, cost_by = {}, {}
    realized, wins, losses = 0.0, 0, 0
    for t in trades:
        sym = t.symbol
        if t.side.upper() == "BUY":
            qty_by[sym] = qty_by.get(sym, 0.0) + t.quantity
            cost_by[sym] = cost_by.get(sym, 0.0) + t.usdt_value
        else:
            held = qty_by.get(sym, 0.0)
            if held <= 1e-12:
                continue
            avg = cost_by[sym] / held
            sell_qty = min(t.quantity, held)
            pnl = (t.price - avg) * sell_qty
            ts = t.timestamp if t.timestamp.tzinfo else t.timestamp.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                realized += pnl
                if pnl >= 0:
                    wins += 1
                else:
                    losses += 1
            cost_by[sym] -= avg * sell_qty
            qty_by[sym] = held - sell_qty
            if qty_by[sym] <= 1e-12:
                qty_by[sym] = 0.0
                cost_by[sym] = 0.0
    return realized, wins, losses


def main():
    s = get_settings()
    db = SessionLocal()
    try:
        trades = db.execute(select(Trade).order_by(Trade.timestamp.asc())).scalars().all()
        buys = [t for t in trades if t.side.upper() == "BUY"]
        sells = [t for t in trades if t.side.upper() == "SELL"]
        realized, wins, losses = scorecard._walk_realized(db)
        closed = wins + losses
        win_rate = (wins / closed * 100) if closed else 0.0

        print("=" * 64)
        print("WYNIKI GIELDAREK")
        print("=" * 64)
        print(f"Transakcji: {len(trades)}  (kupno {len(buys)} / sprzedaż {len(sells)})")
        print(f"Zrealizowany P&L (CAŁE ŻYCIE): {_fmt(realized)}  | zamknięte: {closed}  "
              f"| trafność: {win_rate:.0f}%  ({wins} W / {losses} L)")

        # Podział na epoki: stara strategia (churn) vs nowa (pozycyjna). To
        # kluczowe -- lifetime miesza oba, a decyzja o limitach zależy od tego,
        # czy NOWA strategia realnie zarabia.
        now = datetime.now(timezone.utc)
        for label, days in (("OSTATNIE 7 DNI", 7), ("OSTATNIE 30 DNI", 30)):
            r, w, l = _realized_since(trades, now - timedelta(days=days))
            c = w + l
            wr = (w / c * 100) if c else 0.0
            print(f"Zrealizowany P&L ({label}): {_fmt(r)}  | zamknięte: {c}  "
                  f"| trafność: {wr:.0f}%  ({w} W / {l} L)")

        # --- Pozycje otwarte + papierowy P&L ---
        snap = db.execute(
            select(PortfolioSnapshot).where(PortfolioSnapshot.venue == "alpaca")
            .order_by(PortfolioSnapshot.timestamp.desc()).limit(1)
        ).scalar_one_or_none()
        unreal = 0.0
        print("\nOTWARTE POZYCJE:")
        if snap is None:
            print("  (brak snapshotu)")
        else:
            balances = json.loads(snap.balances_json or "{}")
            prices = json.loads(snap.prices_json or "{}")
            held = [(b, q) for b, q in balances.items() if q and q > 0]
            if not held:
                print("  (brak -- gotówka czeka)")
            for base, qty in sorted(held, key=lambda kv: -(kv[1] * (prices.get(kv[0]) or 0))):
                price = prices.get(base)
                if price is None:
                    continue
                basis = average_cost_basis(db, base, venue="alpaca")
                opened = position_opened_at(db, base, venue="alpaca")
                days = None
                if opened is not None:
                    o = opened if opened.tzinfo else opened.replace(tzinfo=timezone.utc)
                    days = (datetime.now(timezone.utc) - o).days
                pnl = (price - basis) * qty if basis else 0.0
                unreal += pnl
                chg = f"{(price - basis) / basis * 100:+.1f}%" if basis else "—"
                print(f"  {base:6}  {_fmt(qty * price):>10}  wejście {_fmt(basis) if basis else '—':>10}  "
                      f"{chg:>7}  {_fmt(pnl):>9}  {days if days is not None else '—'} dni")
            print(f"  Papierowy razem: {_fmt(unreal)}")
        print(f"\n>>> ZYSK AUTOMATU (zrealizowany + papierowy): {_fmt(realized + unreal)}")

        # --- Czy limit wejść WIĄŻE? świeże wejścia dziennie ---
        cap = s.max_new_positions_per_day
        per_day = collections.Counter()
        for t in buys:
            per_day[t.timestamp.date().isoformat()] += 1
        print("\n" + "=" * 64)
        print(f"WEJŚCIA DZIENNIE vs LIMIT (cap = {cap}/dzień)")
        print("=" * 64)
        if not per_day:
            print("  (brak kupna w historii)")
        else:
            hit = 0
            for day in sorted(per_day)[-14:]:
                n = per_day[day]
                bar = "█" * n
                mark = "  <-- LIMIT" if n >= cap else ""
                if n >= cap:
                    hit += 1
                print(f"  {day}  {n:2}  {bar}{mark}")
            mx = max(per_day.values())
            print(f"\n  Max w jednym dniu: {mx}  |  dni z osiągniętym limitem: {hit}")
            if mx < cap:
                print(f"  WNIOSEK: limit {cap} NIGDY nie był osiągnięty -> NIE hamuje wejść.")
                print("           Mało wejść wynika ze strategii/reżimu/pewności, nie z capu.")
            else:
                print(f"  WNIOSEK: limit bywa osiągany ({hit} dni) -> podniesienie MOŻE pomóc.")

        # --- DLACZEGO mało wejść: odrzucenia i decyzje ---
        recent = db.execute(
            select(Decision).order_by(Decision.timestamp.desc()).limit(300)
        ).scalars().all()
        by_action = collections.Counter(d.action.value if hasattr(d.action, "value") else str(d.action) for d in recent)
        rejected = [d for d in recent if d.rejection_reason]
        rej_reasons = collections.Counter(d.rejection_reason for d in rejected)
        print("\n" + "=" * 64)
        print("DLACZEGO TYLE WEJŚĆ? (ostatnie 300 decyzji)")
        print("=" * 64)
        print("  Akcje Claude:", dict(by_action))
        print(f"  Odrzuconych (nie weszły mimo sygnału): {len(rejected)}")
        for reason, n in rej_reasons.most_common(8):
            print(f"    {n:3}x  {reason}")

        print("\n" + "=" * 64)
        print("USTAWIENIA WPŁYWAJĄCE NA LICZBĘ WEJŚĆ")
        print("=" * 64)
        print(f"  max_new_positions_per_day = {s.max_new_positions_per_day}")
        print(f"  max_concurrent_positions  = {s.max_concurrent_positions}")
        print(f"  min_buy_confidence        = {s.min_buy_confidence}")
        print(f"  min_hold_minutes          = {s.min_hold_minutes}")
        print(f"  regime_gate_enabled       = {s.regime_gate_enabled}  (risk-off = tylko gotówka/defensywa)")
        print(f"  entry_filter_enabled      = {s.entry_filter_enabled}  (min_score {s.entry_min_score}/3)")
        print(f"  price_move_trigger_pct    = {s.price_move_trigger_pct}  (budzi Claude na ruchu)")
        print(f"  signal_timeframe          = {s.signal_timeframe}")
        print("=" * 64)
    finally:
        db.close()


if __name__ == "__main__":
    main()
