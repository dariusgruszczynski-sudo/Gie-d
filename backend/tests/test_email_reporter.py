from unittest.mock import MagicMock, patch

from app.models import Decision, PortfolioSnapshot, TradeAction, TriggerType
from app.services import email_reporter


def test_build_report_handles_empty_db(db_session, settings):
    html, png = email_reporter.build_report(db_session, settings)
    assert "<div" in html
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_build_report_includes_latest_decision_reasoning(db_session, settings):
    db_session.add(PortfolioSnapshot(total_value_usdt=1050.0, usdt_balance=500))
    db_session.add(
        Decision(
            action=TradeAction.BUY,
            symbol="BTCUSDT",
            size_pct=10,
            confidence=0.8,
            reasoning="Silny trend wzrostowy, kupujemy.",
            triggered_by=TriggerType.PRICE_MOVE,
            executed=True,
        )
    )
    db_session.commit()

    html, _ = email_reporter.build_report(db_session, settings)
    assert "Silny trend wzrostowy" in html
    assert "BTCUSDT" in html


def test_send_daily_report_skips_without_smtp_credentials(db_session, settings):
    settings.smtp_username = ""
    settings.smtp_password = ""
    with patch("smtplib.SMTP") as mock_smtp:
        email_reporter.send_daily_report(db_session, settings)
    mock_smtp.assert_not_called()


def test_send_daily_report_sends_via_smtp(db_session, settings):
    settings.smtp_username = "bot@gmail.com"
    settings.smtp_password = "app-password"
    settings.smtp_from_email = "bot@gmail.com"

    mock_server = MagicMock()
    mock_server.__enter__.return_value = mock_server
    with patch("smtplib.SMTP", return_value=mock_server) as mock_smtp:
        email_reporter.send_daily_report(db_session, settings)

    mock_smtp.assert_called_once_with(settings.smtp_host, settings.smtp_port, timeout=30)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("bot@gmail.com", "app-password")
    mock_server.send_message.assert_called_once()
