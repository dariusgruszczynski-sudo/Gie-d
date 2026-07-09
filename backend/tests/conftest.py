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
        # New profit/risk guards (Pakiet 1-4) default OFF here so the many
        # existing exit/cycle tests keep their original behaviour; each
        # dedicated test enables exactly the one it exercises via model_copy.
        min_buy_confidence=0.0,
        max_new_positions_per_day=0,
        min_hold_minutes=0,
        partial_take_profit_enabled=False,
        risk_per_trade_pct=0.0,
        regime_gate_enabled=False,
        auto_blacklist_stop_count=0,
    )
