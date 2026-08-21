import enum
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


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
    # Which lot this belongs to: "alpaca" (day, US stocks/ETFs) or "extended"
    # (24-7 extended, same Alpaca account). Existing rows backfill to "alpaca".
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


class AuditLog(Base):
    """Ślad audytowy operacji WRAŻLIWYCH wykonanych z panelu: ręczna transakcja,
    STOP-wszystko (panic), sprzedaż pozycji, pauza/wznowienie, restart, zmiana
    budżetu. Zapisujemy CO, KIEDY, z jakiego IP i skrót parametrów -- żeby gdyby
    coś nieoczekiwanie ruszyło pozycje na żywej kasie, był czytelny dowód „kto,
    kiedy, co". Nigdy nie trzyma sekretów (tylko symbol/kwota/strona)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    action: Mapped[str] = mapped_column(String(32), index=True)
    detail: Mapped[str] = mapped_column(String(255), default="")
    client_ip: Mapped[str] = mapped_column(String(64), default="")
    outcome: Mapped[str] = mapped_column(String(16), default="ok")  # ok | error


class PushSubscription(Base):
    """A browser/PWA Web Push endpoint the user opted into. One row per device
    that pressed "Włącz powiadomienia" -- phone, watch-mirroring iPhone, laptop.
    Keyed by the endpoint URL (unique per device+browser) so re-subscribing the
    same device updates in place instead of duplicating. Push is best-effort:
    a 404/410 from the push service means the sub is dead and gets pruned."""

    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)
    # Free-text label so the user can tell devices apart in the UI later.
    user_agent: Mapped[str] = mapped_column(String(255), default="")


class SystemState(Base):
    """Singleton row (id=1) holding global mutable trading state."""

    __tablename__ = "system_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)  # Alpaca equities (day) venue manual pause
    # Extended (24/7) venue manual pause -- independent START/STOP from the
    # equities one. Defaults paused so a freshly-enabled venue never trades
    # until the human presses START. is_halted (loss-limit auto-stop) is global.
    extended_paused: Mapped[bool] = mapped_column(Boolean, default=True)
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
    extended_partial_tp_taken_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON dict {ticker -> [ISO timestamps of recent stop-losses]} -- drives the
    # auto-blacklist: a ticker that stop-losses too many times in a short window
    # gets quarantined (a long re-buy cooldown) instead of being retried.
    stop_loss_streak_json: Mapped[str] = mapped_column(Text, default="{}")
    extended_stop_loss_streak_json: Mapped[str] = mapped_column(Text, default="{}")
    # JSON dict {ticker -> [recent per-ticker headline titles]} -- lets the
    # bot detect a brand-new headline (earnings, material single-stock news)
    # the moment it's published and wake Claude immediately, independent of
    # any price move. Bounded to PER_TICKER_LIMIT titles per ticker each
    # cycle so this never grows unbounded.
    seen_ticker_headlines_json: Mapped[str] = mapped_column(Text, default="{}")
    # Dedicated per-cycle state for the extended (24-7) venue, kept in separate
    # columns so the equities venue's state above stays byte-for-byte untouched
    # (zero risk to the live stock path). Same JSON shapes as their equities
    # counterparts. analysis_state_json holds {last_full_date, last_at}.
    extended_check_prices_json: Mapped[str] = mapped_column(Text, default="{}")
    extended_position_peaks_json: Mapped[str] = mapped_column(Text, default="{}")
    extended_stop_loss_cooldowns_json: Mapped[str] = mapped_column(Text, default="{}")
    extended_seen_ticker_headlines_json: Mapped[str] = mapped_column(Text, default="{}")
    extended_analysis_state_json: Mapped[str] = mapped_column(Text, default="{}")
    claude_budget_month_key: Mapped[str] = mapped_column(String(7), default="")
    claude_spend_usd_this_month: Mapped[float] = mapped_column(Float, default=0.0)
    # Ręczne nadpisanie miesięcznego budżetu tokenów, ustawiane z UI (0 = użyj
    # wartości z .env). Pozwala wpisać/zmienić limit bez wchodzenia na serwer.
    claude_monthly_budget_override: Mapped[float] = mapped_column(Float, default=0.0)
    # NEVER resets (unlike the monthly counter above) -- lifetime Claude spend,
    # so "wynik netto" can compare it against realized_pnl_usd (also lifetime,
    # since inception). Comparing lifetime P&L against only THIS month's spend
    # would understate cost more and more every month that passes.
    claude_spend_usd_lifetime: Mapped[float] = mapped_column(Float, default=0.0)
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
    # The extended venue's own risk regime (BTC trend + extended breadth), cached by
    # the extended cycle so the dashboard can show a separate extended chip.
    extended_market_regime_json: Mapped[str] = mapped_column(Text, default="{}")
    # Live, auto-managed POZA SESJĄ whitelist (JSON list of tickers). Empty ->
    # falls back to the config seed (extended_whitelist). Rewritten by the
    # Friday whitelist_review; read by the extended cycle so add/remove takes
    # effect without a redeploy.
    extended_whitelist_json: Mapped[str] = mapped_column(Text, default="")
    # Highest ever-observed total account value -- distinct from day/week
    # start (which reset on a rolling window). Drives the max-drawdown-from-
    # peak halt: unlike day/week loss, this catches a slow bleed that never
    # crosses either daily or weekly limit on any single day. 0 = not yet
    # initialized (set on the first update_portfolio_value call).
    peak_account_value: Mapped[float] = mapped_column(Float, default=0.0)
    # A candidate new all-time-high awaiting confirmation (see
    # PEAK_CONFIRMATION_UPDATES in risk_manager.py) -- both venues share one
    # Alpaca account, so account_total_value() combines THIS venue's live
    # numbers with the OTHER venue's last stored snapshot; a real diagnostic
    # caught two legs briefly holding positions at the same moment inflating
    # the combined total for a few hours, which then got canonized as an
    # all-time peak the account's real, sustained value never actually
    # reached again -- a permanently unfair drawdown reference. Requiring the
    # candidate to reappear on a later update before promoting it filters that
    # out without blocking a genuine, sustained new high.
    pending_peak_value: Mapped[float] = mapped_column(Float, default=0.0)
    pending_peak_confirmations: Mapped[int] = mapped_column(Integer, default=0)
    # Auto-odkryte źródła newsów: JSON lista [[nazwa, url], ...] dołączana do
    # stałych RSS_FEEDS. Codzienny job próbnie sięga do puli kandydatów i dopisuje
    # ~10% nowych, OSIĄGALNYCH z serwera źródeł (te zablokowane odpadają). Pusta =
    # tylko wbudowana lista. discovered_feeds_meta_json trzyma {date, added, total}
    # na potrzeby nagłówka zakładki Newsy ("znaleziono dziś N nowych źródeł").
    discovered_feeds_json: Mapped[str] = mapped_column(Text, default="[]")
    discovered_feeds_meta_json: Mapped[str] = mapped_column(Text, default="{}")
    # "Od kiedy mierzymy" skuteczność/edge — ISO timestamp ustawiany przyciskiem
    # „Świeży start" (po zmianie strategii / wpłacie). Puste = licz od zawsze.
    # NIE kasuje transakcji (historia zostaje) — tylko przesuwa punkt startu
    # statystyk, żeby stara epoka churnu nie zaniżała obrazu nowej strategii.
    stats_epoch: Mapped[str] = mapped_column(String(32), default="")
    # Tryb powiadomień push per-transakcja: all (każda), big (tylko duże ruchy),
    # daily (tylko dzienne podsumowanie), off (żadne per-trade). Dzienny raport
    # leci niezależnie. Ustawiany z Centrum sterowania.
    push_mode: Mapped[str] = mapped_column(String(8), default="all")
    # Dedup alertu progu dziennego P&L: "YYYY-MM-DD:up" / ":down" — ostatnio
    # wysłany alert, żeby ten sam próg w tym samym dniu/kierunku nie spamował.
    day_pnl_alert_stamp: Mapped[str] = mapped_column(String(16), default="")
    # Plan oszczędzania (wygoda): miesięczna wpłata i cel kwotowy, żeby panel
    # pokazywał postęp i prognozę dojścia. 0 = nieustawione.
    monthly_deposit_plan: Mapped[float] = mapped_column(Float, default=0.0)
    goal_amount: Mapped[float] = mapped_column(Float, default=0.0)
    # Co widżet iOS pokazuje jako główną liczbę: "total" (zysk automatu),
    # "day" (zysk dnia), "account" (stan konta), "positions" (liczba pozycji).
    widget_metric: Mapped[str] = mapped_column(String(12), default="total")
    # Ręczne plany wyjścia per symbol: {"SPY": {"stop_pct": 3.0, "take_profit_pct": 8.0}}.
    # DODATKOWE, ZACIEŚNIAJĄCE progi zamknięcia (nie luzują automatu): pozycja jest
    # sprzedana w całości, gdy strata/zysk osiągnie ręczny próg. Puste = tylko automat.
    exit_overrides_json: Mapped[str] = mapped_column(Text, default="{}")
