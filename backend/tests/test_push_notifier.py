import json
from datetime import UTC, datetime, timezone

import pytest

from app.models import PortfolioSnapshot, PushSubscription, Trade, TradeMode
from app.services import push_notifier


@pytest.fixture
def push_settings(settings):
    return settings.model_copy(update={
        "push_enabled": True,
        "vapid_public_key": "pub",
        "vapid_private_key": "priv",
    })


@pytest.fixture(autouse=True)
def fake_pywebpush(monkeypatch):
    """pywebpush may not be installed in this environment -- fake it so the
    actual send path is exercised, not just the "not configured" short-circuit."""
    monkeypatch.setattr(push_notifier, "_HAVE_PYWEBPUSH", True)
    calls = []

    def fake_webpush(*, subscription_info, data, vapid_private_key, vapid_claims, ttl):
        calls.append(json.loads(data))

    monkeypatch.setattr(push_notifier, "webpush", fake_webpush)
    return calls


def test_push_not_configured_without_keys(settings):
    assert push_notifier.push_configured(settings) is False


def test_push_configured_with_keys(push_settings):
    assert push_notifier.push_configured(push_settings) is True


def test_send_to_all_delivers_to_every_subscription(db_session, push_settings, fake_pywebpush):
    db_session.add(PushSubscription(endpoint="https://push/1", p256dh="a", auth="b"))
    db_session.add(PushSubscription(endpoint="https://push/2", p256dh="c", auth="d"))
    db_session.commit()

    sent = push_notifier.send_to_all(db_session, push_settings, title="t", body="b")

    assert sent == 2
    assert len(fake_pywebpush) == 2


def test_send_trade_push_includes_symbol(db_session, push_settings, fake_pywebpush):
    db_session.add(PushSubscription(endpoint="https://push/1", p256dh="a", auth="b"))
    db_session.commit()
    trade = Trade(
        symbol="SPY", side="BUY", quantity=1, price=100.0, usdt_value=100.0,
        mode=TradeMode.LIVE, venue="alpaca",
    )
    trade.id = 1

    push_notifier.send_trade_push(db_session, push_settings, trade, account_total=1000.0)

    assert len(fake_pywebpush) == 1
    assert "SPY" in fake_pywebpush[0]["title"]


def test_daily_summary_push_false_when_no_snapshots(db_session, push_settings):
    assert push_notifier.send_daily_summary_push(db_session, push_settings) is False


def test_daily_summary_push_sends_account_total(db_session, push_settings, fake_pywebpush):
    db_session.add(PushSubscription(endpoint="https://push/1", p256dh="a", auth="b"))
    now = datetime.now(UTC)
    db_session.add(PortfolioSnapshot(
        timestamp=now, total_value_usdt=1150.0, usdt_balance=1000.0,
        balances_json=json.dumps({"SPY": 1.0}), venue="alpaca",
    ))
    db_session.commit()

    sent = push_notifier.send_daily_summary_push(db_session, push_settings)

    assert sent is True
    assert len(fake_pywebpush) == 1
    assert "1,150" in fake_pywebpush[0]["title"]
    assert "Akcje US: 1 poz." in fake_pywebpush[0]["body"]
