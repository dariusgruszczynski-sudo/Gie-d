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

    # --- eToro: drugi broker dla handlu nocnego/24-7 (krypto spot) ---
    # eToro autoryzuje parą nagłówków: x-api-key (klucz publiczny) +
    # x-user-key (klucz prywatny/portfela Agent Portfolio). Demo (sandbox) ma
    # identyczne API pod ścieżką /demo/ -- domyślnie ON, żeby zweryfikować
    # integrację na wirtualnych pieniądzach przed przełączeniem na żywe.
    etoro_enabled: bool = False
    etoro_api_key: str = ""
    etoro_user_key: str = ""
    etoro_paper: bool = True
    # Krypto handluje 24/7 (także w weekend) -- to pokrywa noce, gdy rynek US
    # jest zamknięty. Spot, bez dźwigni, ta sama mechanika co portfel Alpaca.
    etoro_whitelist: str = "BTC,ETH,SOL"

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
    # Volatility-scaled (ATR-style) hard stop: instead of a fixed %, the stop
    # distance scales with the ticker's own 1h-return volatility, so it sits
    # OUTSIDE normal noise -- a calm index isn't shaken out on a routine 2%
    # wobble (then missing the bounce), while a wild name (TSLA/crypto) gets a
    # proportionally wider stop. stop% = clamp(mult * volatility_pct_1h,
    # min_pct, max_pct). Set stop_loss_vol_mult=0 to disable and fall back to
    # the fixed stop_loss_pct above.
    stop_loss_vol_mult: float = 6.0
    stop_loss_min_pct: float = 2.5
    stop_loss_max_pct: float = 12.0
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
    # --- Geometria zysk/ryzyko (Pakiet 1) -----------------------------------
    # After the ATR stop change the reward side stayed fixed (+3% arm, 1.5%
    # trail) while stops widened to 2.5-12% -- an INVERTED risk/reward that cut
    # winners early and let losers run to the stop (the diagnostic showed 0 wins
    # / all exits stop-losses). Couple the reward to the (vol-scaled) stop
    # distance so they stay in proportion: the take-profit ARM sits at
    # stop_dist * reward_risk_ratio and the trailing at stop_dist *
    # trailing_stop_frac. Set reward_risk_ratio=0 to fall back to the fixed
    # take_profit_pct / trailing_stop_pct above.
    reward_risk_ratio: float = 1.5
    trailing_stop_frac: float = 0.5
    # Partial profit-taking: once a position reaches +partial_take_profit_r *
    # stop_dist, sell partial_take_profit_frac of it and let the rest run under
    # the trailing stop. This books a realized WIN (take-profit alone almost
    # never fired) while keeping upside open. Set enabled=False to disable.
    partial_take_profit_enabled: bool = True
    partial_take_profit_frac: float = 0.5
    partial_take_profit_r: float = 1.0
    # --- Anty-churn (Pakiet 2) ----------------------------------------------
    # Hard conviction floor: an automated BUY below this confidence is rejected
    # outright -- cash is a valid position, don't trade a weak edge. 0 disables.
    min_buy_confidence: float = 0.60
    # Cap on NEW automated BUY entries per venue per calendar day -- stops a
    # small account churning on many low-edge entries. 0 disables.
    max_new_positions_per_day: int = 3
    # Minimum holding time (minutes) before a NON-stop mechanical exit (trailing
    # / take-profit / partial) may fire. The hard stop-loss is ALWAYS allowed.
    # Kills in-and-out round trips that only pay the spread. 0 disables.
    min_hold_minutes: int = 30
    # --- Sizing oparty na ryzyku + reżim rynku (Pakiet 3) -------------------
    # Risk-based position cap: size a BUY so that hitting its stop costs at most
    # risk_per_trade_pct of the WHOLE account (position_value * stop_dist =
    # risk). Composed as a CAP with Claude's request and max_position_pct (only
    # ever shrinks), so a wide-stop name automatically gets a smaller slice.
    # 0 disables (falls back to the volatility-scaled sizing only).
    risk_per_trade_pct: float = 1.0
    # Market-regime gate: in a risk-off regime (benchmark below its long trend +
    # elevated VIX / falling tape) only defensive/inverse names may be bought;
    # everything else is forced to HOLD. The regime is ALWAYS passed to Claude
    # as context regardless. Set regime_gate_enabled=False to keep the context
    # signal but drop the hard block.
    regime_gate_enabled: bool = True
    regime_vix_risk_off: float = 25.0
    defensive_symbols: str = "GLD,TLT,SH,PSQ"
    # --- Auto-blacklist po serii stop-lossów (Pakiet 4) ---------------------
    # If a ticker stop-losses auto_blacklist_stop_count times within
    # auto_blacklist_window_hours, quarantine it: block re-buying for
    # auto_blacklist_hours (a long cooldown) -- a setup that keeps failing is
    # parked instead of retried. Set auto_blacklist_stop_count=0 to disable.
    auto_blacklist_stop_count: int = 3
    auto_blacklist_window_hours: int = 24
    auto_blacklist_hours: int = 48
    # Send an email the moment any trade executes (BUY/SELL, incl. TP/SL exits).
    # Uses the same SMTP config as the daily report; silently skipped if SMTP
    # isn't configured. Set False to keep only the daily report.
    trade_alerts_enabled: bool = True
    # A DIVERSIFIED, tradable universe -- not just correlated tech beta, so the
    # bot can actually rotate to what's working and hedge instead of making one
    # big leveraged "tech goes up" bet:
    #  - Core tech/beta: SPY, QQQ, AAPL, NVDA (deep liquidity, fractional-OK)
    #  - MSTR: the deliberately volatile high-beta pick (leveraged BTC proxy)
    #  - Uncorrelated / defensive: GLD (gold), TLT (long bonds), XLE (energy),
    #    IWM (small caps) -- these often zig when tech zags
    #  - Inverse ETFs: SH (inverse S&P), PSQ (inverse Nasdaq) -- let the bot
    #    PROFIT in a downtrend by going long an inverse ETF instead of just
    #    sitting in cash. Deliberately the 1x (not 3x-leveraged) inverses, so
    #    downside is bounded like any long position -- no unlimited-loss short
    #    mechanics, which would be reckless on a small account.
    #  - TSLA: second high-beta single name -- huge news flow (pairs well with
    #    the news trigger), deep liquidity, fractional-OK. Deliberately NOT a
    #    3x-leveraged ETF: those move ~2% within an hour, which with the
    #    global 2% stop-loss would just churn the account through stop-outs.
    trading_whitelist: str = "SPY,QQQ,AAPL,NVDA,MSTR,TSLA,GLD,TLT,XLE,IWM,SH,PSQ"
    # Benchmark the whole strategy against simply buying and holding this
    # ticker -- if the bot can't beat holding SPY, it isn't earning its
    # complexity. Drives the dashboard scorecard and is fed back to Claude.
    benchmark_symbol: str = "SPY"
    # Volatility-aware position sizing: Claude's requested size_pct is scaled
    # DOWN for tickers more volatile than this reference (so a wild name like
    # MSTR can't dominate P&L), never scaled up. Expressed as a per-bar
    # (1h) return standard deviation in %. ~1.0 is roughly a broad-index bar.
    # Set 0 to disable vol-scaling entirely.
    volatility_reference_pct: float = 1.0
    # Never let vol-scaling shrink a position below this fraction of what
    # Claude asked for -- otherwise a very volatile name gets sized to dust.
    volatility_min_scale: float = 0.35

    poll_interval_minutes: int = 15
    price_move_trigger_pct: float = 2.0
    # Heartbeat: force a full Claude analysis at least this often during
    # tradable hours, even when no price crossed the trigger threshold --
    # otherwise the bot only ever looks at the market on spikes and can sit
    # idle through an entire quiet session. ~3-4 cheap fast-model calls per
    # regular session at the default. 0 disables the heartbeat.
    full_analysis_every_minutes: int = 120
    # US stocks/ETFs trade the regular session only (9:30-16:00 ET). Pre-market
    # and after-hours were removed: on a small account a position slice is
    # smaller than one whole share (extended hours reject fractional/notional
    # orders), so they could never actually buy or exit -- overnight coverage
    # is handled by the separate 24/7 crypto venue instead.
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
    def etoro_whitelist_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.etoro_whitelist.split(",") if s.strip()]

    @property
    def defensive_symbol_list(self) -> list[str]:
        """Names allowed to be BOUGHT even in a risk-off regime -- gold, bonds
        and inverse ETFs that tend to hold up (or profit) when the broad market
        falls. Everything else is HOLD-only while risk-off."""
        return [s.strip().upper() for s in self.defensive_symbols.split(",") if s.strip()]

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
