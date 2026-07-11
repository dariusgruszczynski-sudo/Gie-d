import json
from datetime import datetime, timedelta, timezone

from app.api import routes_dashboard
from app.api.routes_dashboard import _account_view, get_portfolio, get_status
from app.models import PortfolioSnapshot
from app.services import market_hours


def test_account_view_counts_shared_cash_once(db_session):
    """One Alpaca account, two engines: both per-engine snapshots record the
    SAME account cash. The account view must count that cash ONCE plus each
    engine's position value -- not sum the two snapshot totals (which would
    double-count the cash, the "two portfolios" bug)."""
    now = datetime.now(timezone.utc)
    # cash=100 in both; equities holds 50 of positions, crypto holds 30.
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=150.0, usdt_balance=100.0, venue="alpaca"))
    db_session.add(PortfolioSnapshot(timestamp=now, total_value_usdt=130.0, usdt_balance=100.0, venue="crypto"))
    db_session.commit()

    acc = _account_view(db_session)
    assert acc["cash"] == 100.0
    assert acc["equity_positions_value"] == 50.0
    assert acc["crypto_positions_value"] == 30.0
    # 100 + 50 + 30 = 180, NOT 150 + 130 = 280 (cash counted once).
    assert acc["total_value"] == 180.0


def test_account_view_none_when_no_snapshots(db_session):
    assert _account_view(db_session) is None


def test_portfolio_venue_filter_separates_portfolios(db_session, settings):
    """/api/portfolio?venue=... must return only that venue's snapshots, so the
    equities and crypto portfolios never bleed into each other on the dashboard."""
    now = datetime.now(timezone.utc)
    db_session.add(
        PortfolioSnapshot(timestamp=now, total_value_usdt=500.0, usdt_balance=500.0, venue="alpaca")
    )
    db_session.add(
        PortfolioSnapshot(timestamp=now, total_value_usdt=42.0, usdt_balance=42.0, venue="crypto")
    )
    db_session.commit()

    alpaca = get_portfolio(limit=200, venue="alpaca", db=db_session, settings=settings)
    crypto = get_portfolio(limit=200, venue="crypto", db=db_session, settings=settings)

    assert alpaca["current"]["total_value_usdt"] == 500.0
    assert crypto["current"]["total_value_usdt"] == 42.0
    assert crypto["scorecard"] is None  # crypto venue has no SPY scorecard


def test_portfolio_inception_is_the_very_first_snapshot_even_beyond_limit(db_session, settings):
    """/api/portfolio's `limit` truncates `history`, but `inception` must
    still reflect the true first-ever snapshot so "since the beginning" P&L
    doesn't quietly drift once more than `limit` snapshots have accumulated."""
    base = datetime.now(timezone.utc) - timedelta(days=10)
    for i in range(5):
        db_session.add(
            PortfolioSnapshot(
                timestamp=base + timedelta(hours=i),
                total_value_usdt=1000.0 + i * 10,
                usdt_balance=1000.0,
                balances_json="{}",
                prices_json=json.dumps({"SPY": 50000.0 + i * 100}),
            )
        )
    db_session.commit()

    body = get_portfolio(limit=2, db=db_session, settings=settings)

    assert len(body["history"]) == 2
    assert body["inception"] is not None
    assert body["inception"]["total_value_usdt"] == 1000.0


def test_portfolio_inception_is_none_when_no_snapshots_exist(db_session, settings):
    body = get_portfolio(limit=200, db=db_session, settings=settings)
    assert body["current"] is None
    assert body["inception"] is None


def test_status_includes_market_session_and_bounds(db_session, settings, monkeypatch):
    now = datetime.now(market_hours.ET)
    info = market_hours.SessionInfo(
        session=market_hours.REGULAR,
        regular_open=now,
        regular_close=now,
    )
    monkeypatch.setattr(routes_dashboard.market_hours, "get_session_info", lambda broker: info)

    body = get_status(db=db_session, settings=settings)

    assert body["market_session"] == "regular"
    assert body["session_bounds"]["regular_open"] == now.isoformat()


def test_status_degrades_gracefully_when_session_lookup_fails(db_session, settings, monkeypatch):
    def failing_get_session_info(broker):
        raise RuntimeError("Alpaca calendar unavailable")

    monkeypatch.setattr(routes_dashboard.market_hours, "get_session_info", failing_get_session_info)

    body = get_status(db=db_session, settings=settings)

    assert body["market_session"] is None
    assert body["session_bounds"] is None
    # The rest of the endpoint must still work despite the session lookup failure.
    assert "is_paused" in body
