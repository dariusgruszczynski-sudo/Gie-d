"""Testy watchdoga rekoncyliacji baza↔broker (R19/R24/R26, meta-analiza 2026-11-09)."""

import json
from datetime import UTC, datetime

from app.models import PortfolioSnapshot, Trade, TradeMode
from app.services import reconciliation, risk_manager


def _crypto_settings(settings, **over):
    base = {"crypto_enabled": True, "quote_currency": "USD",
            "crypto_reconciliation_halt_pct": 1.0, "crypto_reconciliation_halt_floor_usd": 2000.0}
    base.update(over)
    return settings.model_copy(update=base)


def test_ledger_vs_broker_flags_divergence(db_session, settings):
    """Baza myśli, że trzyma HYPE, broker ma 0 -> rozjazd, reconciled=False."""
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="HYPE/USD", side="BUY", quantity=100.0,
                         price=80.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=2000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({}),
                                     prices_json=json.dumps({"HYPE/USD": 80.0}), venue="crypto"))
    db_session.commit()
    rec = reconciliation.ledger_vs_broker(db_session, _crypto_settings(settings), account_total=2000.0)
    assert rec is not None
    assert rec["residual_usd"] == 8000.0
    assert rec["reconciled"] is False
    assert rec["by_symbol"][0]["symbol"] == "HYPE/USD"


def test_ledger_vs_broker_ok_when_matched(db_session, settings):
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="BTC/USD", side="BUY", quantity=0.1,
                         price=80000.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=10000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({"BTC/USD": 0.1}),
                                     prices_json=json.dumps({"BTC/USD": 80000.0}), venue="crypto"))
    db_session.commit()
    rec = reconciliation.ledger_vs_broker(db_session, _crypto_settings(settings), account_total=10000.0)
    assert rec["reconciled"] is True
    assert rec["residual_usd"] == 0.0


def test_check_and_halt_trips_halt_on_divergence(db_session, settings):
    """Watchdog: rozjazd > próg -> is_halted=True z powodem rekoncyliacji."""
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="HYPE/USD", side="BUY", quantity=100.0,
                         price=80.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=2000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({}),
                                     prices_json=json.dumps({"HYPE/USD": 80.0}), venue="crypto"))
    db_session.commit()
    assert risk_manager.get_state(db_session).is_halted is False
    reconciliation.check_and_halt(db_session, _crypto_settings(settings), account_total=2000.0)
    state = risk_manager.get_state(db_session)
    assert state.is_halted is True
    assert "rekoncyliacji" in (state.halted_reason or "").lower()


def test_check_and_halt_noop_when_reconciled(db_session, settings):
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="BTC/USD", side="BUY", quantity=0.1,
                         price=80000.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=10000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({"BTC/USD": 0.1}),
                                     prices_json=json.dumps({"BTC/USD": 80000.0}), venue="crypto"))
    db_session.commit()
    reconciliation.check_and_halt(db_session, _crypto_settings(settings), account_total=10000.0)
    assert risk_manager.get_state(db_session).is_halted is False


def test_check_and_halt_disabled_when_pct_zero(db_session, settings):
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="HYPE/USD", side="BUY", quantity=100.0,
                         price=80.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=2000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({}),
                                     prices_json=json.dumps({"HYPE/USD": 80.0}), venue="crypto"))
    db_session.commit()
    reconciliation.check_and_halt(db_session, _crypto_settings(settings, crypto_reconciliation_halt_pct=0.0),
                                  account_total=2000.0)
    assert risk_manager.get_state(db_session).is_halted is False


# --- R24/R25: narzędzie re-sync (uzgodnienie bazy z brokerem) ---

def _phantom_setup(db_session):
    """Baza: kupiono 100 HYPE @ koszt $80 (usdt_value 8000). Broker: 0 HYPE."""
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="HYPE/USD", side="BUY", quantity=100.0,
                         price=80.0, usdt_value=8000.0, mode=TradeMode.LIVE, venue="crypto"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=2000.0, usdt_balance=2000.0,
                                     balances_json=json.dumps({}),
                                     prices_json=json.dumps({"HYPE/USD": 80.0}), venue="crypto"))
    db_session.commit()


def test_resync_preview_does_not_write(db_session, settings):
    _phantom_setup(db_session)
    before = db_session.query(Trade).count()
    rep = reconciliation.resync_ledger_to_broker(db_session, _crypto_settings(settings), apply=False)
    assert rep["applied"] is False
    assert rep["count"] == 1
    assert rep["adjustments"][0]["symbol"] == "HYPE/USD"
    assert rep["adjustments"][0]["excess_qty"] == 100.0
    assert rep["total_loss_usd"] == 8000.0
    assert db_session.query(Trade).count() == before  # nic nie zapisane


def test_resync_apply_books_and_reconciles(db_session, settings):
    _phantom_setup(db_session)
    cs = _crypto_settings(settings)
    assert reconciliation.ledger_vs_broker(db_session, cs, account_total=2000.0)["reconciled"] is False
    rep = reconciliation.resync_ledger_to_broker(db_session, cs, apply=True)
    assert rep["applied"] is True
    assert rep["total_loss_usd"] == 8000.0
    # Po uzgodnieniu: netto bazy = broker (0 HYPE) -> reconciled True.
    rec = reconciliation.ledger_vs_broker(db_session, cs, account_total=2000.0)
    assert rec["reconciled"] is True
    assert abs(rec["residual_usd"]) < 1.0
    # Zaksięgowano syntetyczną transakcję uzgadniającą ze stratą.
    adj = db_session.query(Trade).filter(Trade.order_id.like("RESYNC-%")).all()
    assert len(adj) == 1
    assert adj[0].pnl_usd == -8000.0


def test_resync_idempotent(db_session, settings):
    _phantom_setup(db_session)
    cs = _crypto_settings(settings)
    reconciliation.resync_ledger_to_broker(db_session, cs, apply=True)
    # Drugie uruchomienie: już uzgodnione -> brak nowych transakcji.
    rep2 = reconciliation.resync_ledger_to_broker(db_session, cs, apply=True)
    assert rep2["count"] == 0
    assert rep2["applied"] is False
