"""Rekonsyliacja baza↔broker (R24/R26, meta-analiza 2026-11-09).

Jedno źródło prawdy dla porównania: ile crypto myśli, że trzymamy (netto z
NASZEGO logu transakcji), vs ile realnie trzyma broker (ostatni snapshot).

Geneza: blowout HYPE (2026-10-27) był AWARIĄ REKONCYLIACJI — baza logowała 2848
HYPE, a broker miał 0; gotówka wyszła na kupno, pozycja warta ułamek, a
realized/unrealized tego nie widziały (P&L pokazywał "+$1k" przy koncie −27%).
Ten moduł liczy rozjazd jawnie — zasila (a) baner/nagłówek-uczciwość na pulpicie
i (b) WATCHDOG z auto-haltem, żeby silnik nie handlował na rozjechanych księgach.
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import PortfolioSnapshot, Trade


def _latest_crypto_snapshot(db: Session) -> PortfolioSnapshot | None:
    return db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.venue == "crypto")
        .order_by(PortfolioSnapshot.id.desc())
    ).scalars().first()


def ledger_vs_broker(db: Session, settings: Settings, *, account_total: float | None = None) -> dict | None:
    """Porównaj pozycje wg bazy (netto kupna−sprzedaże) z saldem brokera.

    Zwraca {ledger_crypto_usd, broker_crypto_usd, residual_usd, reconciled,
    threshold_usd, by_symbol} albo None, gdy krypto wyłączone / brak snapshotu.
    `reconciled` = abs(residual) <= próg (większy z podłogi i % konta).
    """
    if not settings.crypto_enabled:
        return None
    snap = _latest_crypto_snapshot(db)
    if snap is None:
        return None
    try:
        broker_bal = json.loads(snap.balances_json or "{}")
        prices = json.loads(snap.prices_json or "{}")
    except (TypeError, ValueError):
        return None

    rows = db.execute(
        select(Trade.symbol, Trade.side, Trade.quantity, Trade.price)
        .where(Trade.venue == "crypto")
        .order_by(Trade.id)
    ).all()
    ledger_qty: dict[str, float] = {}
    last_px: dict[str, float] = {}
    for sym, side, qty, px in rows:
        signed = qty if "BUY" in str(side).upper() else -qty
        ledger_qty[sym] = ledger_qty.get(sym, 0.0) + (signed or 0.0)
        if px:
            last_px[sym] = px

    def _px(sym: str) -> float:
        return prices.get(sym) or last_px.get(sym) or 0.0

    ledger_usd = sum(max(0.0, q) * _px(s) for s, q in ledger_qty.items())
    broker_usd = sum((broker_bal.get(s, 0.0) or 0.0) * _px(s) for s in set(broker_bal) | set(ledger_qty))
    residual = round(ledger_usd - broker_usd, 2)

    by_symbol = []
    for s in set(ledger_qty) | set(broker_bal):
        lq = max(0.0, ledger_qty.get(s, 0.0))
        bq = broker_bal.get(s, 0.0) or 0.0
        d = (lq - bq) * _px(s)
        if abs(d) >= 1.0:
            by_symbol.append({
                "symbol": s, "ledger_qty": round(lq, 6),
                "broker_qty": round(bq, 6), "diff_usd": round(d, 2),
            })
    by_symbol.sort(key=lambda x: -abs(x["diff_usd"]))

    acct = account_total if account_total is not None else (snap.total_value_usdt or 0.0)
    pct = float(getattr(settings, "crypto_reconciliation_halt_pct", 1.0) or 1.0)
    floor = float(getattr(settings, "crypto_reconciliation_halt_floor_usd", 2000.0) or 2000.0)
    threshold = max(floor, (acct or 0.0) * pct / 100.0)
    return {
        "ledger_crypto_usd": round(ledger_usd, 2),
        "broker_crypto_usd": round(broker_usd, 2),
        "residual_usd": residual,
        "reconciled": abs(residual) <= threshold,
        "threshold_usd": round(threshold, 2),
        "by_symbol": by_symbol[:8],
    }


def resync_ledger_to_broker(db: Session, settings: Settings, *, apply: bool = False) -> dict:
    """Dociąga NASZĄ bazę transakcji do realnych pozycji brokera (źródło prawdy).

    Dla każdej monety, gdzie baza myśli, że trzyma WIĘCEJ niż broker (phantom —
    jak HYPE: baza 2848 szt., broker 0), księguje syntetyczną transakcję
    uzgadniającą: SELL nadwyżki po cenie 0 = pełne spisanie kosztu phantomu w
    realized. Po tym netto bazy = saldo brokera, więc (a) watchdog widzi
    reconciled=True i silnik może wznowić, (b) realized P&L przestaje UKRYWAĆ
    stratę zjedzoną po stronie kupna (koniec z "+$1k" przy koncie −39%).

    Cena 0 (nie bieżący mark): pozycja u brokera ZNIKŁA, więc konserwatywnie
    zakładamy, że gotówka przepadła — realized dostaje pełny koszt phantomu.
    Wartość konta na pulpicie pochodzi i tak z brokera, więc to NIE zmienia
    wyświetlanego salda; prostuje tylko nasz wewnętrzny rachunek wyniku.

    apply=False (domyślnie): tylko PODGLĄD — nic nie zapisuje. Idempotentne:
    ponowne uruchomienie po uzgodnieniu = brak zmian. Rozjazd w DRUGĄ stronę
    (broker trzyma więcej niż baza) jest tylko RAPORTOWANY, nie zmyślamy kupna.
    """
    from datetime import UTC, datetime

    from app.models import TradeMode
    from app.services.trading_engine import average_cost_basis

    snap = _latest_crypto_snapshot(db)
    if snap is None:
        return {"applied": False, "reason": "brak snapshotu krypto", "adjustments": [], "total_loss_usd": 0.0}
    try:
        broker_bal = json.loads(snap.balances_json or "{}")
        prices = json.loads(snap.prices_json or "{}")
    except (TypeError, ValueError):
        return {"applied": False, "reason": "nieczytelny snapshot", "adjustments": [], "total_loss_usd": 0.0}

    rows = db.execute(
        select(Trade.symbol, Trade.side, Trade.quantity)
        .where(Trade.venue == "crypto")
        .order_by(Trade.id)
    ).all()
    ledger_qty: dict[str, float] = {}
    for sym, side, qty in rows:
        signed = qty if "BUY" in str(side).upper() else -qty
        ledger_qty[sym] = ledger_qty.get(sym, 0.0) + (signed or 0.0)

    adjustments: list[dict] = []
    reverse: list[dict] = []
    now = datetime.now(UTC)
    for sym, lq in ledger_qty.items():
        bq = float(broker_bal.get(sym, 0.0) or 0.0)
        excess = lq - bq
        price = float(prices.get(sym, 0.0) or 0.0)
        if excess * max(price, 1.0) < 1.0:
            # nadwyżka < ~$1 (albo baza <= broker). Rozjazd w drugą stronę -> raport.
            if (bq - lq) * max(price, 1.0) >= 1.0:
                reverse.append({"symbol": sym, "ledger_qty": round(lq, 6), "broker_qty": round(bq, 6)})
            continue
        # average_cost_basis dopasowuje po PEŁNYM symbolu (Trade.symbol == "HYPE/USD"),
        # nie po base — podajemy sym, nie _base_asset(sym).
        basis = average_cost_basis(db, sym, venue="crypto") or 0.0
        loss = round(excess * basis, 2)   # SELL po cenie 0 => realized = −(excess*basis)
        adjustments.append({
            "symbol": sym, "excess_qty": round(excess, 6),
            "avg_cost": round(basis, 6), "loss_usd": loss,
            "mark_now": round(price, 6),
        })
        if apply:
            db.add(Trade(
                timestamp=now, symbol=sym, side="SELL", quantity=excess, price=0.0,
                usdt_value=0.0, order_id=f"RESYNC-{sym}-{now.strftime('%Y%m%dT%H%M%S')}",
                mode=TradeMode.LIVE, is_manual=False, venue="crypto",
                pnl_usd=-loss, pnl_pct=-100.0 if basis > 0 else 0.0,
            ))

    total_loss = round(sum(a["loss_usd"] for a in adjustments), 2)
    if apply and adjustments:
        db.commit()
        try:
            risk_manager = __import__("app.services.risk_manager", fromlist=["_log_event"])
            risk_manager._log_event(
                db, "ledger_resync",
                f"Uzgodniono {len(adjustments)} pozycji z brokerem; spisano ${total_loss:,.0f} jako realized",
            )
        except Exception:  # pragma: no cover
            pass
    return {
        "applied": bool(apply and adjustments),
        "adjustments": adjustments,
        "reverse_divergence": reverse,
        "total_loss_usd": total_loss,
        "count": len(adjustments),
    }


def check_and_halt(db: Session, settings: Settings, *, account_total: float | None = None) -> dict | None:
    """WATCHDOG (R19/R26): gdy rozjazd baza↔broker przekracza próg, zatrzymaj
    handel (auto-halt) i zaalarmuj. Zwraca raport rekonsyliacji (albo None).

    To halt KONTA (nie blacklista monet): nie handlujemy, dopóki księgi nie
    zgadzają się z brokerem. Lepki — jak kill-switch dźwigni; zdejmuje go ręczny
    Wznów po rozwiązaniu desyncu (reset papierowego konta albo re-sync ledgera).
    """
    from app.services import risk_manager

    pct = float(getattr(settings, "crypto_reconciliation_halt_pct", 0.0) or 0.0)
    if pct <= 0:
        return None
    rec = ledger_vs_broker(db, settings, account_total=account_total)
    if rec is None or rec["reconciled"]:
        return rec

    state = risk_manager.get_state(db)
    if not state.is_halted:
        top = rec["by_symbol"][0] if rec["by_symbol"] else None
        detail = f" (głównie {top['symbol']}: ${top['diff_usd']:,.0f})" if top else ""
        state.is_halted = True
        state.halted_reason = (
            f"Rozjazd rekoncyliacji: baza vs broker różni się o ${rec['residual_usd']:,.0f}{detail} "
            f"— handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; "
            "rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)"
        )
        try:
            risk_manager._log_event(db, "reconciliation_halt", state.halted_reason)
        except Exception:  # pragma: no cover
            pass
        db.commit()
        db.refresh(state)
        try:
            from app.services import push_notifier

            push_notifier.send_alarm(
                db, settings,
                title="⛔ Automat ZATRZYMANY (rozjazd z brokerem)",
                body=state.halted_reason,
                tag="reconciliation-halt",
            )
        except Exception:  # pragma: no cover
            pass
    return rec
