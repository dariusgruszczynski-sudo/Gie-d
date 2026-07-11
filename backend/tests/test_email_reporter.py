from datetime import datetime, timezone

from app.models import Decision, PortfolioSnapshot, TradeAction, TriggerType
from app.services import email_reporter


def test_build_report_renders_both_portfolios(db_session, settings):
    crypto_settings = settings.model_copy(update={"crypto_enabled": True})
    now = datetime.now(timezone.utc)
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=100.0, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=42.0, usdt_balance=42.0, venue="crypto"))
    db_session.add(
        Decision(
            timestamp=now, symbol="BTCUSD", action=TradeAction.BUY, reasoning="krypto",
            triggered_by=TriggerType.MANUAL, executed=True, venue="crypto",
        )
    )
    db_session.commit()

    html, chart_png = email_reporter.build_report(db_session, crypto_settings)

    assert "$500.00" in html
    assert "$42.00" in html
    assert "$542.00" in html
    assert "Krypto" in html
    assert isinstance(chart_png, bytes) and len(chart_png) > 0


def test_build_report_handles_crypto_disabled(db_session, settings):
    crypto_disabled = settings.model_copy(update={"crypto_enabled": False})
    now = datetime.now(timezone.utc)
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=100.0, venue="alpaca"))
    db_session.commit()

    html, _ = email_reporter.build_report(db_session, crypto_disabled)
    assert "$500.00" in html
    assert "wyłączony" in html
