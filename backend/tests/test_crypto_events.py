"""Rdzeń reakcji na katalizatory (R1 hack-exit + dyscyplina shadow-first)."""
from types import SimpleNamespace

from app.services.crypto_events import (
    CryptoEvent,
    classify_severity,
    event_action,
)


def _settings(enabled=True, mode="act", exit_min=0.6, alert_min=0.3, unlock_days=3.0):
    return SimpleNamespace(
        crypto_event_response_enabled=enabled,
        crypto_event_action_mode=mode,
        crypto_event_exit_min_severity=exit_min,
        crypto_event_alert_min_severity=alert_min,
        crypto_event_unlock_block_days=unlock_days,
    )


def test_master_off_ignores_everything():
    ev = CryptoEvent(kind="hack", symbol="ETH", severity=0.99)
    d = event_action(ev, ["ETH/USD"], _settings(enabled=False))
    assert d.action == "ignore"
    assert d.acted is False


def test_hack_on_held_exits_in_act_mode():
    ev = CryptoEvent(kind="hack", symbol="ETH", severity=0.95)
    d = event_action(ev, ["ETH/USD", "BTC/USD"], _settings(mode="act"))
    assert d.action == "exit_now" and d.acted is True and d.symbol == "ETH"


def test_shadow_mode_downgrades_to_alert():
    # Ten sam hack, ale tryb alert_only -> tylko alarm, ZERO realnej akcji.
    ev = CryptoEvent(kind="hack", symbol="ETH", severity=0.95)
    d = event_action(ev, ["ETH/USD"], _settings(mode="alert_only"))
    assert d.action == "alert" and d.acted is False
    assert "alert_only" in d.reason


def test_hack_on_not_held_blocks_entry():
    ev = CryptoEvent(kind="exploit", symbol="SOL", severity=0.8)
    d = event_action(ev, ["ETH/USD"], _settings(mode="act"))
    assert d.action == "block_entry" and d.acted is True


def test_low_severity_hack_below_exit_threshold_is_alert_only():
    ev = CryptoEvent(kind="hack", symbol="ETH", severity=0.4)  # < exit_min 0.6
    d = event_action(ev, ["ETH/USD"], _settings(mode="act"))
    assert d.action == "alert" and d.acted is False  # alarm, nie wyjście


def test_unlock_near_blocks_entry():
    ev = CryptoEvent(kind="unlock", symbol="AVAX", severity=0.5, days_until=2.0)
    d = event_action(ev, [], _settings(mode="act", unlock_days=3.0))
    assert d.action == "block_entry"


def test_unlock_far_is_not_blocked():
    ev = CryptoEvent(kind="unlock", symbol="AVAX", severity=0.5, days_until=30.0)
    d = event_action(ev, [], _settings(mode="act", unlock_days=3.0))
    assert d.action != "block_entry"


def test_bullish_listing_only_alerts_never_buys():
    ev = CryptoEvent(kind="listing", symbol="DOGE", severity=0.6)
    d = event_action(ev, [], _settings(mode="act"))
    # Nigdy auto-kupno: zawsze alert, acted False, nawet w trybie 'act'.
    assert d.action == "alert" and d.acted is False


def test_noise_below_alert_threshold_ignored():
    ev = CryptoEvent(kind="outage", symbol="LTC", severity=0.1)
    d = event_action(ev, [], _settings(mode="act"))
    assert d.action == "ignore"


def test_classify_severity_keywords():
    assert classify_severity("Protocol X drained of $50M in exploit") >= 0.9
    assert classify_severity("Token unlock scheduled next week") == 0.5
    assert classify_severity("New Binance listing announced") == 0.4
    assert classify_severity("") == 0.0
