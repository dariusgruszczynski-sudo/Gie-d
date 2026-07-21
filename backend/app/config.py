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
    # LEAN-AI (mały kapitał): domyślnie WYŁĄCZAMY eskalację do droższego modelu
    # (Opus). Każdy cykl to jedno tanie wywołanie modelu szybkiego -- to obcina
    # koszt AI, który przy małym koncie jest głównym progiem rentowności. Włącz
    # (=true) dopiero, gdy konto jest na tyle duże, że koszt Opusa to <2-3%/mies.
    claude_escalation_enabled: bool = False
    # Twardy bezpiecznik budżetu: gdy szacowany wydatek Claude w tym miesiącu
    # przekroczy claude_monthly_budget_usd, automat WSTRZYMUJE nowe wywołania
    # (nie pyta Claude, nie handluje automatycznie), zamiast palić budżet w
    # nieskończoność. Ręczne transakcje i mechaniczne wyjścia działają dalej.
    claude_pause_trading_at_budget: bool = True

    alpaca_api_key: str = ""
    alpaca_api_secret: str = ""
    # Alpaca (unlike Kraken) has a real paper-trading environment with the
    # identical API -- set to True to rehearse safely on a simulated account
    # before flipping back to live. quote_currency drives how the dashboard
    # labels amounts (tickers have no quote-currency suffix, unlike crypto
    # pairs, so it does NOT need to appear in trading_whitelist).
    alpaca_paper: bool = False
    quote_currency: str = "USD"

    # --- POZA SESJĄ (extended hours): DRUGI lot na TYM SAMYM koncie Alpaca ---
    # Ta sama para kluczy i to samo konto co sesja regularna, ale handluje w
    # pre-market (4:00-9:30 ET) i after-hours (16:00-20:00 ET). Poza sesją Alpaca
    # NIE przyjmuje zleceń MARKET ani ułamków -- tylko LIMIT na CAŁE akcje. Dlatego
    # ta noga gra WĄSKĄ listą TANICH, płynnych ETF-ów (całe sztuki muszą zmieścić
    # się w budżecie). Domyślnie OFF -- włącza się dopiero gdy egzekucja AH
    # (LIMIT/całe akcje) jest zbudowana i skonfigurowana.
    extended_enabled: bool = False
    # Tania, płynna whitelista ETF pod handel po godzinach (całe sztuki < ~$60).
    # Zarządzana automatycznie przez piątkowy auto-przegląd (dodaj/wyrzuć/sprzedaj);
    # to jest tylko seed startowy.
    extended_whitelist: str = "XLF,GDX,SLV,FXI,EEM,EWZ,KWEB"
    # Piątkowy auto-przegląd whitelisty POZA SESJĄ (whitelist_review): co piątek po
    # zamknięciu after-market wybiera z puli kandydatów te TANIE, płynne ETF-y,
    # które mieszczą się w budżecie (całe akcje), wyrzuca za drogie / niepłynne
    # (wyrzucone, jeśli trzymane, sprzedaje istniejący force-close przy najbliższym
    # pre-market) i dodaje nowe. Lista żyje w bazie (extended_whitelist_json);
    # te pola sterują doborem.
    extended_max_share_price: float = 60.0        # całe akcje muszą się mieścić
    extended_whitelist_target: int = 7            # docelowa liczba nazw
    extended_whitelist_review_enabled: bool = True
    # Szeroka pula kandydatów, z której piątkowy przegląd dobiera whitelistę:
    # tanie, płynne, NIElewarowane ETF-y (sektory, surowce, geografia).
    extended_candidate_pool: str = (
        "XLF,XLE,XLU,XLI,XLV,GDX,GDXJ,SLV,IAU,FXI,KWEB,EEM,EWZ,EWJ,INDA,"
        "TLT,HYG,KRE,SMH,IWM,VWO,ARKK,PSLV"
    )

    # --- DWA MÓZGI: osobne profile agresji per noga --------------------------
    # Bazowe knoby niżej to profil SESJI REGULARNEJ ("średnio agresywnie",
    # ułamki, MARKET). Noga POZA SESJĄ dostaje WŁASNY, OSTROŻNIEJSZY profil
    # (cieńsza płynność, szersze spready, całe akcje) -- te extended_* wartości
    # nadpisują bazowe TYLKO dla venue "extended" (patrz strategy_profiles.
    # effective_settings). Zmień tu, żeby dostroić handel po godzinach bez
    # ruszania sesji regularnej.
    extended_risk_per_trade_pct: float = 1.3          # nieco odwazniej, ale wciaz ostroznie po godzinach
    extended_max_concurrent_positions: int = 0        # 0 = bez limitu
    extended_min_buy_confidence: float = 0.55         # zrownane z sesja -- 0.60 dawalo 0 prob BUY przez tydzien
    extended_max_new_positions_per_day: int = 0       # 0 = bez limitu
    extended_min_hold_minutes: int = 0                # 0 = bez limitu
    extended_max_position_pct: float = 30.0
    extended_reward_risk_ratio: float = 1.5
    extended_trailing_stop_frac: float = 0.5
    extended_partial_take_profit_frac: float = 0.50
    extended_partial_take_profit_r: float = 0.7
    extended_stop_loss_vol_mult: float = 4.0
    extended_stop_loss_min_pct: float = 1.5
    extended_stop_loss_max_pct: float = 8.0
    extended_volatility_reference_pct: float = 1.5
    extended_price_move_trigger_pct: float = 1.5
    extended_full_analysis_every_minutes: int = 30
    # Poza sesją sprawdzamy rzadziej niż sesja regularna (cieńszy rynek, mniej
    # okazji, oszczędność tokenów) -- co 15 min.
    extended_poll_interval_minutes: int = 15
    extended_signal_timeframe: str = "15m"

    # --- Podział kapitału między dwie nogi (JEDNO konto Alpaca) --------------
    # Obie nogi grają jedną, wspólną gotówką. Każda może zaangażować najwyżej swój
    # PRZYDZIAŁ wartości konta w pozycje; sizing BUY jest przycinany do wolnego
    # miejsca w tym przydziale. 100/100 = brak limitu wzajemnego (mogą się
    # nakładać jako górne limity).
    alpaca_allocation_pct: float = 100.0
    extended_allocation_pct: float = 100.0

    daily_loss_limit_pct: float = 20.0
    # Zacieśnione z 70% -> 25%: tygodniowy 70% to praktycznie brak ochrony małego
    # konta. 25% to realny bezpiecznik: seria złych dni zatrzyma automat, zanim
    # zrobi poważną wyrwę w kapitale.
    weekly_loss_limit_pct: float = 25.0
    # Ostatni bezpiecznik: spadek konta o tyle % OD SZCZYTU (ever-observed, nie
    # od początku dnia/tygodnia) zatrzymuje handel. Łapie powolny, wieloDNIOWY
    # krwotok, który nigdy nie przekracza dziennego/tygodniowego limitu w
    # pojedynczym dniu, ale sumuje się w realną stratę kapitału.
    max_drawdown_halt_pct: float = 20.0
    max_position_pct: float = 32.0          # wiekszy udzial na mocnym setupie
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
    # Twardy sufit realizacji zysku: nawet przy włączonym trailingu, gdy pozycja
    # urośnie o >= tyle procent od wejścia, BIERZEMY cały zysk od razu -- żeby
    # mocny ruch nie „odjechał" z powrotem czekając aż trailing się uzbroi. To
    # odpowiedź na "indeks na +X% a nie sprzedany". 0 wyłącza (czysty trailing).
    hard_take_profit_pct: float = 8.0
    # Pozycje, których automat NIE otworzył sam (były na koncie wcześniej albo
    # kupione ręcznie) nie mają zapisanej ceny wejścia -> dotąd mechaniczny stop
    # je pomijał (żadnej ochrony). Gdy włączone, taka "adoptowana" pozycja i tak
    # dostaje TRAILING-STOP liczony od najwyższej ceny zaobserwowanej od momentu
    # adopcji (zawsze uzbrojony -- nie ma znanego wejścia, od którego czekać na
    # +R; brak twardego stopa-od-wejścia i częściowej realizacji dla niej).
    protect_adopted_positions: bool = True
    # --- Geometria zysk/ryzyko (Pakiet 1) -----------------------------------
    # After the ATR stop change the reward side stayed fixed (+3% arm, 1.5%
    # trail) while stops widened to 2.5-12% -- an INVERTED risk/reward that cut
    # winners early and let losers run to the stop (the diagnostic showed 0 wins
    # / all exits stop-losses). Couple the reward to the (vol-scaled) stop
    # distance so they stay in proportion: the take-profit ARM sits at
    # stop_dist * reward_risk_ratio and the trailing at stop_dist *
    # trailing_stop_frac. Set reward_risk_ratio=0 to fall back to the fixed
    # take_profit_pct / trailing_stop_pct above.
    reward_risk_ratio: float = 2.0
    trailing_stop_frac: float = 0.5
    # Partial profit-taking: once a position reaches +partial_take_profit_r *
    # stop_dist, sell partial_take_profit_frac of it and let the rest run under
    # the trailing stop. This books a realized WIN (take-profit alone almost
    # never fired) while keeping upside open. Set enabled=False to disable.
    partial_take_profit_enabled: bool = True
    partial_take_profit_frac: float = 0.33
    partial_take_profit_r: float = 1.5
    # --- Anty-churn (Pakiet 2) ----------------------------------------------
    # Hard conviction floor: an automated BUY below this confidence is rejected
    # outright -- cash is a valid position, don't trade a weak edge. 0 disables.
    # Equities profile = "medium aggressive" (crypto overrides lower, see above).
    min_buy_confidence: float = 0.57
    # Cap on NEW automated BUY entries per venue per calendar day -- stops a
    # small account churning on many low-edge entries. 0 disables (bez limitu).
    max_new_positions_per_day: int = 0
    # Minimum holding time (minutes) before a NON-stop mechanical exit (trailing
    # / take-profit / partial) may fire. The hard stop-loss is ALWAYS allowed.
    # Kills in-and-out round trips that only pay the spread. 0 disables (bez limitu wyjść).
    min_hold_minutes: int = 0
    # --- Filtr konfluencji wejść (Tier 1: przewaga wejścia) -----------------
    # Entry edge (win rate) is the FIRST-ORDER driver of profit -- exit geometry
    # is second-order -- so a BUY must clear a transparent confluence of trend +
    # momentum + RSI before it commits capital (trading WITH the trend avoids
    # knife-catching and lifts the win rate). Score is 0-3 over {SMA50>SMA200,
    # MACD bullish, RSI in a healthy/momentum zone}; a BUY needs >= entry_min_score.
    # A 6-year backtest showed an earlier RSI-overbought VETO made results worse
    # (fewer entries, lower expectancy) -- it filtered out continuation entries
    # into exactly the strong multi-month trends this strategy needs to catch,
    # since persistently high RSI in a genuine trend is normal, not exhaustion.
    # Removed: RSI now only ever adds to the score. entry_filter_enabled=False
    # disables the whole filter.
    entry_filter_enabled: bool = True
    # 2-of-3 proved too strict in a choppy/mixed market: 5 days of live data
    # showed ZERO autonomous BUY on either venue despite real intraday swings --
    # not because entries were rejected (rejection log was empty), but because
    # Claude's own system prompt describes this gate, so it self-censored any
    # candidate it expected to fail 2-of-3 confluence. Lowered to 1-of-3 so a
    # single clear signal (fresh RSI bounce, a MACD cross, trend alignment) is
    # enough to clear -- catches smaller, more frequent moves, not just clean
    # multi-signal trends. Trade-off: more attempts also means more spread/
    # slippage cost and more chances to be wrong, not free money.
    entry_min_score: int = 1
    # --- Ilościowa auto-degradacja setupów (Tier 1) -------------------------
    # Once a ticker has >= auto_demote_min_trades CLOSED trades on a venue with
    # negative realized P&L and a sub-par win rate, block opening fresh
    # positions in it -- stop repeating a setup the data says doesn't work.
    auto_demote_enabled: bool = True
    auto_demote_min_trades: int = 5
    auto_demote_win_rate_floor: float = 40.0
    # --- Ochrona przewagi: koszty / churn / koncentracja (Tier 2) -----------
    # Cap on concurrently-held positions per venue. The whitelist is heavily
    # correlated (tech beta), so many open names are really ONE bet -- this
    # bounds that concentration. 0 disables (bez limitu).
    max_concurrent_positions: int = 0
    # Wide-spread / thinner names (inverse ETFs, small caps, sector/bond ETFs):
    # every round trip pays more spread, so their edge must be larger. Haircut
    # their BUY size by high_spread_size_scale (1.0 = no haircut).
    high_spread_symbols: str = "SH,PSQ,IWM,XLE,TLT,SLV,EEM,EFA,XLU,XLP,XLI"
    high_spread_size_scale: float = 0.6
    # --- Sizing oparty na ryzyku + reżim rynku (Pakiet 3) -------------------
    # Risk-based position cap: size a BUY so that hitting its stop costs at most
    # risk_per_trade_pct of the WHOLE account (position_value * stop_dist =
    # risk). Composed as a CAP with Claude's request and max_position_pct (only
    # ever shrinks), so a wide-stop name automatically gets a smaller slice.
    # 0 disables (falls back to the volatility-scaled sizing only).
    risk_per_trade_pct: float = 1.8          # odwazniej gdy jest przewaga
    # Market-regime gate: in a risk-off regime (benchmark below its long trend +
    # elevated VIX / falling tape) only defensive/inverse names may be bought;
    # everything else is forced to HOLD. The regime is ALWAYS passed to Claude
    # as context regardless. Set regime_gate_enabled=False to keep the context
    # signal but drop the hard block.
    # Adaptacyjne ryzyko: oba silniki SAME skalują agresję wg reżimu rynku
    # (patrz adaptive_risk.py) -- agresywnie w trendzie sprzyjającym, ostrożnie
    # w defensywie. Gdy włączone, zastępuje sztywną bramkę risk-off płynnym
    # zjazdem parametrów (silnik dalej handluje, tylko konserwatywnie), więc
    # regime_gate_enabled / crypto_regime_gate_enabled są wtedy pomijane.
    adaptive_risk_enabled: bool = True

    regime_gate_enabled: bool = True
    regime_vix_risk_off: float = 25.0
    defensive_symbols: str = "GLD,TLT,SH"
    # --- POZA SESJĄ: regime read ---------------------------------------------
    # The extended-hours leg trades the SAME US market as the regular session
    # (just pre-/after-market), so it reads the SAME equity regime (SPY trend +
    # VIX) rather than a separate benchmark. In risk-off the gate blocks new
    # longs; cash is the defensive position. Set extended_regime_gate_enabled=
    # False to keep the signal as context but drop the hard block.
    extended_regime_gate_enabled: bool = True
    extended_regime_benchmark: str = "SPY"
    extended_defensive_symbols: str = ""
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
    # CURATED, FOCUSED universe (trimmed from a 30-ticker list): a wide roster
    # spread attention and Claude's context thin without adding real edge --
    # fewer, deeper-liquidity names is easier to trade well AND cheaper (less
    # market data + fewer tokens per cycle). Kept:
    #  - Core index/beta: SPY, QQQ (deepest liquidity, tightest spreads)
    #  - Mega-cap trend leaders: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA --
    #    the most liquid single names with the cleanest trends, so the mechanical
    #    filter has a real bench to rotate into without correlated noise.
    #  - Defensive/inverse (kept in sync with defensive_symbols below): GLD
    #    (gold), TLT (long bonds), SH (inverse S&P, 1x -- not 3x-leveraged, so
    #    downside stays bounded like any long position).
    # Roster changes are safe: check_take_profit_stop_loss() force-closes any
    # held position whose symbol is no longer on this list, so trimming/adding
    # names never orphans a position.
    trading_whitelist: str = "SPY,QQQ,AAPL,MSFT,NVDA,AMZN,GOOGL,META,TSLA,GLD,TLT,SH"
    # Benchmark the whole strategy against simply buying and holding this
    # ticker -- if the bot can't beat holding SPY, it isn't earning its
    # complexity. Drives the dashboard scorecard and is fed back to Claude.
    benchmark_symbol: str = "SPY"
    # Volatility-aware position sizing: Claude's requested size_pct is scaled
    # DOWN for tickers more volatile than this reference (so a wild name like
    # MSTR can't dominate P&L), never scaled up. Expressed as a per-bar
    # per-bar return standard deviation in %, so it MUST be recalibrated
    # whenever signal_timeframe changes -- it's currently set for "1h" bars
    # (~0.6 is a typical broad-index hour; was 1.5 for a daily bar, ~2.55x
    # bigger per sqrt-time scaling over ~6.5 session-hours/day). Set 0 to
    # disable vol-scaling entirely.
    volatility_reference_pct: float = 0.6
    # Never let vol-scaling shrink a position below this fraction of what
    # Claude asked for -- otherwise a very volatile name gets sized to dust.
    volatility_min_scale: float = 0.35

    # Timeframe świec, z których liczone są sygnały wejścia (trend SMA50/200,
    # MACD, RSI) i skala zmienności stopa. Był "1d" (dowiedziona backtestem
    # przewaga, ale niewrażliwa na dzienne wahnięcia -- 5 dni bez ŻADNEGO
    # autonomicznego wejścia mimo realnych ruchów rynku). Świadomie skrócone na
    # "1h" (2026-07-21, decyzja właściciela): SMA50/200 liczone na 200
    # godzinach, MACD/RSI też godzinowe -- łapie mniejsze, częstsze ruchy w
    # ciągu dnia. To teren NIEzwalidowany backtestem na tym interwale -- więcej
    # transakcji, ale i więcej szumu/kosztu spreadu; obserwuj wyniki.
    signal_timeframe: str = "1h"

    # Akcje US: agresja siedzi w knobach ryzyka/pewności, NIE w częstotliwości --
    # na sygnale dziennym (1d) nie ma po co zaglądać co chwilę. Sprawdzamy co 30
    # min (świeca dzienna i tak nie zmienia trendu między pollami), co odciąża
    # apkę i budżet Claude. Krypto ma własny, szybszy poll (crypto_poll_interval).
    poll_interval_minutes: int = 30
    # Raised from 2.0 -> 3.0 (Tier 2): a lower bar woke Claude on routine noise
    # and drove low-edge, cost-bleeding trades. A wider trigger = fewer, better
    # analyses (the expectancy model showed cost meaningfully lifts break-even).
    price_move_trigger_pct: float = 3.0
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

    # Set this to match what you've actually loaded on console.anthropic.com so
    # the dashboard's "pozostało ~$X" reads as a real (estimated) remaining
    # balance. The hard pause (claude_pause_trading_at_budget) is a REDUNDANT
    # small-account safety: your real console credit is the true limit -- when it
    # runs out the API errors and the scheduled cycle skips gracefully (never
    # crashes), so this cap only guards against a runaway loop, not real spend.
    claude_monthly_budget_usd: float = 50.0
    claude_budget_alert_threshold_pct: float = 80.0

    # Finnhub API key (free tier: https://finnhub.io) -- an OPTIONAL, reliable,
    # keyed primary news source. Unlike the free RSS feeds it isn't UA/IP-blocked
    # on datacenter hosts, so it guarantees Claude sees market + per-ticker
    # company news even when outlets like CNBC/Barron's/Reddit reject the server.
    # Empty -> the news layer runs on RSS only, exactly as before (graceful).
    finnhub_api_key: str = ""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    report_recipient_email: str = "0grucha0@gmail.com"
    # Godzina codziennego podsumowania PUSH (nie maila -- patrz push_notifier.
    # send_daily_summary_push / scheduler._report_job).
    report_hour: int = 8
    report_minute: int = 0
    report_timezone: str = "Europe/Warsaw"

    database_url: str = "sqlite:///./data/trading.db"

    # --- Powiadomienia PUSH (telefon / Apple Watch przez PWA) ----------------
    # Web Push wymaga pary kluczy VAPID (wygeneruj raz: docker compose exec -T
    # app python scripts/gen_vapid.py, wklej do .env). Puste = push wyłączony (apka działa
    # normalnie, tylko bez powiadomień). vapid_subject to kontakt "mailto:" lub
    # URL wymagany przez spec Web Push. Powiadomienie leci przy KAŻDEJ realnej
    # transakcji (kupno/sprzedaż): co, ile, po ile, stan konta.
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:darius.gruszczynski@gmail.com"
    push_enabled: bool = True

    # Empty = no login required (backward-compatible default for existing
    # deployments). Format: "user1:pass1,user2:pass2".
    dashboard_users: str = ""

    # Read-only share link: gdy ustawisz sekret, każdy z linkiem
    # https://.../?share=<SEKRET> zobaczy dashboard TYLKO DO ODCZYTU (bez
    # logowania, bez żadnych przycisków/handlu -- serwer przepuszcza tylko GET
    # na dane, blokuje wszystkie akcje). Puste = udostępnianie wyłączone.
    # Wygeneruj długi losowy: python -c "import secrets; print(secrets.token_urlsafe(24))"
    share_token: str = ""

    @property
    def whitelist_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.trading_whitelist.split(",") if s.strip()]

    @property
    def extended_whitelist_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.extended_whitelist.split(",") if s.strip()]

    @property
    def extended_candidate_pool_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.extended_candidate_pool.split(",") if s.strip()]

    @property
    def high_spread_symbol_list(self) -> list[str]:
        return [s.strip().upper() for s in self.high_spread_symbols.split(",") if s.strip()]

    @property
    def defensive_symbol_list(self) -> list[str]:
        """Names allowed to be BOUGHT even in a risk-off regime -- gold, bonds
        and inverse ETFs that tend to hold up (or profit) when the broad market
        falls. Everything else is HOLD-only while risk-off."""
        return [s.strip().upper() for s in self.defensive_symbols.split(",") if s.strip()]

    @property
    def extended_defensive_symbol_list(self) -> list[str]:
        """Names the extended-hours leg may still BUY in a risk-off regime.
        Empty by default -- risk-off forces HOLD (cash)."""
        return [s.strip().upper() for s in self.extended_defensive_symbols.split(",") if s.strip()]

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
