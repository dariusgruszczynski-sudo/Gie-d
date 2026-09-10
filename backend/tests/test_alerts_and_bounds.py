"""P14 (guard zakresów knobów), P15 (alert bezczynności), P8 (alert shadow)."""

from datetime import UTC, datetime, timedelta

from app.models import PortfolioSnapshot, Trade, TradeMode
from app.services import opus_controller, push_notifier, shadow_analysis


# --- P14: klamry Opusa nie mogą dopuścić do ruiny --------------------------
def test_knob_bounds_are_non_ruinous():
    ak = opus_controller.ALLOWED_KNOBS
    assert ak["risk_per_trade_pct"][1] <= 6.0 and ak["risk_per_trade_pct"][0] >= 0.5
    assert ak["conviction_max_risk_per_trade_pct"][1] <= 8.0
    assert ak["stop_loss_min_pct"][0] >= 1.0
    assert ak["min_buy_confidence"][0] >= 0.30
    for name, (lo, hi, _is_int) in ak.items():
        assert lo < hi, f"zły zakres dla {name}"


# --- P15: alert bezczynności -----------------------------------------------
def _patch_push(monkeypatch):
    monkeypatch.setattr(push_notifier, "push_configured", lambda s: True)
    sent = []
    monkeypatch.setattr(push_notifier, "send_alarm", lambda db, s, **k: sent.append(k) or 1)
    return sent


def test_idle_alert_fires_when_no_entries(db_session, settings, monkeypatch):
    sent = _patch_push(monkeypatch)
    # brak jakiegokolwiek BUY -> idle_days ogromne -> alarm
    assert push_notifier.check_idle_alert(db_session, settings) is True
    assert sent and sent[0]["tag"] == "idle"


def test_idle_alert_quiet_when_active_and_low_cash(db_session, settings, monkeypatch):
    _patch_push(monkeypatch)
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="SPY", side="BUY", quantity=1, price=100.0,
                         usdt_value=100.0, mode=TradeMode.LIVE, venue="alpaca"))
    db_session.add(PortfolioSnapshot(venue="alpaca", timestamp=now, total_value_usdt=1000.0,
                                     usdt_balance=100.0, balances_json="{}", prices_json="{}"))
    db_session.commit()
    # świeże wejście + gotówka 10% -> brak alarmu
    assert push_notifier.check_idle_alert(db_session, settings) is False


def test_idle_alert_fires_on_high_cash(db_session, settings, monkeypatch):
    sent = _patch_push(monkeypatch)
    now = datetime.now(UTC)
    db_session.add(Trade(timestamp=now, symbol="SPY", side="BUY", quantity=1, price=100.0,
                         usdt_value=100.0, mode=TradeMode.LIVE, venue="alpaca"))
    db_session.add(PortfolioSnapshot(venue="alpaca", timestamp=now, total_value_usdt=1000.0,
                                     usdt_balance=800.0, balances_json="{}", prices_json="{}"))
    db_session.commit()
    # świeże wejście, ale gotówka 80% (>60) -> alarm
    assert push_notifier.check_idle_alert(db_session, settings) is True
    assert sent[0]["tag"] == "idle"


# --- P8: alert, gdy Claude przegrywa z mechaniką ---------------------------
def test_shadow_alert_fires_when_claude_underperforms(db_session, settings, monkeypatch):
    sent = _patch_push(monkeypatch)
    monkeypatch.setattr(shadow_analysis, "compute_claude_edge", lambda db, s, **k: {
        "mechanical_only": {"closed_trades": 50, "win_rate_pct": 67},
        "with_claude": {"closed_trades": 40, "win_rate_pct": 26},
    })
    assert push_notifier.check_shadow_underperformance(db_session, settings) is True
    assert sent[0]["tag"] == "shadow"


def test_shadow_alert_quiet_on_small_sample(db_session, settings, monkeypatch):
    _patch_push(monkeypatch)
    monkeypatch.setattr(shadow_analysis, "compute_claude_edge", lambda db, s, **k: {
        "mechanical_only": {"closed_trades": 5, "win_rate_pct": 67},
        "with_claude": {"closed_trades": 4, "win_rate_pct": 26},
    })
    assert push_notifier.check_shadow_underperformance(db_session, settings) is False
