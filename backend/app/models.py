import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TradeAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TriggerType(str, enum.Enum):
    PRICE_MOVE = "price_move"
    SCHEDULED_DAILY = "scheduled_daily"
    MANUAL = "manual"


class TradeMode(str, enum.Enum):
    TESTNET = "testnet"
    LIVE = "live"


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    symbol: Mapped[str | None] = mapped_column(String(20), nullable=True)
    action: Mapped[TradeAction] = mapped_column(Enum(TradeAction))
    size_pct: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    market_data_snapshot: Mapped[str] = mapped_column(Text, default="{}")
    news_snapshot: Mapped[str] = mapped_column(Text, default="[]")
    market_context_snapshot: Mapped[str] = mapped_column(Text, default="{}")
    triggered_by: Mapped[TriggerType] = mapped_column(Enum(TriggerType), default=TriggerType.SCHEDULED_DAILY)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    trades: Mapped[list["Trade"]] = relationship(back_populates="decision")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    symbol: Mapped[str] = mapped_column(String(20))
    side: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    usdt_value: Mapped[float] = mapped_column(Float)
    order_id: Mapped[str] = mapped_column(String(64), default="")
    mode: Mapped[TradeMode] = mapped_column(Enum(TradeMode))
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False)

    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id"), nullable=True)
    decision: Mapped[Decision | None] = relationship(back_populates="trades")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    total_value_usdt: Mapped[float] = mapped_column(Float)
    usdt_balance: Mapped[float] = mapped_column(Float)
    # JSON dicts keyed by base asset ("XBT", "SOL", ...) / trading pair
    # ("XBTEUR", ...) so the whitelist can hold any number of coins without
    # a schema change per coin.
    balances_json: Mapped[str] = mapped_column(Text, default="{}")
    prices_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON list of whitelist symbols that failed to price this cycle (network
    # hiccup, delisted pair, ...) -- lets the dashboard tell "genuinely
    # unavailable" apart from "just hasn't loaded yet" instead of showing
    # "oczekiwanie na dane" forever.
    failed_symbols_json: Mapped[str] = mapped_column(Text, default="[]")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    details: Mapped[str] = mapped_column(Text, default="")


class SystemState(Base):
    """Singleton row (id=1) holding global mutable trading state."""

    __tablename__ = "system_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    is_halted: Mapped[bool] = mapped_column(Boolean, default=False)
    halted_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    day_start_date: Mapped[str] = mapped_column(String(10), default="")
    day_start_value: Mapped[float] = mapped_column(Float, default=0.0)
    week_start_date: Mapped[str] = mapped_column(String(10), default="")
    week_start_value: Mapped[float] = mapped_column(Float, default=0.0)
    # JSON dict keyed by trading pair ("BTCUSDT", ...) -> last observed price,
    # so the price-move trigger works for any whitelist size.
    last_check_prices_json: Mapped[str] = mapped_column(Text, default="{}")
    last_full_analysis_date: Mapped[str] = mapped_column(String(10), default="")
    claude_budget_month_key: Mapped[str] = mapped_column(String(7), default="")
    claude_spend_usd_this_month: Mapped[float] = mapped_column(Float, default=0.0)
    # HMAC key for signing login session cookies -- generated once on first
    # boot and persisted so restarting the app doesn't log everyone out.
    session_secret: Mapped[str] = mapped_column(String(64), default="")
