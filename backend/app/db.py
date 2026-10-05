import os

from sqlalchemy import create_engine, event, inspect, text
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

# SQLite + wiele wątków (scheduler, wątek primingu, requesty) pisze do jednego
# pliku. Bez WAL i busy_timeout współbieżny zapis sypie „database is locked".
# WAL = równoległe czytanie w trakcie zapisu; busy_timeout = czekaj (nie rzucaj)
# gdy plik chwilowo zajęty; synchronous=NORMAL = bezpieczny i szybki pod WAL.
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _record):  # pragma: no cover - zależne od sterownika
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=5000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

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
    _add_column_if_missing("system_state", "claude_monthly_budget_override", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "claude_input_tokens_this_month", "INTEGER", "0")
    _add_column_if_missing("system_state", "claude_output_tokens_this_month", "INTEGER", "0")
    _add_column_if_missing("system_state", "last_check_prices_json", "TEXT", "'{}'")
    _add_column_if_missing("portfolio_snapshots", "balances_json", "TEXT", "'{}'")
    _add_column_if_missing("portfolio_snapshots", "prices_json", "TEXT", "'{}'")
    _add_column_if_missing("decisions", "market_context_snapshot", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "session_secret", "VARCHAR(64)", "''")
    _add_column_if_missing("portfolio_snapshots", "failed_symbols_json", "TEXT", "'[]'")
    _add_column_if_missing("system_state", "stop_loss_cooldowns_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "position_peaks_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "partial_tp_taken_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_partial_tp_taken_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "stop_loss_streak_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_stop_loss_streak_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "seen_ticker_headlines_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "benchmark_start_date", "VARCHAR(10)", "''")
    _add_column_if_missing("system_state", "benchmark_start_price", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "benchmark_start_value", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "deposits_usd_lifetime", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "knob_overrides_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "opus_controller_enabled", "BOOLEAN", "0")
    _add_column_if_missing("system_state", "opus_controller_user_set", "BOOLEAN", "0")
    _add_column_if_missing("system_state", "opus_controller_last_run", "VARCHAR(10)", "''")
    _add_column_if_missing("system_state", "opus_knowledge_json", "TEXT", "'[]'")
    _add_column_if_missing("system_state", "lessons_json", "TEXT", "'[]'")
    _add_column_if_missing("system_state", "last_self_review_date", "VARCHAR(10)", "''")
    _add_column_if_missing("system_state", "last_analysis_at", "VARCHAR(32)", "''")
    # Two lots on one Alpaca account: tag each record with its venue (existing
    # rows -> "alpaca") and give the extended venue its own isolated per-cycle
    # state columns.
    _add_column_if_missing("decisions", "venue", "VARCHAR(16)", "'alpaca'")
    _add_column_if_missing("trades", "venue", "VARCHAR(16)", "'alpaca'")
    _add_column_if_missing("portfolio_snapshots", "venue", "VARCHAR(16)", "'alpaca'")
    _add_column_if_missing("system_state", "extended_check_prices_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_position_peaks_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_stop_loss_cooldowns_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_seen_ticker_headlines_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_analysis_state_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_paused", "BOOLEAN", "1")
    _add_column_if_missing("system_state", "market_regime_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_market_regime_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "extended_whitelist_json", "TEXT", "''")
    # Crypto (24/7) venue: its own isolated per-cycle state columns (same shapes
    # as extended), so enabling crypto never touches the equities/extended paths.
    _add_column_if_missing("system_state", "crypto_paused", "BOOLEAN", "1")
    _add_column_if_missing("system_state", "crypto_check_prices_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_position_peaks_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_stop_loss_cooldowns_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_seen_ticker_headlines_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_partial_tp_taken_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_stop_loss_streak_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_analysis_state_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "crypto_market_regime_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "peak_account_value", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "pending_peak_value", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "pending_peak_confirmations", "INTEGER", "0")
    _add_column_if_missing("system_state", "claude_spend_usd_lifetime", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "discovered_feeds_json", "TEXT", "'[]'")
    _add_column_if_missing("system_state", "discovered_feeds_meta_json", "TEXT", "'{}'")
    _add_column_if_missing("system_state", "stats_epoch", "VARCHAR(32)", "''")
    _add_column_if_missing("system_state", "push_mode", "VARCHAR(8)", "'all'")
    _add_column_if_missing("system_state", "day_pnl_alert_stamp", "VARCHAR(16)", "''")
    _add_column_if_missing("system_state", "monthly_deposit_plan", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "goal_amount", "FLOAT", "0.0")
    _add_column_if_missing("system_state", "widget_metric", "VARCHAR(12)", "'total'")
    _add_column_if_missing("system_state", "exit_overrides_json", "TEXT", "'{}'")
    # One-time backfill for deployments upgrading from before the lifetime
    # counter existed: seed it from this month's already-tracked spend instead
    # of a misleadingly-clean 0 (still misses months before this one, but
    # closer than nothing). Idempotent -- a no-op once real usage has grown it.
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE system_state SET claude_spend_usd_lifetime = claude_spend_usd_this_month "
                "WHERE claude_spend_usd_lifetime = 0 AND claude_spend_usd_this_month > 0"
            )
        )
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
    _ensure_hot_indexes()
    _seed_stopped_state_on_fresh_deploy()


def _ensure_hot_indexes() -> None:
    """Indeksy pod gorące zapytania pulpitu (filtr po venue + sort po timestamp).
    create_all nie dodaje indeksów do ISTNIEJĄCYCH tabel, więc dokładamy je tu
    ręcznie (IF NOT EXISTS -> idempotentne). Bez nich rosnąca historia trade'ów/
    decyzji/snapshotów liniowo spowalnia każde odświeżenie dashboardu."""
    index_ddls = (
        "CREATE INDEX IF NOT EXISTS ix_trades_venue_ts ON trades (venue, timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_decisions_venue_ts ON decisions (venue, timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_snapshots_venue_ts ON portfolio_snapshots (venue, timestamp)",
    )
    existing = set(inspect(engine).get_table_names())
    needed = {"trades", "decisions", "portfolio_snapshots"}
    if not needed.issubset(existing):
        return
    with engine.begin() as conn:
        for ddl in index_ddls:
            conn.execute(text(ddl))


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
