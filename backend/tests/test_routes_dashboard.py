import json
from datetime import datetime, timedelta, timezone

from app.api import routes_dashboard
from app.api.routes_dashboard import get_portfolio, get_status
from app.models import PortfolioSnapshot
from app.services import market_hours


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
