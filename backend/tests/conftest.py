import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.db import Base
from app import models  # noqa: F401  (registers tables on Base)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def settings():
    return Settings(
        anthropic_api_key="test-key",
        alpaca_api_key="test-key",
        alpaca_api_secret="test-secret",
        alpaca_paper=True,
        quote_currency="USD",
        daily_loss_limit_pct=10.0,
        weekly_loss_limit_pct=20.0,
        max_position_pct=25.0,
        trading_whitelist="SPY,QQQ",
        poll_interval_minutes=15,
        price_move_trigger_pct=2.0,
        # Earnings guard off by default in tests; the dedicated earnings test
        # sets it explicitly. (The calendar lookup itself is mocked to {}.)
        earnings_blackout_days=0,
    )
