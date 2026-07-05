from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    # Every cycle is analyzed by the fast/cheap model first. Its decision is
    # trusted directly on HOLD or high-confidence BUY/SELL; a low-confidence
    # BUY/SELL (genuine doubt) is escalated to claude_model for a second,
    # more expensive opinion -- see ClaudeAdvisor.decide().
    claude_model: str = "claude-opus-4-8"
    claude_model_fast: str = "claude-sonnet-5"
    claude_escalation_confidence_threshold: float = 0.65

    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    # Alpaca (unlike Kraken) has a real paper-trading environment with the
    # identical API -- set to True to rehearse safely on a simulated account
    # before flipping back to live. quote_currency drives how the dashboard
    # labels amounts (tickers have no quote-currency suffix, unlike crypto
    # pairs, so it does NOT need to appear in trading_whitelist).
    alpaca_paper: bool = False
    quote_currency: str = "USD"

    daily_loss_limit_pct: float = 20.0
    weekly_loss_limit_pct: float = 70.0
    max_position_pct: float = 25.0
    # Mechanical exit rules applied to every held position on every poll,
    # without asking Claude: auto-SELL the whole position when it gains
    # >= take_profit_pct or loses >= stop_loss_pct vs its average entry price.
    # This is what actually makes the bot "obraca kapitałem" (rotate capital)
    # instead of just buying and holding. Set take_profit_pct=0 to disable
    # take-profit, stop_loss_pct=0 to disable stop-loss.
    stop_loss_pct: float = 2.0
    # After a stop-loss cuts a position, block re-buying that same coin for
    # this many minutes -- stops the bot from "piłowanie" (buy top -> stop ->
    # rebuy -> stop) that bleeds a small account dry on fees. 0 = disabled.
    stop_loss_cooldown_minutes: int = 60
    # Exit style for winners:
    #  - trailing_stop_enabled=True (default): let winners run. Once a position
    #    reaches +take_profit_pct it ARMS a trailing stop and is only sold when
    #    price falls trailing_stop_pct below its peak -- so a big trend isn't
    #    capped at +take_profit_pct. take_profit_pct becomes the ARM threshold.
    #  - trailing_stop_enabled=False: fixed take-profit -- sell immediately at
    #    +take_profit_pct.
    # stop_loss_pct is always a hard floor from the entry price, either way.
    take_profit_pct: float = 3.0
    trailing_stop_enabled: bool = True
    trailing_stop_pct: float = 1.5
    # Send an email the moment any trade executes (BUY/SELL, incl. TP/SL exits).
    # Uses the same SMTP config as the daily report; silently skipped if SMTP
    # isn't configured. Set False to keep only the daily report.
    trade_alerts_enabled: bool = True
    # Broad-market ETF + liquid, fractionable large caps -- tight spreads, deep
    # liquidity, and available fractional/notional orders on Alpaca, which
    # matters a lot on a small account (share prices don't need to divide
    # evenly into the position size).
    # MSTR added as the deliberately volatile/high-beta pick -- a leveraged
    # bitcoin proxy via corporate balance sheet, swings far harder than the
    # rest of the whitelist on any given day.
    trading_whitelist: str = "SPY,QQQ,AAPL,NVDA,MSTR"

    poll_interval_minutes: int = 15
    price_move_trigger_pct: float = 2.0
    # Stocks/ETFs regular session is only ~6.5h/day (9:30-16:00 ET). Extended
    # hours add pre-market (4:00-9:30 ET) and after-hours (16:00-20:00 ET) on
    # the SAME Alpaca account -- no new broker/money needed -- for ~16h/day of
    # coverage. Orders there are whole-share LIMIT orders only (thinner
    # liquidity, wider spreads -- a real execution-risk tradeoff, worse on
    # volatile picks like MSTR/NVDA). On a tiny account a position slice is
    # smaller than one whole share, so extended hours can't actually buy/exit
    # -- hence it's OFF manually by default and auto-enables only once the
    # portfolio is big enough to be useful (see below).
    extended_hours_trading_enabled: bool = False
    # Auto-enable extended-hours trading once total portfolio value reaches
    # this many USD, without needing to flip the manual switch. Set 0 to
    # disable auto-enabling (then only extended_hours_trading_enabled counts).
    extended_hours_auto_enable_usd: float = 500.0
    # Applies only during pre-market/after-hours: a higher bar than
    # price_move_trigger_pct before waking Claude, since routine drift
    # outside the regular session is less meaningful and extending the
    # trading window to ~2.5x its length would otherwise ~2.5x the Claude
    # API spend for the same signal quality.
    extended_hours_price_move_trigger_pct: float = 4.0
    # Earnings-gap guard: the mechanical stop-loss CANNOT protect against an
    # overnight earnings gap (price jumps straight through the stop). So block
    # opening a NEW position in a ticker reporting within this many days.
    # SELL/HOLD stay allowed; 0 disables the guard. Only acts on KNOWN
    # upcoming earnings -- a calendar-lookup failure never blocks trading.
    earnings_blackout_days: int = 2

    claude_monthly_budget_usd: float = 20.0
    claude_budget_alert_threshold_pct: float = 80.0

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    report_recipient_email: str = "0grucha0@gmail.com"
    report_hour: int = 6
    report_minute: int = 0
    report_timezone: str = "Europe/Warsaw"

    database_url: str = "sqlite:///./data/trading.db"

    # Empty = no login required (backward-compatible default for existing
    # deployments). Format: "user1:pass1,user2:pass2".
    dashboard_users: str = ""

    @property
    def whitelist_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.trading_whitelist.split(",") if s.strip()]

    @property
    def dashboard_credentials(self) -> dict[str, str]:
        creds: dict[str, str] = {}
        for pair in self.dashboard_users.split(","):
            if ":" not in pair:
                continue
            user, pw = pair.split(":", 1)
            user = user.strip()
            if user:
                creds[user] = pw.strip()
        return creds


@lru_cache
def get_settings() -> Settings:
    return Settings()
