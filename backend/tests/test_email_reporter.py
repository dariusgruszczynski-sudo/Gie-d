from datetime import UTC, datetime, timedelta

from app.models import Decision, PortfolioSnapshot, TradeAction, TriggerType
from app.services import email_reporter


def test_build_report_is_crypto_primary_aggregate(db_session, settings):
    """Po przełączeniu na krypto dzienny raport jest WIDOKIEM ZBIORCZYM konta:
    główną nogą jest krypto, a RAZEM to pełna suma (gotówka raz + pozycje)."""
    crypto_settings = settings.model_copy(update={"crypto_enabled": True})
    now = datetime.now(UTC)
    # Jedno konto: gotówka identyczna w każdym snapshotcie; krypto trzyma $98k pozycji.
    db_session.add(PortfolioSnapshot(
        timestamp=now, total_value_usdt=99000.0, usdt_balance=1000.0,
        balances_json="{}", prices_json="{}", venue="crypto",
    ))
    db_session.add(
        Decision(
            timestamp=now, symbol="BTC/USD", action=TradeAction.BUY, reasoning="wejście BTC",
            triggered_by=TriggerType.MANUAL, executed=True, venue="crypto",
        )
    )
    db_session.commit()

    html, chart_png = email_reporter.build_report(db_session, crypto_settings)

    assert "KRYPTO" in html          # kubełek krypto jest nogą główną
    assert "$99,000.00" in html      # RAZEM = gotówka $1k + pozycje $98k
    assert "$98,000.00" in html      # wartość pozycji krypto
    assert "Krypto" in html          # tag nogi w aktywności
    assert isinstance(chart_png, bytes) and len(chart_png) > 0


def test_build_report_stocks_with_extended(db_session, settings):
    """Widok akcji + poza sesją: gotówka liczona RAZ, pozycje per noga."""
    stock_settings = settings.model_copy(update={"extended_enabled": True, "crypto_enabled": False})
    now = datetime.now(UTC)
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=100.0, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now + timedelta(seconds=1), total_value_usdt=140.0, usdt_balance=100.0, venue="extended"))
    db_session.commit()

    html, _ = email_reporter.build_report(db_session, stock_settings)

    # gotówka $100 (raz) + akcje $400 + poza sesją $40 = $540
    assert "$540.00" in html
    assert "AKCJE US" in html
    assert "Poza sesją" in html or "POZA SESJĄ" in html


def test_build_report_handles_extended_disabled(db_session, settings):
    stock_settings = settings.model_copy(update={"extended_enabled": False, "crypto_enabled": False})
    now = datetime.now(UTC)
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=100.0, venue="alpaca"))
    db_session.commit()

    html, _ = email_reporter.build_report(db_session, stock_settings)
    assert "$500.00" in html          # gotówka $100 + akcje $400
    assert "AKCJE US" in html
