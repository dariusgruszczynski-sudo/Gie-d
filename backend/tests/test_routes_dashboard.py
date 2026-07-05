import json
from datetime import datetime, timedelta, timezone

from app.api.routes_dashboard import get_portfolio
from app.models import PortfolioSnapshot


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
                prices_json=json.dumps({"BTCUSDT": 50000.0 + i * 100}),
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
