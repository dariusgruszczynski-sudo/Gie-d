import os

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

if settings.database_url.startswith("sqlite:///./"):
    db_path = settings.database_url.replace("sqlite:///./", "")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _add_column_if_missing(table: str, column: str, ddl_type: str, default_sql: str) -> None:
    """SQLAlchemy's create_all only creates missing tables, never alters existing
    ones -- this adds newly-introduced columns to a pre-existing SQLite DB file
    so upgrading the app in place doesn't crash on 'no such column'."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    if column in existing:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type} DEFAULT {default_sql}"))


def _drop_column_if_exists(table: str, column: str) -> None:
    """Removes a dead column left over from an old schema. Needed (not just
    cosmetic) when the column is NOT NULL with no server-side DEFAULT in the
    actual SQLite DDL -- the current model's INSERT no longer supplies it,
    which makes every insert into that table fail with an IntegrityError.
    Requires SQLite >= 3.35 (2021), bundled with Python 3.12."""
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns(table)}
    if column not in existing:
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} DROP COLUMN {column}"))


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _add_column_if_missing("system_state", "claude_budget_month_key", "VARCHAR(7)", "''")
    _add_column_if_missing("system_state", "claude_spend_usd_this_month", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "last_check_prices_json", "TEXT", "'{}'")
    _add_column_if_missing("portfolio_snapshots", "balances_json", "TEXT", "'{}'")
    _add_column_if_missing("portfolio_snapshots", "prices_json", "TEXT", "'{}'")
    _add_column_if_missing("decisions", "market_context_snapshot", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "session_secret", "VARCHAR(64)", "''")
    _add_column_if_missing("portfolio_snapshots", "failed_symbols_json", "TEXT", "'[]'")
    # Dead columns from the pre-generic-whitelist schema (superseded by
    # balances_json/prices_json/last_check_prices_json) -- NOT NULL with no
    # DB-level default, so they broke every insert once the ORM stopped
    # supplying them.
    _drop_column_if_exists("portfolio_snapshots", "btc_balance")
    _drop_column_if_exists("portfolio_snapshots", "eth_balance")
    _drop_column_if_exists("portfolio_snapshots", "btc_price")
    _drop_column_if_exists("portfolio_snapshots", "eth_price")
    _drop_column_if_exists("system_state", "last_btc_check_price")
    _drop_column_if_exists("system_state", "last_eth_check_price")
    _seed_stopped_state_on_fresh_deploy()


def seed_stopped_state(session) -> None:
    """Live-money safety: a brand-new deployment must sit STOPPED until the
    human explicitly presses START in the dashboard -- never place a real
    order on its own before that. Seeds the singleton SystemState with
    is_paused=True only when it doesn't exist yet; an existing (possibly
    running) state is left untouched on restart, so a restart never silently
    re-pauses a bot the user had already started. Tests use in-memory DBs and
    never call init_db(), so their model-default (is_paused=False, i.e. active)
    behaviour is unaffected unless they call this explicitly."""
    from datetime import date

    from app.models import SystemState

    if session.get(SystemState, 1) is None:
        today = date.today().isoformat()
        session.add(SystemState(id=1, is_paused=True, day_start_date=today, week_start_date=today))
        session.commit()


def _seed_stopped_state_on_fresh_deploy() -> None:
    with SessionLocal() as session:
        seed_stopped_state(session)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
