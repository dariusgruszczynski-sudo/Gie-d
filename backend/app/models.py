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
    # A brand-new, ticker-specific headline (earnings release, material
    # filing-driven news, ...) fired this cycle independent of any price
    # move -- crucial pre-/after-market, where thin trading means price can
    # lag the news print by minutes.
    NEWS_EVENT = "news_event"


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
    # Which broker/portfolio this belongs to: "alpaca" (day, US stocks/ETFs) or
    # "etoro" (24-7 crypto/forex). Existing rows backfill to "alpaca".
    venue: Mapped[str] = mapped_column(String(16), default="alpaca", index=True)

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
    venue: Mapped[str] = mapped_column(String(16), default="alpaca", index=True)

    decision_id: Mapped[int | None] = mapped_column(ForeignKey("decisions.id"), nullable=True)
    decision: Mapped[Decision | None] = relationship(back_populates="trades")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    total_value_usdt: Mapped[float] = mapped_column(Float)
    usdt_balance: Mapped[float] = mapped_column(Float)
    # JSON dicts keyed by ticker ("SPY", "AAPL", ...) so the whitelist can
    # hold any number of tickers without a schema change per one.
    balances_json: Mapped[str] = mapped_column(Text, default="{}")
    prices_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON list of whitelist symbols that failed to price this cycle (network
    # hiccup, delisted pair, ...) -- lets the dashboard tell "genuinely
    # unavailable" apart from "just hasn't loaded yet" instead of showing
    # "oczekiwanie na dane" forever.
    failed_symbols_json: Mapped[str] = mapped_column(Text, default="[]")
    venue: Mapped[str] = mapped_column(String(16), default="alpaca", index=True)


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
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)  # Alpaca (day) venue manual pause
    # eToro (night) venue manual pause -- independent START/STOP from the
    # Alpaca one. Defaults paused so a freshly-enabled venue never trades until
    # the human presses START. is_halted (loss-limit auto-stop) stays global.
    etoro_paused: Mapped[bool] = mapped_column(Boolean, default=True)
    is_halted: Mapped[bool] = mapped_column(Boolean, default=False)
    halted_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    day_start_date: Mapped[str] = mapped_column(String(10), default="")
    day_start_value: Mapped[float] = mapped_column(Float, default=0.0)
    week_start_date: Mapped[str] = mapped_column(String(10), default="")
    week_start_value: Mapped[float] = mapped_column(Float, default=0.0)
    # JSON dict keyed by ticker ("SPY", ...) -> last observed price, so the
    # price-move trigger works for any whitelist size.
    last_check_prices_json: Mapped[str] = mapped_column(Text, default="{}")
    last_full_analysis_date: Mapped[str] = mapped_column(String(10), default="")
    # ISO timestamp of the last completed Claude analysis -- drives the
    # heartbeat trigger (a full look at the market every N minutes even
    # without a sharp price move).
    last_analysis_at: Mapped[str] = mapped_column(String(32), default="")
    # JSON dict {ticker -> ISO timestamp until which re-buying is blocked}
    # after a stop-loss on that ticker. Prevents a small account bleeding out
    # on repeated buy-top/stop-out churn.
    stop_loss_cooldowns_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON dict {ticker -> highest price seen since entry} -- drives the
    # trailing stop. Cleared per ticker when the position is closed.
    position_peaks_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON dict {ticker -> true} marking positions whose partial take-profit has
    # already been booked, so the partial only fires once per position (not on
    # every subsequent poll). Cleared per ticker when the position is closed.
    partial_tp_taken_json: Mapped[str] = mapped_column(Text, default="{}")
    etoro_partial_tp_taken_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON dict {ticker -> [ISO timestamps of recent stop-losses]} -- drives the
    # auto-blacklist: a ticker that stop-losses too many times in a short window
    # gets quarantined (a long re-buy cooldown) instead of being retried.
    stop_loss_streak_json: Mapped[str] = mapped_column(Text, default="{}")
    etoro_stop_loss_streak_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON dict {ticker -> [recent per-ticker headline titles]} -- lets the
    # bot detect a brand-new headline (earnings, material single-stock news)
    # the moment it's published and wake Claude immediately, independent of
    # any price move. Bounded to PER_TICKER_LIMIT titles per ticker each
    # cycle so this never grows unbounded.
    seen_ticker_headlines_json: Mapped[str] = mapped_column(Text, default="{}")
    # Dedicated per-cycle state for the eToro (24-7 crypto/forex) venue, kept in
    # separate columns so the Alpaca venue's state above stays byte-for-byte
    # untouched (zero risk to the live stock path). Same JSON shapes as their
    # Alpaca counterparts. analysis_state_json holds {last_full_date, last_at}.
    etoro_check_prices_json: Mapped[str] = mapped_column(Text, default="{}")
    etoro_position_peaks_json: Mapped[str] = mapped_column(Text, default="{}")
    etoro_stop_loss_cooldowns_json: Mapped[str] = mapped_column(Text, default="{}")
    etoro_seen_ticker_headlines_json: Mapped[str] = mapped_column(Text, default="{}")
    etoro_analysis_state_json: Mapped[str] = mapped_column(Text, default="{}")
    claude_budget_month_key: Mapped[str] = mapped_column(String(7), default="")
    claude_spend_usd_this_month: Mapped[float] = mapped_column(Float, default=0.0)
    # Live token meter: running input/output token totals for the current month,
    # reset alongside the spend counter on a month rollover. Lets the dashboard
    # show real token throughput, not just the estimated dollar figure.
    claude_input_tokens_this_month: Mapped[int] = mapped_column(Integer, default=0)
    claude_output_tokens_this_month: Mapped[int] = mapped_column(Integer, default=0)
    # Buy-and-hold benchmark baseline, set on the first cycle that can price
    # the benchmark ticker (and reset alongside the portfolio). Lets the
    # scorecard answer "am I beating just holding SPY?": benchmark value now =
    # benchmark_start_value * (benchmark_price_now / benchmark_start_price).
    benchmark_start_date: Mapped[str] = mapped_column(String(10), default="")
    benchmark_start_price: Mapped[float] = mapped_column(Float, default=0.0)
    benchmark_start_value: Mapped[float] = mapped_column(Float, default=0.0)
    # Weekly self-review: a rolling JSON list of {date, lesson} entries Claude
    # distilled from its own recent trades. Fed back into every decision's
    # context -- durable memory that outlives the 15-trade recent window.
    lessons_json: Mapped[str] = mapped_column(Text, default="[]")
    last_self_review_date: Mapped[str] = mapped_column(String(10), default="")
    # HMAC key for signing login session cookies -- generated once on first
    # boot and persisted so restarting the app doesn't log everyone out.
    session_secret: Mapped[str] = mapped_column(String(64), default="")
    # Last computed broad-market regime {regime, score, reasons} -- cached here
    # by the Alpaca cycle so /api/status can show it without recomputing on
    # every 15s poll.
    market_regime_json: Mapped[str] = mapped_column(Text, default="{}")
