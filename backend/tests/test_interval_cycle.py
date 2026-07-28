"""Symuluje kolejne TIKI schedulera (run_cycle wywoływane w kółko, tak jak
robi to APScheduler co poll_interval_minutes) i sprawdza, że trzy filary
strategii działają w interwałach:

  1. ZAPYTANIA DO CLAUDE  -- Claude jest pytany, gdy cykl się wyzwoli
     (pierwszy poll dnia, ruch ceny > próg, heartbeat), a POMIJANY na
     jałowym tiku (nic się nie ruszyło) -- to jest oszczędność budżetu.
  2. KUPOWANIE            -- decyzja BUY z Claude ląduje jako realne zlecenie.
  3. SPRZEDAWANIE         -- mechaniczne wyjście (take-profit/stop) sprzedaje
     pozycję na zwykłym pollu, BEZ pytania Claude.

Testujemy tu WYŁĄCZNIE mechanikę interwałów/wyzwalaczy i okablowanie
kupna/sprzedaży; bramki wejścia (filtr konfluencji, próg pewności, reżim)
mają własne testy, więc tutaj są wyłączone, żeby BUY był deterministyczny.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.services import market_hours, risk_manager, trading_engine
from app.services.claude_advisor import TradingDecision


@pytest.fixture(autouse=True)
def _regular_session(monkeypatch):
    now = datetime.now(market_hours.ET)
    monkeypatch.setattr(
        trading_engine.market_hours,
        "get_session_info",
        lambda broker: market_hours.SessionInfo(session=market_hours.REGULAR, regular_open=now, regular_close=now),
    )
    monkeypatch.setattr(trading_engine.earnings_calendar, "get_days_until_earnings", lambda tickers: {})


@dataclass
class _Order:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float


class Broker:
    """Fake Alpaca z MUTOWALNĄ ceną -- między tikami mogę ruszyć rynkiem."""

    def __init__(self):
        self.prices = {"SPY": 500.0, "QQQ": 400.0}
        self.balances = {"USD": 1000.0}
        self.orders: list[_Order] = []

    def get_price(self, symbol):
        return self.prices[symbol]

    def get_klines(self, symbol, interval="1h", limit=24):
        p = self.prices[symbol]
        return [[0, p, p, p, p, "1"] for _ in range(limit)]

    def get_account_balances(self):
        return dict(self.balances)

    def place_order_for_session(self, symbol, side, *, session="regular", usdt_amount=None, quantity=None):
        price = self.prices[symbol]
        if usdt_amount is not None:
            qty, val = usdt_amount / price, usdt_amount
        else:
            qty, val = quantity, quantity * price
        if side.upper() == "BUY":
            self.balances["USD"] -= val
            self.balances[symbol] = self.balances.get(symbol, 0.0) + qty
        else:
            self.balances["USD"] += val
            self.balances[symbol] = self.balances.get(symbol, 0.0) - qty
        order = _Order(str(len(self.orders) + 1), symbol, side.upper(), qty, price, val)
        self.orders.append(order)
        return order


class News:
    def get_headlines(self, currencies, limit=10):
        return []

    def get_new_ticker_headlines(self, tickers, seen):
        return [], {t: seen.get(t, []) for t in tickers}


class Advisor:
    """Skryptowany dubler Claude, który LICZY ile razy go zapytano."""

    def __init__(self, decision: TradingDecision):
        self.decision = decision
        self.calls = 0

    def set(self, decision: TradingDecision):
        self.decision = decision

    def decide(self, **kwargs):
        self.calls += 1
        return self.decision


class Ctx:
    def get_market_context(self):
        return {"vix_level": 15, "sp500_change_pct": 0.3}


def _prod_like_settings() -> Settings:
    return Settings(
        anthropic_api_key="test-key",
        alpaca_api_key="test-key",
        alpaca_api_secret="test-secret",
        alpaca_paper=True,
        quote_currency="USD",
        trading_whitelist="SPY,QQQ",
        # Jawne limity strat, żeby halt w teście był deterministyczny.
        daily_loss_limit_pct=10.0,
        weekly_loss_limit_pct=20.0,
        # Kadencja jak na prodzie: ruch 3% budzi Claude, heartbeat co 120 min.
        price_move_trigger_pct=3.0,
        full_analysis_every_minutes=120,
        # Stały take-profit, żeby wyjście było deterministyczne w teście:
        # stop 5% × RR 1.0 => take-profit uzbraja się na +5%.
        trailing_stop_enabled=False,
        stop_loss_pct=5.0,
        reward_risk_ratio=1.0,
        stop_loss_vol_mult=0.0,  # bez skalowania zmiennością -> stała odległość stopa
        hard_take_profit_pct=0.0,
        partial_take_profit_enabled=False,
        # Bramki wejścia off -> BUY deterministyczne (mają własne testy).
        entry_filter_enabled=False,
        min_buy_confidence=0.0,
        risk_per_trade_pct=0.0,
        max_concurrent_positions=0,
        regime_gate_enabled=False,
        adaptive_risk_enabled=False,
        earnings_blackout_days=0,
        max_new_positions_per_day=0,
        min_hold_minutes=0,
        auto_blacklist_stop_count=0,
        auto_demote_enabled=False,
        high_spread_size_scale=1.0,
        # Blackout newsów off w bazie -- News() zwraca [] celowo; dedykowany
        # test włącza go jawnie.
        news_blackout_halt_enabled=False,
    )


def test_claude_asked_on_trigger_and_buy_executes(db_session):
    """TIK 1 (pierwszy poll dnia): cykl się wyzwala -> Claude PYTANY -> BUY
    ląduje jako realne zlecenie. TIK 2 (nic się nie ruszyło): jałowy interwał
    -> Claude NIE pytany (oszczędność), brak zlecenia."""
    s = _prod_like_settings()
    broker, news, ctx = Broker(), News(), Ctx()
    advisor = Advisor(TradingDecision("BUY", "SPY", 10, 0.9, "Mocny sygnał wejścia."))

    # --- TIK 1: pierwszy poll -> wyzwalacz SCHEDULED_DAILY ---
    d1 = trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 1                       # Claude ZAPYTANY w interwale
    assert d1 is not None and d1.executed is True    # KUPOWANIE zadziałało
    assert broker.orders[-1].side == "BUY" and broker.orders[-1].symbol == "SPY"
    assert abs(broker.orders[-1].usdt_value - 100.0) < 1e-6  # 10% z 1000 USD

    # --- TIK 2: żadnego ruchu ceny, analiza dnia już zrobiona -> jałowy tik ---
    advisor.set(TradingDecision("HOLD", None, 0, 0.5, "Nie powinienem zostać zapytany."))
    orders_before = len(broker.orders)
    d2 = trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert d2 is None                                # jałowy interwał -> brak decyzji
    assert advisor.calls == 1                        # Claude NIE pytany ponownie
    assert len(broker.orders) == orders_before       # żadnego nowego zlecenia


def test_price_move_between_polls_wakes_claude(db_session):
    """Ruch ceny powyżej progu MIĘDZY pollami budzi Claude na kolejnym tiku
    (kadencja oparta na skumulowanym ruchu od kotwicy, nie na jednym pollu)."""
    s = _prod_like_settings()
    broker, news, ctx = Broker(), News(), Ctx()
    advisor = Advisor(TradingDecision("HOLD", None, 0, 0.6, "Trzymam."))

    # TIK 1: ustawia kotwice + odpala analizę dnia (Claude call #1).
    trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 1

    # TIK 2: bez ruchu -> jałowy, Claude nie pytany.
    trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 1

    # TIK 3: SPY skacze +4% (> próg 3%) -> Claude budzony ruchem ceny.
    broker.prices["SPY"] = 520.0
    d3 = trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 2
    assert d3 is not None and d3.triggered_by.value == "price_move"


def test_heartbeat_wakes_claude_after_interval(db_session):
    """Heartbeat: nawet bez ruchu ceny, gdy od ostatniej pełnej analizy minęło
    full_analysis_every_minutes, kolejny poll i tak budzi Claude."""
    s = _prod_like_settings()
    broker, news, ctx = Broker(), News(), Ctx()
    advisor = Advisor(TradingDecision("HOLD", None, 0, 0.5, "Trzymam."))

    trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 1

    # Cofnij znacznik ostatniej analizy o 200 min (> próg 120), zostawiając datę
    # dnia jako dziś (żeby wyzwalaczem był WYŁĄCZNIE heartbeat, nie "nowy dzień").
    state = risk_manager.get_state(db_session)
    stale = (datetime.now(timezone.utc) - timedelta(minutes=200)).isoformat()
    trading_engine._set_analysis_marks(state, "alpaca", date.today().isoformat(), stale)
    db_session.commit()

    trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 2  # heartbeat obudził Claude mimo braku ruchu


def test_mechanical_sell_fires_on_poll_without_claude(db_session):
    """SPRZEDAWANIE w interwale: pozycja na plusie powyżej take-profit jest
    sprzedawana przez mechaniczne wyjście na zwykłym pollu -- decyzja SELL
    NIE pochodzi od Claude (advisor tu tylko HOLD-uje), tylko z silnika."""
    s = _prod_like_settings()
    broker, news, ctx = Broker(), News(), Ctx()

    # TIK 1: kup SPY po 500.
    trading_engine.run_cycle(
        db_session, s, broker, news, Advisor(TradingDecision("BUY", "SPY", 10, 0.9, "Wejście.")), market_ctx=ctx
    )
    assert broker.orders[-1].side == "BUY"

    # TIK 2: SPY +6% (>= take-profit 5%). Advisor daje TYLKO HOLD -- gdyby SELL
    # pochodził od Claude, nie byłoby go. Liczymy zapytania do Claude, żeby
    # udowodnić, że sprzedaż jest mechaniczna.
    broker.prices["SPY"] = 530.0
    hold_only = Advisor(TradingDecision("HOLD", None, 0, 0.5, "Nie sprzedaję z Claude."))
    trading_engine.run_cycle(db_session, s, broker, news, hold_only, market_ctx=ctx)

    sells = [o for o in broker.orders if o.side == "SELL"]
    assert len(sells) == 1                    # SPRZEDAWANIE zadziałało
    assert sells[0].symbol == "SPY"
    # Sprzedaż jest mechaniczna: SPY zamknięte niezależnie od tego, co "powiedział" Claude.
    assert broker.balances.get("SPY", 0.0) <= 1e-9


class PortfolioAdvisor:
    """Dubler Claude w trybie zarządzania portfelem: zwraca ZESTAW akcji przez
    decide_portfolio (nie pojedynczą decide)."""

    def __init__(self, decisions: list[TradingDecision]):
        self.decisions = decisions
        self.calls = 0

    def decide_portfolio(self, **kwargs) -> list[TradingDecision]:
        self.calls += 1
        return list(self.decisions)


def test_portfolio_manager_executes_multiple_buys_in_one_cycle(db_session):
    """Tryb PM: jedno wywołanie zwraca DWA BUY (SPY + QQQ) i OBA lądują jako
    realne zlecenia w jednym cyklu. Rozmiary liczą się PO KOLEI od aktualnej
    wolnej gotówki (po pierwszym kupnie portfel jest odświeżany), więc drugi
    BUY bierze % z tego, co zostało -- to jest 'Claude prowadzi cały portfel'."""
    s = _prod_like_settings()
    broker, news, ctx = Broker(), News(), Ctx()
    advisor = PortfolioAdvisor(
        [
            TradingDecision("BUY", "SPY", 20, 0.9, "Wejście SPY."),
            TradingDecision("BUY", "QQQ", 15, 0.8, "Wejście QQQ."),
        ]
    )

    d = trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)
    assert advisor.calls == 1  # jedno wywołanie na cały portfel
    buys = [o for o in broker.orders if o.side == "BUY"]
    assert {o.symbol for o in buys} == {"SPY", "QQQ"}  # OBA kupione
    spy = next(o for o in buys if o.symbol == "SPY")
    qqq = next(o for o in buys if o.symbol == "QQQ")
    assert abs(spy.usdt_value - 200.0) < 1e-6  # 20% z 1000
    assert abs(qqq.usdt_value - 120.0) < 1e-6  # 15% z 800 (po odświeżeniu portfela)
    assert d is not None and d.symbol == "SPY"  # zwraca pierwszą decyzję


def test_news_blackout_halts_new_entries_and_skips_claude(db_session):
    """Gdy feedy newsów padają (za mało nagłówków), silnik NIE otwiera nowych
    pozycji na ślepo: zwraca HOLD z powodem 'blackout' i NIE pyta Claude --
    dokładnie 'wstrzymujemy trading z powodu braku danych'."""
    s = _prod_like_settings().model_copy(update={"news_blackout_halt_enabled": True, "news_min_headlines": 3})
    broker, ctx = Broker(), Ctx()

    class DarkNews:
        def get_headlines(self, currencies, limit=10):
            return []  # feedy w dół

        def get_new_ticker_headlines(self, tickers, seen):
            return [], {t: seen.get(t, []) for t in tickers}

    advisor = Advisor(TradingDecision("BUY", "SPY", 10, 0.9, "Nie powinno pójść do Claude."))
    d = trading_engine.run_cycle(db_session, s, broker, DarkNews(), advisor, market_ctx=ctx)

    assert advisor.calls == 0  # Claude NIE pytany bez danych
    assert d is not None and d.action.value == "HOLD"
    assert d.rejection_reason and "blackout" in d.rejection_reason.lower()
    assert len(broker.orders) == 0  # żadnego nowego wejścia


def test_halted_interval_skips_claude_entirely(db_session):
    """Gdy automat jest zatrzymany (halt limitem strat), zaplanowany tik NIE
    marnuje płatnego zapytania do Claude -- decyzja mogłaby zostać tylko
    odrzucona, więc silnik w ogóle nie pyta."""
    s = _prod_like_settings()
    # Utrąć halt: -15% w jednym oknie przebija dzienny limit 10%.
    risk_manager.update_portfolio_value(db_session, s, 1000.0)
    risk_manager.update_portfolio_value(db_session, s, 850.0)
    assert risk_manager.get_state(db_session).is_halted is True

    broker, news, ctx = Broker(), News(), Ctx()
    advisor = Advisor(TradingDecision("BUY", "SPY", 10, 0.9, "Nie powinno pójść do Claude."))
    decision = trading_engine.run_cycle(db_session, s, broker, news, advisor, market_ctx=ctx)

    assert advisor.calls == 0                  # ani jednego zapytania do Claude
    assert decision is not None and decision.action.value == "HOLD"
    assert decision.rejection_reason is not None
    assert len(broker.orders) == 0             # żadnego zlecenia


def test_low_budget_alert_fires_once_at_threshold_then_at_zero(db_session, monkeypatch):
    """Alarm o niskim budżecie: raz przy zejściu <=10% zostało, raz przy $0,
    bez re-firowania na tym samym poziomie."""
    from app.services import budget_tracker, trading_engine

    s = _prod_like_settings().model_copy(update={"claude_monthly_budget_usd": 100.0, "claude_low_budget_alert_pct": 10.0, "claude_pause_trading_at_budget": True})
    alarms = []
    monkeypatch.setattr(trading_engine.push_notifier, "send_alarm", lambda db, st, **kw: alarms.append(kw.get("tag")))
    trading_engine._low_budget_alert.update(month="", level=None)  # zbij stan

    budget_tracker.record_usage_cost(db_session, 92.0)  # zostało 8 (<=10%)
    trading_engine._maybe_alert_low_budget(db_session, s)
    trading_engine._maybe_alert_low_budget(db_session, s)  # brak re-fire
    assert alarms == ["low-budget"]

    budget_tracker.record_usage_cost(db_session, 10.0)  # zostało 0
    trading_engine._maybe_alert_low_budget(db_session, s)
    assert alarms == ["low-budget", "budget-out"]
