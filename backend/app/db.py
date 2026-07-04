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


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _add_column_if_missing("system_state", "claude_budget_month_key", "VARCHAR(7)", "''")
    _add_column_if_missing("system_state", "claude_spend_usd_this_month", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "last_check_prices_json", "TEXT", "'{}'")
    _add_column_if_missing("portfolio_snapshots", "balances_json", "TEXT", "'{}'")
    _add_column_if_missing("portfolio_snapshots", "prices_json", "TEXT", "'{}'")
    _add_column_if_missing("decisions", "market_context_snapshot", "TEXT", "'{}'")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
