from datetime import datetime, timezone

from app.models import Decision, PortfolioSnapshot, TradeAction, TriggerType
from app.services import email_reporter


def test_build_report_renders_both_portfolios(db_session, settings):
    etoro_settings = settings.model_copy(update={"etoro_enabled": True})
    now = datetime.now(timezone.utc)
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=100.0, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=42.0, usdt_balance=42.0, venue="etoro"))
    db_session.add(
        Decision(
            timestamp=now, symbol="BTC", action=TradeAction.BUY, reasoning="krypto",
            triggered_by=TriggerType.MANUAL, executed=True, venue="etoro",
        )
    )
    db_session.commit()

    html, chart_png = email_reporter.build_report(db_session, etoro_settings)

    assert "$500.00" in html
    assert "$42.00" in html
    assert "$542.00" in html
    assert "eToro" in html
    assert isinstance(chart_png, bytes) and len(chart_png) > 0


def test_build_report_handles_etoro_disabled(db_session, settings):
    now = datetime.now(timezone.utc)
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=100.0, venue="alpaca"))
    db_session.commit()

    html, _ = email_reporter.build_report(db_session, settings)
    assert "$500.00" in html
    assert "wyłączony" in html
