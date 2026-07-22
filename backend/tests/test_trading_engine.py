import json
from dataclasses import dataclass
from datetime import datetime

import pytest

from app.services import market_hours, risk_manager, trading_engine
from app.services.claude_advisor import TradingDecision


def _session_info(session: str) -> market_hours.SessionInfo:
    now = datetime.now(market_hours.ET)
    return market_hours.SessionInfo(
        session=session,
        regular_open=now,
        regular_close=now,
    )


@pytest.fixture(autouse=True)
def _default_regular_session(monkeypatch):
    """Most tests don't care about market-hours gating -- default every test
    to the regular session so run_cycle/check_take_profit_stop_loss behave as
    if the market is simply open, unless a test overrides this explicitly.
    Also stub the earnings calendar to 'no upcoming earnings' so no test hits
    the network; the earnings test overrides this explicitly."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.REGULAR)
    )
    monkeypatch.setattr(trading_engine.earnings_calendar, "get_days_until_earnings", lambda tickers: {})


class FakeAlpaca:
    def __init__(self, prices=None, balances=None):
        self.prices = prices or {"SPY": 500.0, "QQQ": 400.0}
        self.balances = balances or {"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0}
        self.orders = []

    def get_price(self, symbol):
        return self.prices[symbol]

    def get_klines(self, symbol, interval="1h", limit=24):
        return [[0, self.prices[symbol], self.prices[symbol], self.prices[symbol], self.prices[symbol], "1"]]

    def get_account_balances(self):
        return dict(self.balances)

    def place_market_order_usdt_amount(self, symbol, side, usdt_amount):
        price = self.prices[symbol]
        quantity = usdt_amount / price
        if side.upper() == "BUY":
            self.balances["USD"] -= usdt_amount
            self.balances[symbol] = self.balances.get(symbol, 0.0) + quantity
        else:
            self.balances["USD"] += usdt_amount
            self.balances[symbol] = self.balances.get(symbol, 0.0) - quantity
        order = _FakeOrder(str(len(self.orders) + 1), symbol, side.upper(), quantity, price, usdt_amount)
        self.orders.append(order)
        return order

    def place_market_order_quantity(self, symbol, side, raw_quantity):
        price = self.prices[symbol]
        usdt_value = raw_quantity * price
        if side.upper() == "BUY":
            self.balances["USD"] -= usdt_value
            self.balances[symbol] = self.balances.get(symbol, 0.0) + raw_quantity
        else:
            self.balances["USD"] += usdt_value
            self.balances[symbol] = self.balances.get(symbol, 0.0) - raw_quantity
        order = _FakeOrder(str(len(self.orders) + 1), symbol, side.upper(), raw_quantity, price, usdt_value)
        self.orders.append(order)
        return order

    def place_order_for_session(self, symbol, side, *, session="regular", usdt_amount=None, quantity=None):
        self.last_order_session = session
        if usdt_amount is not None:
            return self.place_market_order_usdt_amount(symbol, side, usdt_amount)
        return self.place_market_order_quantity(symbol, side, quantity)


@dataclass
class _FakeOrder:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float


class FakeNews:
    def get_headlines(self, currencies, limit=10):
        return []

    def get_new_ticker_headlines(self, tickers, seen):
        return [], {ticker: seen.get(ticker, []) for ticker in tickers}


class FakeAdvisor:
    def __init__(self, decision: TradingDecision):
        self.decision = decision
        self.calls = 0
        self.last_kwargs = None

    def decide(self, **kwargs):
        self.calls += 1
        self.last_kwargs = kwargs
        return self.decision


class FakeMarketContext:
    def get_market_context(self):
        return {"fear_greed_index": 62, "btc_dominance_pct": 54.1, "global_market_cap_change_24h_pct": 1.8}


def test_hold_decision_creates_no_trade(db_session, settings):
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert decision is not None
    assert decision.action.value == "HOLD"
    assert decision.executed is False
    assert len(broker.orders) == 0


def test_buy_decision_executes_trade(db_session, settings):
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Silny sygnał wzrostowy."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert decision.executed is True
    assert len(broker.orders) == 1
    assert broker.orders[0].symbol == "SPY"
    assert broker.orders[0].side == "BUY"
    # 10% of 1000 USD starting balance
    assert abs(broker.orders[0].usdt_value - 100.0) < 1e-6


def test_oversized_position_rejected_without_trade(db_session, settings):
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 90, 0.9, "Va banque."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert decision.executed is False
    assert len(broker.orders) == 0


def test_automated_trade_blocked_while_halted(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)  # trips 10% daily limit
    state = risk_manager.get_state(db_session)
    assert state.is_halted is True

    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Kupujemy dołek."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert len(broker.orders) == 0


def test_halted_scheduled_cycle_does_not_call_opus(db_session, settings):
    """Budget guard: when trading is halted, a scheduled cycle must NOT spend a
    Claude API call on a decision that could only ever be rejected."""
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)  # trips halt
    assert risk_manager.get_state(db_session).is_halted is True

    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Nie powinno zostać wywołane."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert advisor.calls == 0  # Claude never asked
    assert decision.rejection_reason is not None
    assert decision.action.value == "HOLD"
    assert len(broker.orders) == 0


def test_force_analysis_runs_opus_even_without_a_trigger(db_session, settings):
    """The 'Wymuś analizę' button (force=True) must always ask Claude, even when
    the daily analysis already ran and no price moved past the threshold --
    otherwise clicking it does nothing (the reported bug)."""
    risk_manager.get_state(db_session)
    # Mark today's analysis as already done so the scheduled trigger would NOT fire.
    trading_engine._mark_analysis_done_today(db_session)
    broker = FakeAlpaca()
    # Seed last-check prices so no price-move trigger either.
    trading_engine.check_trigger(db_session, settings, {"SPY": 500.0, "QQQ": 400.0})

    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.7, "Wymuszona analiza."))

    # Without force: nothing happens.
    assert trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor) is None
    assert advisor.calls == 0

    # With force: Claude is asked and a decision is produced.
    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)
    assert decision is not None
    assert advisor.calls == 1
    assert decision.triggered_by.value == "manual"


def test_manual_trade_executes_even_when_halted(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)
    assert risk_manager.get_state(db_session).is_halted is True

    broker = FakeAlpaca()
    trade = trading_engine.execute_manual_trade(
        db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0
    )

    assert trade.is_manual is True
    assert len(broker.orders) == 1


def test_manual_trade_rejects_symbol_outside_whitelist(db_session, settings):
    broker = FakeAlpaca()

    with pytest.raises(ValueError, match="whiteli"):
        trading_engine.execute_manual_trade(
            db_session, settings, broker, symbol="TSLA", side="BUY", usdt_amount=100.0
        )
    assert len(broker.orders) == 0


def test_resume_resets_daily_baseline_so_it_does_not_immediately_rehalt(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)  # trips 10% daily limit
    assert risk_manager.get_state(db_session).is_halted is True

    risk_manager.resume(db_session)
    # Portfolio is still down 15% from the *original* baseline, but resume()
    # should have reset the baseline to today's current value so this does
    # not immediately re-trip the halt.
    state = risk_manager.update_portfolio_value(db_session, settings, 850.0)

    assert state.is_halted is False


def test_pause_mid_analysis_blocks_execution_before_order_placed(db_session, settings):
    """Simulates a user clicking 'Zatrzymaj' while Claude is still 'thinking' --
    the advisor's decide() call, as a side effect, pauses the automat before
    returning its decision. run_cycle must re-check right before executing."""
    broker = FakeAlpaca()

    class PausingAdvisor:
        def decide(self, **kwargs):
            risk_manager.pause(db_session)
            return TradingDecision("BUY", "SPY", 10, 0.9, "Silny sygnał.")

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), PausingAdvisor())

    assert decision.executed is False
    assert decision.rejection_reason is not None
    assert len(broker.orders) == 0


def test_whitelist_supports_more_than_two_tickers(db_session, settings):
    """Verifies the whitelist is fully generic -- AAPL/NVDA work the same way
    as SPY/QQQ with no per-ticker code changes required."""
    four_ticker_settings = settings.model_copy(update={"trading_whitelist": "SPY,QQQ,AAPL,NVDA"})
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "QQQ": 400.0, "AAPL": 200.0, "NVDA": 120.0},
        balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "AAPL": 0.0, "NVDA": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("BUY", "NVDA", 10, 0.85, "NVDA wygląda mocno."))

    decision = trading_engine.run_cycle(db_session, four_ticker_settings, broker, FakeNews(), advisor)

    assert decision.executed is True
    assert len(broker.orders) == 1
    assert broker.orders[0].symbol == "NVDA"
    # 10% of 1000 USD starting balance
    assert abs(broker.orders[0].usdt_value - 100.0) < 1e-6


def test_symbol_unavailable_on_broker_does_not_abort_whole_cycle(db_session, settings):
    """Simulates NVDA failing to price (network hiccup, delisted ticker, ...)
    -- the cycle must still succeed for the other tickers instead of the whole
    analysis silently failing every time (which is exactly what happened
    before this fix: one bad symbol killed compute_portfolio, which killed
    the entire cycle, forever, for every ticker)."""
    four_ticker_settings = settings.model_copy(update={"trading_whitelist": "SPY,QQQ,AAPL,NVDA"})
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "QQQ": 400.0, "AAPL": 200.0},  # NVDA missing on purpose
        balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "AAPL": 0.0, "NVDA": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "SPY wygląda mocno."))

    decision = trading_engine.run_cycle(db_session, four_ticker_settings, broker, FakeNews(), advisor)

    assert decision.executed is True
    assert len(broker.orders) == 1
    assert broker.orders[0].symbol == "SPY"
    assert "NVDA" not in advisor.last_kwargs["whitelist"]
    assert set(advisor.last_kwargs["market_data"].keys()) == {"SPY", "QQQ", "AAPL"}


def test_compute_portfolio_records_failed_symbols(db_session, settings):
    """The dashboard needs to tell 'Alpaca genuinely doesn't have this ticker'
    apart from 'no data yet' -- so a symbol that fails to price must be
    recorded on the snapshot, not just silently dropped."""
    from app.models import PortfolioSnapshot

    four_ticker_settings = settings.model_copy(update={"trading_whitelist": "SPY,QQQ,AAPL,NVDA"})
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "QQQ": 400.0, "AAPL": 200.0},  # NVDA missing on purpose
        balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "AAPL": 0.0, "NVDA": 0.0},
    )

    portfolio = trading_engine.compute_portfolio(db_session, four_ticker_settings, broker)

    assert portfolio["failed_symbols"] == ["NVDA"]
    snapshot = db_session.query(PortfolioSnapshot).order_by(PortfolioSnapshot.id.desc()).first()
    assert json.loads(snapshot.failed_symbols_json) == ["NVDA"]


def test_compute_portfolio_records_held_extended_qty(db_session, settings):
    """Alpaca keys a held extended position by the FULL symbol ("BTCUSD"), not the
    base ("BTC"). compute_portfolio must find that qty so the coin isn't recorded
    as 0 (which would hide it and zero its value on the dashboard)."""
    from app.models import PortfolioSnapshot

    extended_settings = settings.model_copy(update={"extended_whitelist": "BTCUSD,ETHUSD"})
    broker = FakeAlpaca(
        prices={"BTCUSD": 50000.0, "ETHUSD": 3000.0},
        balances={"USD": 500.0, "BTCUSD": 0.01, "ETHUSD": 0.0},
    )

    portfolio = trading_engine.compute_portfolio(
        db_session, extended_settings, broker, venue="extended", whitelist=["BTCUSD", "ETHUSD"]
    )

    # 0.01 BTC @ 50k = 500 of position value on top of 500 cash.
    assert portfolio["balances"]["BTC"] == 0.01
    assert portfolio["total_value_usdt"] == 1000.0
    snapshot = db_session.query(PortfolioSnapshot).order_by(PortfolioSnapshot.id.desc()).first()
    assert json.loads(snapshot.balances_json)["BTC"] == 0.01


def test_compute_portfolio_values_held_position_off_whitelist(db_session, settings):
    """A held ticker that isn't on the trading whitelist must still be valued and
    surfaced -- otherwise it vanishes from the dashboard and the account total is
    understated. It's display/valuation only; trading stays whitelist-gated."""
    two_ticker = settings.model_copy(update={"trading_whitelist": "SPY,QQQ"})
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "QQQ": 400.0, "TSLA": 250.0},
        balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "TSLA": 2.0},  # holds TSLA, not whitelisted
    )

    portfolio = trading_engine.compute_portfolio(db_session, two_ticker, broker)

    assert portfolio["balances"]["TSLA"] == 2.0
    assert portfolio["total_value_usdt"] == 1000.0 + 2.0 * 250.0


def test_dual_listed_ticker_not_double_counted(db_session, settings):
    """A ticker on BOTH whitelists (e.g. XLF) must be valued on exactly ONE leg.
    Regression for the account being overstated (and the position shown twice --
    once as an entry-less "adopted" copy) when the equities snapshot AND the
    extended snapshot each counted the same shared Alpaca position."""
    from app.api.routes_dashboard import _account_view

    s = settings.model_copy(update={"trading_whitelist": "SPY,XLF", "extended_whitelist": "XLF,GDX"})
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "XLF": 40.0, "GDX": 30.0},
        balances={"USD": 100.0, "SPY": 0.0, "XLF": 2.0, "GDX": 0.0},  # holds 2 XLF = $80
    )
    trading_engine.compute_portfolio(db_session, s, broker, venue="alpaca")
    trading_engine.compute_portfolio(db_session, s, broker, venue="extended", whitelist=s.extended_whitelist_symbols)

    acct = _account_view(db_session)
    # cash 100 + XLF 80 counted ONCE == 180 (the bug made this 260).
    assert acct["total_value"] == 180.0
    # No ledger for XLF -> classified by whitelist membership -> extended leg.
    assert acct["extended_positions_value"] == 80.0
    assert acct["equity_positions_value"] == 0.0


def test_owned_ticker_stays_on_the_leg_that_opened_it(db_session, settings):
    """Ownership wins: XLF bought by the SESJA (alpaca) engine stays on that leg
    -- valued there with its real cost basis -- even though it also sits on the
    extended whitelist. It must NOT be re-attributed to the extended leg as an
    entry-less adopted position."""
    from app.models import Trade, TradeMode
    from app.api.routes_dashboard import _account_view

    s = settings.model_copy(update={"trading_whitelist": "SPY,XLF", "extended_whitelist": "XLF,GDX"})
    db_session.add(
        Trade(symbol="XLF", side="BUY", quantity=2.0, price=35.0, usdt_value=70.0, mode=TradeMode.LIVE, venue="alpaca")
    )
    db_session.commit()
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "XLF": 40.0, "GDX": 30.0},
        balances={"USD": 100.0, "SPY": 0.0, "XLF": 2.0, "GDX": 0.0},
    )
    trading_engine.compute_portfolio(db_session, s, broker, venue="alpaca")
    trading_engine.compute_portfolio(db_session, s, broker, venue="extended", whitelist=s.extended_whitelist_symbols)

    acct = _account_view(db_session)
    assert acct["total_value"] == 180.0
    assert acct["equity_positions_value"] == 80.0  # valued on SESJA (owner)
    assert acct["extended_positions_value"] == 0.0
    assert trading_engine.venue_for_holding(db_session, "XLF", s) == "alpaca"


def test_whitelist_rejects_symbol_not_in_four_ticker_list(db_session, settings):
    four_ticker_settings = settings.model_copy(update={"trading_whitelist": "SPY,QQQ,AAPL,NVDA"})
    broker = FakeAlpaca(
        prices={"SPY": 500.0, "QQQ": 400.0, "AAPL": 200.0, "NVDA": 120.0},
        balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "AAPL": 0.0, "NVDA": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("BUY", "TSLA", 10, 0.85, "Poza whitelistą."))

    decision = trading_engine.run_cycle(db_session, four_ticker_settings, broker, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert len(broker.orders) == 0


def test_failed_analysis_does_not_burn_the_daily_trigger(db_session, settings):
    broker = FakeAlpaca()

    class FailingAdvisor:
        def decide(self, **kwargs):
            raise RuntimeError("Anthropic API down")

    with pytest.raises(RuntimeError):
        trading_engine.run_cycle(db_session, settings, broker, FakeNews(), FailingAdvisor())

    # last_full_analysis_date must NOT have been marked -- the next cycle
    # (e.g. after Claude recovers) should still be able to trigger today.
    state = risk_manager.get_state(db_session)
    assert state.last_full_analysis_date == ""


def test_market_context_reaches_advisor_and_gets_logged(db_session, settings):
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, FakeMarketContext())

    assert advisor.last_kwargs["market_context"] == {
        "fear_greed_index": 62,
        "btc_dominance_pct": 54.1,
        "global_market_cap_change_24h_pct": 1.8,
    }
    assert json.loads(decision.market_context_snapshot)["fear_greed_index"] == 62


def test_average_cost_basis_tracks_buys_and_sells(db_session, settings):
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 10000.0, "SPY": 0.0, "QQQ": 0.0})
    # Buy 1 SPY @100, then 1 SPY @300 -> avg 200 over qty 2.
    broker.prices["SPY"] = 100.0
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", quantity=1.0)
    broker.prices["SPY"] = 300.0
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", quantity=1.0)

    assert abs(trading_engine.average_cost_basis(db_session, "SPY") - 200.0) < 1e-6

    # Sell 1 -> still 1 held at the same average 200.
    broker.prices["SPY"] = 250.0
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="SELL", quantity=1.0)
    assert abs(trading_engine.average_cost_basis(db_session, "SPY") - 200.0) < 1e-6


def test_average_cost_basis_none_when_flat(db_session, settings):
    assert trading_engine.average_cost_basis(db_session, "SPY") is None


def test_fixed_take_profit_sells_when_price_rises(db_session, settings):
    fixed = settings.model_copy(update={"trailing_stop_enabled": False})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, fixed, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # +4% > take_profit_pct (3)

    portfolio = trading_engine.compute_portfolio(db_session, fixed, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, fixed, broker, portfolio)

    assert len(exits) == 1
    assert exits[0].side == "SELL"
    assert "Take-profit" in exits[0].decision.reasoning


def test_trailing_stop_lets_winner_run_then_sells_on_pullback(db_session, settings):
    """Default mode: at +4% the position ARMS a trailing stop but is NOT sold
    (winner keeps running); it sells only once price falls trailing_stop_pct
    (1.5%) below the peak."""
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)

    # Rises to +10% -> arms trailing, peak=110, but no sell (still climbing).
    broker.prices["SPY"] = 110.0
    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio) == []

    # Pulls back to 108 (>1.5% below the 110 peak) -> trailing stop sells.
    broker.prices["SPY"] = 108.0
    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio)

    assert len(exits) == 1
    assert "Trailing-stop" in exits[0].decision.reasoning


def test_trailing_not_armed_below_take_profit(db_session, settings):
    """A small pullback before the +take_profit_pct arm threshold must NOT
    trigger the trailing stop."""
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)

    broker.prices["SPY"] = 102.0  # +2%, below +3% arm
    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio) == []

    broker.prices["SPY"] = 100.5  # pulled back but never armed -> no trailing exit
    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio) == []


def test_stop_loss_auto_sells_when_price_drops(db_session, settings):
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 97.0  # -3% < -stop_loss_pct (2)

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio)

    assert len(exits) == 1
    assert exits[0].side == "SELL"
    assert "Stop-loss" in exits[0].decision.reasoning


def test_delisted_symbol_force_closed_even_at_a_loss(db_session, settings):
    """A symbol removed from the whitelist after being bought must not be
    orphaned -- the position is force-closed in full, even at a loss and even
    within the min-hold window, rather than silently dropping out of every
    future exit check."""
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0, "TSLA": 250.0}, balances={"USD": 1000.0})
    full = settings.model_copy(update={"trading_whitelist": "SPY,QQQ,TSLA"})
    trading_engine.execute_manual_trade(db_session, full, broker, symbol="TSLA", side="BUY", usdt_amount=100.0)
    broker.prices["TSLA"] = 245.0  # down slightly -- inside normal stop/trailing thresholds

    # TSLA removed from the whitelist going forward.
    trimmed = settings.model_copy(update={"trading_whitelist": "SPY,QQQ"})
    portfolio = trading_engine.compute_portfolio(db_session, trimmed, broker)
    assert "TSLA" in portfolio["prices"]  # still valued even though off-whitelist

    exits = trading_engine.check_take_profit_stop_loss(
        db_session, trimmed, broker, portfolio, whitelist=trimmed.whitelist_symbols
    )

    assert len(exits) == 1
    assert exits[0].symbol == "TSLA"
    assert exits[0].side == "SELL"
    assert "usunięty z listy" in exits[0].decision.reasoning


def test_adopted_position_gets_trailing_protection(db_session, settings):
    """A position with NO buy trade of ours (pre-existing / bought manually) has
    no cost basis, but must still be protected -- a trailing stop from the
    highest observed price triggers a full close when price falls far enough."""
    from app.services import risk_manager

    broker = FakeAlpaca(prices={"SPY": 110.0, "QQQ": 400.0}, balances={"USD": 100.0, "SPY": 1.0})
    state = risk_manager.get_state(db_session)
    state.position_peaks_json = json.dumps({"SPY": 130.0})  # observed high well above 110
    db_session.commit()

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio)

    assert len(exits) == 1
    assert exits[0].symbol == "SPY"
    assert exits[0].side == "SELL"
    assert "bez znanego wejścia" in exits[0].decision.reasoning


def test_adopted_position_held_within_trailing(db_session, settings):
    from app.services import risk_manager

    broker = FakeAlpaca(prices={"SPY": 129.5, "QQQ": 400.0}, balances={"USD": 100.0, "SPY": 1.0})
    state = risk_manager.get_state(db_session)
    state.position_peaks_json = json.dumps({"SPY": 130.0})  # only ~0.4% off the peak
    db_session.commit()

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio) == []


def test_adopted_position_skipped_when_protection_off(db_session, settings):
    """protect_adopted_positions=False restores the old behaviour: a position
    without a known entry is left entirely alone by the mechanical exit."""
    from app.services import risk_manager

    s = settings.model_copy(update={"protect_adopted_positions": False})
    broker = FakeAlpaca(prices={"SPY": 110.0, "QQQ": 400.0}, balances={"USD": 100.0, "SPY": 1.0})
    state = risk_manager.get_state(db_session)
    state.position_peaks_json = json.dumps({"SPY": 130.0})
    db_session.commit()

    portfolio = trading_engine.compute_portfolio(db_session, s, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, s, broker, portfolio) == []


def test_no_exit_within_thresholds(db_session, settings):
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 101.5  # +1.5%, between -2% and +3%

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio) == []


def test_tpsl_does_not_fire_while_stopped(db_session, settings):
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # would take-profit
    risk_manager.pause(db_session)  # user pressed STOP

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio) == []


def test_tpsl_does_not_fire_while_market_closed(db_session, settings):
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # would take-profit if market were open

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    closed = _session_info(market_hours.CLOSED)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio, closed) == []


def test_tpsl_fires_during_regular_session(db_session, settings):
    fixed = settings.model_copy(update={"trailing_stop_enabled": False})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, fixed, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # +4% > take_profit_pct (3) -> immediate sell, fixed take-profit

    portfolio = trading_engine.compute_portfolio(db_session, fixed, broker)
    regular = _session_info(market_hours.REGULAR)
    exits = trading_engine.check_take_profit_stop_loss(db_session, fixed, broker, portfolio, regular)

    assert len(exits) == 1
    assert broker.last_order_session == market_hours.REGULAR


def test_stop_loss_sets_cooldown_and_blocks_rebuy(db_session, settings):
    """After a stop-loss, Claude must not be able to re-buy that ticker until
    the cooldown expires -- the anti-churn guard for a small account."""
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 97.0  # stop-loss

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio)

    active, reason = trading_engine.stop_loss_cooldown_active(db_session, "SPY")
    assert active is True
    assert "Cooldown" in reason

    # Claude tries to buy back in immediately -> must be rejected, no order.
    broker.prices["SPY"] = 100.0
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Odbicie, wracam."))
    orders_before = len(broker.orders)
    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    assert decision.executed is False
    assert "Cooldown" in (decision.rejection_reason or "")
    assert len(broker.orders) == orders_before


def test_take_profit_does_not_set_cooldown(db_session, settings):
    """Only stop-loss triggers a cooldown -- a winning exit shouldn't block
    re-entry if a fresh signal appears."""
    fixed = settings.model_copy(update={"trailing_stop_enabled": False})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, fixed, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # take-profit

    portfolio = trading_engine.compute_portfolio(db_session, fixed, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, fixed, broker, portfolio)
    assert len(exits) == 1  # sanity: it did exit

    active, _ = trading_engine.stop_loss_cooldown_active(db_session, "SPY")
    assert active is False


def test_trade_alert_is_best_effort_and_skipped_without_smtp(db_session, settings):
    """A trade must succeed and be recorded even though the alert email can't be
    sent (SMTP not configured in tests) -- the alert is fire-and-forget."""
    broker = FakeAlpaca()
    trade = trading_engine.execute_manual_trade(
        db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=50.0
    )
    assert trade.id is not None
    assert len(broker.orders) == 1


def test_cooldown_zero_minutes_never_blocks(db_session, settings):
    no_cooldown = settings.model_copy(update={"stop_loss_cooldown_minutes": 0})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, no_cooldown, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 97.0

    portfolio = trading_engine.compute_portfolio(db_session, no_cooldown, broker)
    trading_engine.check_take_profit_stop_loss(db_session, no_cooldown, broker, portfolio)

    active, _ = trading_engine.stop_loss_cooldown_active(db_session, "SPY")
    assert active is False


def test_run_cycle_without_market_ctx_does_not_crash(db_session, settings):
    """market_ctx is optional so existing callers/tests that omit it keep
    working, and the trading engine never hard-depends on this data source."""
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert decision is not None
    assert advisor.last_kwargs["market_context"] == {}


def test_scheduled_cycle_skipped_when_market_closed(db_session, settings, monkeypatch):
    """Stocks/ETFs aren't 24/7 like extended -- a scheduled poll outside market
    hours must do nothing (and never burn Claude budget), same as any other
    routine no-op cycle."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.CLOSED)
    )
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Nie powinno zostać wywołane."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor)

    assert decision is None
    assert advisor.calls == 0
    assert len(broker.orders) == 0


def test_forced_analysis_runs_when_market_closed_but_cannot_execute(db_session, settings, monkeypatch):
    """A manual 'Wymuś analizę' still asks Claude even outside market hours (so
    the user can see its read on demand), but a resulting BUY/SELL must not
    execute -- Alpaca would reject the order anyway."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.CLOSED)
    )
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Wygląda dobrze."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    assert advisor.calls == 1
    assert decision.executed is False
    assert "zamknięty" in (decision.rejection_reason or "").lower()
    assert len(broker.orders) == 0


def test_scheduled_cycle_executes_during_regular_session(db_session, settings, monkeypatch):
    """A scheduled cycle during the regular session must actually execute (via
    a session-routed order), not just passively let Claude look without acting."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.REGULAR)
    )
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Silny sygnał."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    assert decision.executed is True
    assert len(broker.orders) == 1
    assert broker.last_order_session == market_hours.REGULAR


def test_news_event_triggers_cycle_independent_of_price_move(db_session, settings):
    """A brand-new per-ticker headline (earnings, material news) must wake
    Claude even when nothing else would have triggered this cycle -- crucial
    pre-/after-market where price can lag the news print."""
    trading_engine._mark_analysis_done_today(db_session)  # rule out the daily fallback
    broker = FakeAlpaca()
    trading_engine.check_trigger(db_session, settings, broker.prices)  # seed last-check prices, rule out price-move

    class NewsWithFreshHeadline:
        def get_headlines(self, currencies, limit=10):
            return []

        def get_new_ticker_headlines(self, tickers, seen):
            return [{"title": "SPY Corp reports blowout earnings", "published_at": "", "source": "Yahoo Finance (SPY)"}], {
                t: seen.get(t, []) for t in tickers
            }

    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.7, "Reakcja na earnings."))

    decision = trading_engine.run_cycle(db_session, settings, broker, NewsWithFreshHeadline(), advisor)

    assert decision is not None
    assert advisor.calls == 1
    assert decision.triggered_by.value == "news_event"
    # The triggering headline must reach Claude flagged and front-loaded, so
    # it knows exactly what it's reacting to.
    news_arg = advisor.last_kwargs["news"]
    assert news_arg[0]["title"] == "SPY Corp reports blowout earnings"
    assert news_arg[0]["just_published"] is True


def test_market_data_sent_to_claude_is_slimmed(db_session, settings):
    """Prompt cost control: Claude gets a 24h summary + the last few bars, not
    the full raw 24-bar series per ticker."""
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Spokojnie."))

    trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    for payload in advisor.last_kwargs["market_data"].values():
        assert "klines_1h_24" not in payload
        assert len(payload["recent_bars"]) <= 8
        assert "change_period_pct" in payload


def test_performance_context_gives_claude_its_track_record(db_session, settings):
    """Claude must see its own open positions (entry vs current, unrealized
    P&L) and recent trades so it can learn instead of analysing from scratch
    every cycle."""
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 110.0  # position now +10%

    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Trzymam."))
    trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    perf = advisor.last_kwargs["performance_context"]
    assert len(perf["open_positions"]) == 1
    pos = perf["open_positions"][0]
    assert pos["symbol"] == "SPY"
    assert pos["entry_price"] == 100.0
    assert pos["current_price"] == 110.0
    assert pos["unrealized_pnl_pct"] == 10.0
    assert any(t["symbol"] == "SPY" and t["side"] == "BUY" for t in perf["recent_trades"])


def test_failed_mechanical_exit_surfaces_real_reason(db_session, settings):
    """A SELL that fails at the broker (Alpaca hiccup, qty rejection, ...) must
    NOT crash the cycle -- the peak keeps being tracked so the exit retries
    next cycle, and the recorded reason surfaces the REAL exception text
    instead of a one-size-fits-all guess."""

    class FailingSellBroker(FakeAlpaca):
        def place_order_for_session(self, symbol, side, *, session="regular", usdt_amount=None, quantity=None):
            if side.upper() == "SELL":
                raise ValueError("Alpaca 403 insufficient qty available")
            return super().place_order_for_session(symbol, side, session=session, usdt_amount=usdt_amount, quantity=quantity)

    broker = FailingSellBroker(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 97.0  # would stop-loss

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    regular = _session_info(market_hours.REGULAR)

    # Must not raise, and must not record a completed exit trade.
    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio, regular)
    assert exits == []
    # Peak/state preserved so the exit can retry next cycle.
    state = risk_manager.get_state(db_session)
    import json as _json

    assert "SPY" in _json.loads(state.position_peaks_json)

    from app.models import Decision

    decision = db_session.query(Decision).filter(Decision.symbol == "SPY").order_by(Decision.id.desc()).first()
    assert "insufficient qty" in decision.rejection_reason


def test_manual_trade_stamps_venue_and_uses_venue_whitelist(db_session, settings):
    """A manual extended trade must validate against the extended whitelist and
    stamp its records venue='extended' (so they land in the right portfolio)."""
    from app.models import Trade

    broker = FakeAlpaca(prices={"BTCUSD": 50000.0}, balances={"USD": 1000.0, "BTCUSD": 0.0})
    trade = trading_engine.execute_manual_trade(
        db_session, settings, broker, symbol="BTCUSD", side="BUY", usdt_amount=100.0,
        venue="extended", whitelist=["BTCUSD", "ETHUSD"],
    )
    assert trade.venue == "extended"
    assert db_session.query(Trade).filter(Trade.venue == "extended").count() == 1

    # A symbol outside the venue whitelist is rejected.
    try:
        trading_engine.execute_manual_trade(
            db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0,
            venue="extended", whitelist=["BTCUSD", "ETHUSD"],
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_extended_venue_cycle_is_isolated_and_stamped(db_session, settings, monkeypatch):
    """The extended venue trades 24/7 (always_open) even while the US market is
    closed, stamps its records venue='extended', and uses its OWN state columns
    so the equities venue's anchors stay untouched."""
    from app.models import Trade

    extended_settings = settings.model_copy(update={"extended_enabled": True})
    risk_manager.resume(db_session, "extended")  # extended starts paused -> press START
    # Equities would be CLOSED right now -- extended must trade anyway.
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.CLOSED)
    )
    broker = FakeAlpaca(prices={"BTCUSD": 50000.0, "ETHUSD": 3000.0}, balances={"USD": 1000.0, "BTCUSD": 0.0, "ETHUSD": 0.0})
    advisor = FakeAdvisor(TradingDecision("BUY", "BTCUSD", 10, 0.9, "Krypto mocne."))

    decision = trading_engine.run_cycle(
        db_session, extended_settings, broker, FakeNews(), advisor, force=True,
        venue="extended", whitelist=["BTCUSD", "ETHUSD"], always_open=True,
    )

    assert decision.venue == "extended"
    assert decision.executed is True
    trade = db_session.query(Trade).order_by(Trade.id.desc()).first()
    assert trade.venue == "extended"
    assert trade.symbol == "BTCUSD"

    state = risk_manager.get_state(db_session)
    assert json.loads(state.extended_check_prices_json)  # extended anchors were set
    assert json.loads(state.last_check_prices_json or "{}") == {}  # equities column untouched


def test_dust_position_below_min_notional_is_skipped(db_session, settings):
    """A ~1e-7 share remainder (dust worth fractions of a cent) can't be sold
    -- it's below Alpaca's min order -- so the mechanical exit must ignore it
    instead of retrying a doomed SELL (and logging an error) every poll."""
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    # Simulate an almost-full exit leaving dust: hold ~5.9e-7 SPY at $97.
    broker.balances["SPY"] = 0.00000059
    broker.prices["SPY"] = 97.0  # underwater -> would stop-loss if it were sellable

    portfolio = trading_engine.compute_portfolio(db_session, settings, broker)
    regular = _session_info(market_hours.REGULAR)

    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, broker, portfolio, regular)
    assert exits == []
    assert len(broker.orders) == 1  # only the initial BUY -- no doomed dust SELL


def test_earnings_blackout_blocks_new_buy(db_session, settings, monkeypatch):
    """No fresh position into a report the stop-loss can't protect against."""
    monkeypatch.setattr(
        trading_engine.earnings_calendar, "get_days_until_earnings", lambda tickers: {"SPY": 1}
    )
    guarded = settings.model_copy(update={"earnings_blackout_days": 2})
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Kupuję przed wynikami."))

    decision = trading_engine.run_cycle(db_session, guarded, broker, FakeNews(), advisor, force=True)

    assert decision.executed is False
    assert "earnings" in (decision.rejection_reason or "").lower()
    assert len(broker.orders) == 0


def test_earnings_blackout_allows_buy_outside_window(db_session, settings, monkeypatch):
    monkeypatch.setattr(
        trading_engine.earnings_calendar, "get_days_until_earnings", lambda tickers: {"SPY": 9}
    )
    guarded = settings.model_copy(update={"earnings_blackout_days": 2})
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Wyniki daleko, kupuję."))

    decision = trading_engine.run_cycle(db_session, guarded, broker, FakeNews(), advisor, force=True)

    assert decision.executed is True
    assert len(broker.orders) == 1


def test_slow_cumulative_drift_triggers_price_move(db_session, settings):
    """THE bug from the first live session: moves were measured poll-to-poll,
    so a slow steady trend (0.6% per poll) never reached the 2% threshold and
    the automat sat idle all day. Cumulative drift from the last analysis
    anchor must trigger."""
    trading_engine._mark_analysis_done_today(db_session)  # rule out daily fallback

    # Anchor at 100.
    triggered, _ = trading_engine.check_trigger(db_session, settings, {"SPY": 100.0, "QQQ": 400.0})
    assert triggered is False

    # Three slow polls: +0.7%, +1.4%, +2.1% cumulative -- each step is under
    # the 2% threshold vs the PREVIOUS poll, but the third crosses it vs the
    # anchor. The old per-poll logic never fired here.
    assert trading_engine.check_trigger(db_session, settings, {"SPY": 100.7, "QQQ": 400.0})[0] is False
    assert trading_engine.check_trigger(db_session, settings, {"SPY": 101.4, "QQQ": 400.0})[0] is False
    triggered, reason = trading_engine.check_trigger(db_session, settings, {"SPY": 102.1, "QQQ": 400.0})
    assert triggered is True
    assert reason.value == "price_move"

    # Anchors reset after a trigger -- the same price no longer re-triggers.
    trading_engine._mark_analysis_done_today(db_session)
    assert trading_engine.check_trigger(db_session, settings, {"SPY": 102.1, "QQQ": 400.0})[0] is False


def test_heartbeat_triggers_analysis_after_interval(db_session, settings):
    """Even with zero price movement, Claude must take a full look at the
    market every full_analysis_every_minutes -- setups aren't only spikes."""
    from datetime import datetime, timedelta, timezone

    heartbeat = settings.model_copy(update={"full_analysis_every_minutes": 120})
    trading_engine._mark_analysis_done_today(db_session)
    state = risk_manager.get_state(db_session)

    # Fresh analysis -> no heartbeat yet.
    assert trading_engine.check_trigger(db_session, heartbeat, {"SPY": 100.0, "QQQ": 400.0})[0] is False

    # Backdate the last analysis past the interval -> heartbeat fires.
    state.last_analysis_at = (datetime.now(timezone.utc) - timedelta(minutes=121)).isoformat()
    db_session.commit()
    triggered, reason = trading_engine.check_trigger(db_session, heartbeat, {"SPY": 100.0, "QQQ": 400.0})
    assert triggered is True
    assert reason.value == "scheduled_daily"


def test_heartbeat_disabled_when_zero(db_session, settings):
    from datetime import datetime, timedelta, timezone

    no_heartbeat = settings.model_copy(update={"full_analysis_every_minutes": 0})
    trading_engine._mark_analysis_done_today(db_session)
    state = risk_manager.get_state(db_session)
    state.last_analysis_at = (datetime.now(timezone.utc) - timedelta(hours=10)).isoformat()
    db_session.commit()

    assert trading_engine.check_trigger(db_session, no_heartbeat, {"SPY": 100.0, "QQQ": 400.0})[0] is False


def test_volatility_adjusted_size_scales_down_volatile_and_leaves_calm(settings):
    calm = settings.model_copy(update={"volatility_reference_pct": 1.0, "volatility_min_scale": 0.3})
    # Below/at reference -> unchanged.
    assert trading_engine.volatility_adjusted_size(calm, 20.0, 0.8) == 20.0
    assert trading_engine.volatility_adjusted_size(calm, 20.0, 1.0) == 20.0
    # 4x reference vol -> scaled to reference/vol = 0.25, floored at 0.3 -> 6%.
    assert trading_engine.volatility_adjusted_size(calm, 20.0, 4.0) == 6.0
    # 2x reference vol -> 0.5 scale -> 10%.
    assert trading_engine.volatility_adjusted_size(calm, 20.0, 2.0) == 10.0
    # Unknown vol -> unchanged.
    assert trading_engine.volatility_adjusted_size(calm, 20.0, None) == 20.0


def test_volatile_ticker_buy_is_sized_down_end_to_end(db_session, settings):
    """A BUY on a volatile ticker should execute a SMALLER notional than the
    raw size_pct would imply, because vol-scaling cut it."""
    vol_settings = settings.model_copy(
        update={"volatility_reference_pct": 1.0, "volatility_min_scale": 0.3, "max_position_pct": 100.0}
    )

    class VolatileBroker(FakeAlpaca):
        def get_klines(self, symbol, interval="1h", limit=24):
            # Choppy series -> high volatility_pct_1h for SPY.
            return [[0, 0, 0, 0, 100.0 * (1.06 if i % 2 else 0.94), "1"] for i in range(limit)]

    broker = VolatileBroker(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 50, 0.9, "Mocny sygnał ale dziki ticker."))

    decision = trading_engine.run_cycle(db_session, vol_settings, broker, FakeNews(), advisor, force=True)

    assert decision.executed is True
    # Raw 50% of 1000 = $500; vol-scaling must have cut it well below that.
    assert broker.orders[0].usdt_value < 500.0
    assert decision.size_pct < 50.0


def test_dynamic_stop_loss_scales_with_volatility(settings):
    """The volatility-scaled stop must widen for volatile tickers and fall back
    to the fixed stop when volatility is unknown -- this is the fix for the
    whipsaw where a fixed 2% stop sold every dip at a loss."""
    s = settings.model_copy(update={
        "stop_loss_pct": 2.0, "stop_loss_vol_mult": 6.0,
        "stop_loss_min_pct": 2.5, "stop_loss_max_pct": 12.0,
    })
    # Unknown volatility -> fixed stop.
    assert trading_engine.dynamic_stop_loss_pct(s, None) == 2.0
    # Calm ticker (0.25%/1h) -> 6*0.25=1.5, floored to the 2.5% minimum.
    assert trading_engine.dynamic_stop_loss_pct(s, 0.25) == 2.5
    # Volatile ticker (1.5%/1h) -> 6*1.5=9% (within band).
    assert trading_engine.dynamic_stop_loss_pct(s, 1.5) == 9.0
    # Very volatile (extended, 3%/1h) -> 18% capped at the 12% max.
    assert trading_engine.dynamic_stop_loss_pct(s, 3.0) == 12.0
    # Disabled -> fixed stop regardless of volatility.
    off = s.model_copy(update={"stop_loss_vol_mult": 0.0})
    assert trading_engine.dynamic_stop_loss_pct(off, 3.0) == 2.0


# ============================================================================
# Pakiet 1 -- geometria zysk/ryzyko (coupled reward + partial take-profit)
# ============================================================================
def test_reward_levels_couple_to_stop_distance(settings):
    """Take-profit arm, trailing and partial levels must scale WITH the stop
    distance so the risk/reward ratio stays proportional (fixing the inverted
    R:R). Falls back to fixed take_profit/trailing when coupling is disabled."""
    s = settings.model_copy(update={
        "reward_risk_ratio": 1.5, "trailing_stop_frac": 0.5,
        "partial_take_profit_r": 1.0, "take_profit_pct": 3.0, "trailing_stop_pct": 1.5,
    })
    tp_arm, trailing, partial_r = trading_engine._reward_levels(s, 8.0)  # wide (volatile) stop
    assert tp_arm == 12.0      # 8 * 1.5
    assert trailing == 4.0     # 8 * 0.5
    assert partial_r == 8.0    # 8 * 1.0
    # Coupling disabled -> fixed thresholds regardless of stop distance.
    off = s.model_copy(update={"reward_risk_ratio": 0.0})
    tp_arm, trailing, _ = trading_engine._reward_levels(off, 8.0)
    assert (tp_arm, trailing) == (3.0, 1.5)


def test_partial_take_profit_sells_a_slice_once_then_holds(db_session, settings):
    """At +partial_r the engine sells partial_take_profit_frac of the position
    (locking a realized win) and lets the rest run -- and it must fire only
    once, not on every subsequent poll."""
    s = settings.model_copy(update={
        "partial_take_profit_enabled": True, "partial_take_profit_frac": 0.5,
        "partial_take_profit_r": 1.0,  # stop=2% (vol unknown) -> partial at +2%
    })
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, s, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 102.5  # +2.5% >= partial_r (2%), below the +3% trailing arm

    portfolio = trading_engine.compute_portfolio(db_session, s, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, s, broker, portfolio)
    assert len(exits) == 1
    assert "Częściowa realizacja" in exits[0].decision.reasoning
    assert exits[0].quantity == pytest.approx(0.5)  # half of the 1 share
    assert broker.balances["SPY"] == pytest.approx(0.5)  # remainder still held

    # Same price next poll -> partial already booked, no second partial sell.
    portfolio = trading_engine.compute_portfolio(db_session, s, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, s, broker, portfolio) == []


def test_extended_partial_take_profit_promotes_to_full_exit_on_one_share(db_session, settings):
    """Poza sesją trades WHOLE shares only. A partial slice of a 1-share
    position (e.g. 50% of 1 share) rounds to 0 shares -- place_extended_limit_
    order would reject it every cycle forever (regression: silently never banks
    the win). The engine must promote it to a FULL exit instead."""
    s = settings.model_copy(update={
        "partial_take_profit_enabled": True, "partial_take_profit_frac": 0.5,
        "partial_take_profit_r": 1.0,
    })
    risk_manager.resume(db_session, "extended")  # extended starts paused -> press START
    broker = FakeAlpaca(prices={"GDX": 40.0}, balances={"USD": 1000.0, "GDX": 0.0})
    trading_engine.execute_manual_trade(
        db_session, s, broker, symbol="GDX", side="BUY", quantity=1.0, venue="extended", whitelist=["GDX"]
    )
    broker.prices["GDX"] = 41.0  # +2.5% >= partial_r (2%), below the +3% trailing arm

    portfolio = trading_engine.compute_portfolio(db_session, s, broker, venue="extended", whitelist=["GDX"])
    exits = trading_engine.check_take_profit_stop_loss(
        db_session, s, broker, portfolio, venue="extended", whitelist=["GDX"], always_open=True,
    )
    assert len(exits) == 1
    assert exits[0].quantity == pytest.approx(1.0)  # promoted to the FULL share, not 0.5
    assert broker.balances["GDX"] == pytest.approx(0.0)  # fully closed
    assert "nie dzieli się na częściową sprzedaż" in exits[0].decision.reasoning


# ============================================================================
# Pakiet 2 -- anty-churn (conviction floor, per-day cap, min hold)
# ============================================================================
def test_low_confidence_buy_is_rejected(db_session, settings):
    s = settings.model_copy(update={"min_buy_confidence": 0.6})
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.5, "Słaba przewaga."))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert decision.executed is False
    assert "Zbyt niska pewność" in (decision.rejection_reason or "")
    assert len(broker.orders) == 0


def test_max_new_positions_per_day_caps_entries(db_session, settings):
    s = settings.model_copy(update={"max_new_positions_per_day": 1})
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Mocny sygnał."))

    first = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert first.executed is True

    second = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert second.executed is False
    assert "Limit nowych wejść" in (second.rejection_reason or "")
    assert len(broker.orders) == 1


def test_min_hold_blocks_non_stop_exit_but_never_the_stop(db_session, settings):
    # Fixed take-profit so the non-stop exit has a clean 'take_profit' kind.
    s = settings.model_copy(update={"min_hold_minutes": 30, "trailing_stop_enabled": False})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, s, broker, symbol="SPY", side="BUY", usdt_amount=100.0)

    # +4% would take-profit, but the position was just opened -> suppressed.
    broker.prices["SPY"] = 104.0
    portfolio = trading_engine.compute_portfolio(db_session, s, broker)
    assert trading_engine.check_take_profit_stop_loss(db_session, s, broker, portfolio) == []

    # The hard stop-loss must still fire regardless of the min-hold window.
    broker.prices["SPY"] = 90.0
    portfolio = trading_engine.compute_portfolio(db_session, s, broker)
    exits = trading_engine.check_take_profit_stop_loss(db_session, s, broker, portfolio)
    assert len(exits) == 1
    assert "Stop-loss" in exits[0].decision.reasoning


# ============================================================================
# Pakiet 3 -- risk-based sizing + market-regime gate
# ============================================================================
def test_risk_based_size_cap_math(settings):
    s = settings.model_copy(update={"risk_per_trade_pct": 1.0})
    pf = {"total_value_usdt": 1000.0, "usdt_balance": 1000.0}
    # Wide 10% stop -> risk $10 -> max position $100 -> 10% of free cash.
    assert trading_engine.risk_based_size_cap(s, pf, 10.0) == 10.0
    # Tight 2% stop -> risk $10 -> max position $500 -> 50% of free cash.
    assert trading_engine.risk_based_size_cap(s, pf, 2.0) == 50.0
    # Disabled -> no cap.
    off = s.model_copy(update={"risk_per_trade_pct": 0.0})
    assert trading_engine.risk_based_size_cap(off, pf, 10.0) == 100.0


def test_compute_market_regime_classifies_risk_off_on_and_neutral(settings):
    below = {"SPY": {"technical": {"sma50_vs_sma200_1h": "below"}}}
    above = {"SPY": {"technical": {"sma50_vs_sma200_1h": "above"}}}
    risk_off = trading_engine.compute_market_regime(below, {"vix_level": 30.0, "sp500_change_pct": -1.5}, settings)
    assert risk_off["regime"] == "risk_off"
    risk_on = trading_engine.compute_market_regime(above, {"vix_level": 14.0, "sp500_change_pct": 1.4}, settings)
    assert risk_on["regime"] == "risk_on"
    neutral = trading_engine.compute_market_regime({}, {}, settings)
    assert neutral["regime"] == "neutral"


def test_regime_gate_blocks_non_defensive_buy_but_allows_defensive(db_session, settings, monkeypatch):
    # The binary gate is a distinct mode from adaptive risk -- disable adaptive
    # here so this test exercises the hard gate it's about.
    s = settings.model_copy(update={
        "regime_gate_enabled": True, "adaptive_risk_enabled": False, "trading_whitelist": "SPY,QQQ,GLD",
    })
    monkeypatch.setattr(
        trading_engine, "compute_market_regime",
        lambda *a, **k: {"regime": "risk_off", "score": -2, "reasons": ["test risk-off"]},
    )
    prices = {"SPY": 100.0, "QQQ": 400.0, "GLD": 200.0}
    balances = {"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0, "GLD": 0.0}

    # Non-defensive name -> rejected while risk-off.
    broker = FakeAlpaca(prices=dict(prices), balances=dict(balances))
    blocked = trading_engine.run_cycle(
        db_session, s, broker, FakeNews(), FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "risk-off SPY")), force=True
    )
    assert blocked.executed is False
    assert "risk-off" in (blocked.rejection_reason or "")

    # Defensive/inverse name (GLD) -> allowed through the gate.
    broker2 = FakeAlpaca(prices=dict(prices), balances=dict(balances))
    allowed = trading_engine.run_cycle(
        db_session, s, broker2, FakeNews(), FakeAdvisor(TradingDecision("BUY", "GLD", 10, 0.9, "złoto broni")), force=True
    )
    assert allowed.executed is True


def test_adaptive_risk_scales_aggression_with_regime(settings):
    """Both brains self-tune: risk-on -> bigger risk + lower confidence bar +
    more entries; risk-off -> smaller risk + higher bar + fewer entries. Exit
    geometry (stops/trailing) is deliberately NOT touched."""
    from app.services import adaptive_risk

    base = settings.model_copy(update={
        "risk_per_trade_pct": 1.0, "min_buy_confidence": 0.57,
        "max_new_positions_per_day": 5, "stop_loss_pct": 4.0,
    })

    risk_on, f_on = adaptive_risk.adaptive_settings(base, {"regime": "risk_on", "score": 2})
    risk_off, f_off = adaptive_risk.adaptive_settings(base, {"regime": "risk_off", "score": -3})
    neutral, f_neu = adaptive_risk.adaptive_settings(base, {"regime": "neutral", "score": 0})

    assert f_on > 1.0 > f_off and f_neu == 1.0
    # Aggressive regime: bigger bets, lower entry bar, more entries.
    assert risk_on.risk_per_trade_pct > base.risk_per_trade_pct
    assert risk_on.min_buy_confidence < base.min_buy_confidence
    assert risk_on.max_new_positions_per_day >= base.max_new_positions_per_day
    # Defensive regime: smaller bets, higher entry bar, fewer entries.
    assert risk_off.risk_per_trade_pct < base.risk_per_trade_pct
    assert risk_off.min_buy_confidence > base.min_buy_confidence
    assert risk_off.max_new_positions_per_day < base.max_new_positions_per_day
    # Exit geometry untouched in every regime.
    assert risk_on.stop_loss_pct == base.stop_loss_pct == risk_off.stop_loss_pct


def test_adaptive_risk_preserves_unlimited_concurrent_positions(settings):
    """0 = 'bez limitu' must survive adaptive scaling in EVERY regime -- the old
    max(1, ...) silently re-imposed a 1-position cap the user had removed."""
    from app.services import adaptive_risk

    base = settings.model_copy(update={"max_concurrent_positions": 0, "max_new_positions_per_day": 0})
    for regime in ({"regime": "risk_on", "score": 3}, {"regime": "risk_off", "score": -3}, {"regime": "neutral", "score": 0}):
        tuned, _ = adaptive_risk.adaptive_settings(base, regime)
        assert tuned.max_concurrent_positions == 0
        assert tuned.max_new_positions_per_day == 0


def test_extended_regime_uses_the_same_equity_read(settings):
    """Both legs trade the SAME US market, so the extended leg reads the SAME
    equity regime (benchmark trend + VIX + S&P move), not a separate one."""
    bench = settings.benchmark_symbol
    down_md = {bench: {"technical": {"sma50_vs_sma200_1h": "below"}}}
    panic = {"vix_level": 45.0, "sp500_change_pct": -4.0}
    # benchmark below (-1) + VIX high (-1) + S&P dumping (-1) => risk_off.
    assert trading_engine.compute_market_regime(down_md, panic, settings, venue="extended")["regime"] == "risk_off"

    up_md = {bench: {"technical": {"sma50_vs_sma200_1h": "above"}}}
    calm_up = {"vix_level": 14.0, "sp500_change_pct": 1.5}
    assert trading_engine.compute_market_regime(up_md, calm_up, settings, venue="extended")["regime"] == "risk_on"


def test_extended_regime_gate_blocks_new_longs_in_risk_off(db_session, settings, monkeypatch):
    """In extended risk-off the gate blocks new extended longs -- a spot-only book
    has no defensive instrument, so cash is the only defensive position."""
    s = settings.model_copy(update={
        "extended_enabled": True, "extended_regime_gate_enabled": True, "adaptive_risk_enabled": False,
        "extended_whitelist": "BTCUSD,ETHUSD", "extended_defensive_symbols": "",
    })
    risk_manager.resume(db_session, "extended")
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.CLOSED)
    )
    monkeypatch.setattr(
        trading_engine, "compute_market_regime",
        lambda *a, **k: {"regime": "risk_off", "score": -2, "reasons": ["BTC trend spadkowy"]},
    )
    prices = {"BTCUSD": 50000.0, "ETHUSD": 3000.0}
    balances = {"USD": 1000.0, "BTCUSD": 0.0, "ETHUSD": 0.0}

    broker = FakeAlpaca(prices=dict(prices), balances=dict(balances))
    blocked = trading_engine.run_cycle(
        db_session, s, broker, FakeNews(), FakeAdvisor(TradingDecision("BUY", "BTCUSD", 10, 0.9, "krypto")),
        force=True, venue="extended", whitelist=["BTCUSD", "ETHUSD"], always_open=True,
    )
    assert blocked.executed is False
    assert "risk-off" in (blocked.rejection_reason or "")


# ============================================================================
# Pakiet 4 -- auto-blacklist after a stop-loss streak
# ============================================================================
def test_auto_blacklist_after_stop_streak_extends_cooldown(db_session, settings):
    import json as _json
    from datetime import datetime as _dt, timezone as _tz

    s = settings.model_copy(update={
        "auto_blacklist_stop_count": 2, "auto_blacklist_window_hours": 24,
        "auto_blacklist_hours": 48, "stop_loss_cooldown_minutes": 60,
    })

    def _stop_once(broker):
        trading_engine.execute_manual_trade(db_session, s, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
        broker.prices["SPY"] = 90.0  # -10% -> stop-loss
        portfolio = trading_engine.compute_portfolio(db_session, s, broker)
        trading_engine.check_take_profit_stop_loss(db_session, s, broker, portfolio)
        broker.prices["SPY"] = 100.0  # reset for the next manual buy

    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 5000.0, "SPY": 0.0, "QQQ": 0.0})

    def _cooldown_minutes_left():
        state = risk_manager.get_state(db_session)
        until = _dt.fromisoformat(_json.loads(state.stop_loss_cooldowns_json)["SPY"])
        return (until - _dt.now(_tz.utc)).total_seconds() / 60

    _stop_once(broker)  # 1st stop -> normal 60-min cooldown
    assert _cooldown_minutes_left() < 120

    _stop_once(broker)  # 2nd stop within window -> quarantine (~48h)
    assert _cooldown_minutes_left() > 60 * 40


# ============================================================================
# Capital allocation between the two engines (one shared Alpaca account)
# ============================================================================
def test_venue_allocation_room_caps_engine_to_its_share(db_session, settings):
    """Each engine may only deploy up to its share of the WHOLE account (shared
    cash + both engines' positions), minus what it already holds."""
    from app.models import PortfolioSnapshot

    s = settings.model_copy(update={"alpaca_allocation_pct": 50.0, "extended_allocation_pct": 50.0})
    # The OTHER (equities) engine holds $50 of positions on top of $100 shared cash.
    db_session.add(PortfolioSnapshot(total_value_usdt=150.0, usdt_balance=100.0, venue="alpaca"))
    db_session.commit()

    # Extended engine currently holds nothing (its snapshot: cash 100, total 100).
    extended_portfolio = {"usdt_balance": 100.0, "total_value_usdt": 100.0}
    # account = 100 cash + 0 extended + 50 equity = 150; extended target = 75; room = 75.
    room = trading_engine.venue_allocation_room(db_session, s, extended_portfolio, "extended")
    assert room == pytest.approx(75.0)

    # If extended already holds $80 (total 180), it's OVER its 50% target -> less room.
    extended_full = {"usdt_balance": 100.0, "total_value_usdt": 180.0}
    # account = 100 + 80 + 50 = 230; target = 115; room = min(100, 115-80) = 35.
    room2 = trading_engine.venue_allocation_room(db_session, s, extended_full, "extended")
    assert room2 == pytest.approx(35.0)


def test_compute_and_cache_regime_refreshes_without_trading(db_session, settings):
    """The market read must be cacheable independently of a trading cycle (so
    the dashboard stays current while stopped/closed) -- and it must never place
    an order while doing so."""
    from app.services import risk_manager

    class FakeMC:
        def get_market_context(self):
            return {}

    broker = FakeAlpaca(prices={"SPY": 500.0}, balances={"USD": 1000.0})
    regime = trading_engine.compute_and_cache_regime(
        db_session, settings, broker, FakeMC(), venue="alpaca", whitelist=["SPY"]
    )

    assert "regime" in regime
    state = risk_manager.get_state(db_session)
    assert json.loads(state.market_regime_json)["regime"] == regime["regime"]
    assert broker.orders == []  # read-only: no order ever placed


def test_account_total_value_combines_both_venues(db_session, settings):
    from app.models import PortfolioSnapshot

    db_session.add(PortfolioSnapshot(total_value_usdt=150.0, usdt_balance=100.0, venue="alpaca"))
    db_session.commit()

    extended_portfolio = {"usdt_balance": 100.0, "total_value_usdt": 180.0}
    # cash 100 + extended positions 80 + equity positions 50 = 230.
    assert trading_engine.account_total_value(db_session, extended_portfolio, "extended") == pytest.approx(230.0)


def test_account_total_value_ignores_missing_other_venue(db_session, settings):
    extended_portfolio = {"usdt_balance": 100.0, "total_value_usdt": 180.0}
    # No alpaca snapshot exists yet -> falls back to just this venue's total.
    assert trading_engine.account_total_value(db_session, extended_portfolio, "extended") == pytest.approx(180.0)


def test_extended_only_drawdown_trips_account_wide_halt(db_session, settings):
    """The max-drawdown/day-loss halt must see the WHOLE account, not just
    whichever venue happens to poll -- a severe extended-only drawdown has to
    trip the same account-wide halt an equities drawdown would, since is_halted
    blocks BOTH engines."""
    from app.services import risk_manager

    lenient = settings.model_copy(update={
        "extended_enabled": True, "extended_whitelist": "BTCUSD",
        "daily_loss_limit_pct": 10.0, "weekly_loss_limit_pct": 90.0, "max_drawdown_halt_pct": 90.0,
    })

    # Equities side: healthy, $500 total, unchanged all day.
    equities_broker = FakeAlpaca(prices={"SPY": 100.0}, balances={"USD": 500.0})
    trading_engine.run_cycle(
        db_session, lenient.model_copy(update={"trading_whitelist": "SPY"}), equities_broker,
        FakeNews(), FakeAdvisor(TradingDecision("HOLD", None, 0, 0.5, "hold")), force=True,
    )
    assert risk_manager.get_state(db_session).is_halted is False

    # Extended side crashes hard (-40%) on its own -- must trip the account-wide
    # halt even though the equities side never moved.
    extended_broker = FakeAlpaca(prices={"BTCUSD": 30000.0}, balances={"USD": 300.0})
    trading_engine.run_cycle(
        db_session, lenient, extended_broker, FakeNews(),
        FakeAdvisor(TradingDecision("HOLD", None, 0, 0.5, "hold")),
        force=True, venue="extended", whitelist=["BTCUSD"], always_open=True,
    )

    assert risk_manager.get_state(db_session).is_halted is True


def test_budget_hard_stop_skips_cycle_without_calling_claude(db_session, settings):
    """Once the month's estimated Claude spend hits the budget, a scheduled
    cycle must NOT call Claude (lean-AI safety) -- it records a HOLD explaining
    the budget is spent."""
    from app.services import budget_tracker

    s = settings.model_copy(update={"claude_pause_trading_at_budget": True, "claude_monthly_budget_usd": 1.0})
    budget_tracker.record_usage_cost(db_session, 2.0, 100, 50)  # over the $1 budget

    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "x"))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=False)

    assert decision is not None
    assert advisor.last_kwargs is None  # Claude never called
    assert "Budżet Claude wyczerpany" in (decision.rejection_reason or "")


def test_force_run_ignores_budget_stop(db_session, settings):
    """A manual "Wymuś analizę" (force) still runs even over budget -- the user
    explicitly accepts the cost."""
    from app.services import budget_tracker

    s = settings.model_copy(update={"claude_pause_trading_at_budget": True, "claude_monthly_budget_usd": 1.0})
    budget_tracker.record_usage_cost(db_session, 2.0, 100, 50)

    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "x"))
    trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)

    assert advisor.last_kwargs is not None  # Claude WAS called on a forced run


# ============================================================================
# Tier 1/2 -- entry filter, concurrency cap, auto-demote, spread haircut, stats
# ============================================================================
def test_entry_filter_blocks_buy_without_confluence(db_session, settings):
    # FakeAlpaca returns 1 bar -> indicators are None -> confluence score 0.
    s = settings.model_copy(update={"entry_filter_enabled": True, "entry_min_score": 2})
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Chcę wejść."))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert decision.executed is False
    assert "konfluencji" in (decision.rejection_reason or "")
    assert len(broker.orders) == 0


def test_entry_filter_allows_buy_with_confluence(db_session, settings, monkeypatch):
    s = settings.model_copy(update={"entry_filter_enabled": True})
    monkeypatch.setattr(
        trading_engine.signals, "entry_confluence",
        lambda settings, tech: trading_engine.signals.EntrySignal(True, 3, ["ok"]),
    )
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Silny sygnał."))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert decision.executed is True


def test_concurrency_cap_blocks_new_uncorrelated_entry(db_session, settings):
    s = settings.model_copy(update={"max_concurrent_positions": 1})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    # One position already open (QQQ) -> the cap is reached.
    trading_engine.execute_manual_trade(db_session, s, broker, symbol="QQQ", side="BUY", usdt_amount=200.0)
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Druga pozycja."))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert decision.executed is False
    assert "równoczesnych pozycji" in (decision.rejection_reason or "")


def test_auto_demote_blocks_chronically_losing_symbol(db_session, settings):
    s = settings.model_copy(update={"auto_demote_enabled": True, "auto_demote_min_trades": 2})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 5000.0, "SPY": 0.0, "QQQ": 0.0})
    # Two closed LOSING round trips on SPY -> negative track record.
    for _ in range(2):
        broker.prices["SPY"] = 100.0
        trading_engine.execute_manual_trade(db_session, s, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
        broker.prices["SPY"] = 95.0
        trading_engine.execute_manual_trade(db_session, s, broker, symbol="SPY", side="SELL", quantity=1.0)

    stats = trading_engine.compute_symbol_stats(db_session, venue="alpaca")
    assert stats["SPY"]["closed"] == 2 and stats["SPY"]["realized_pnl"] < 0

    broker.prices["SPY"] = 100.0
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Może tym razem."))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert decision.executed is False
    assert "Auto-degradacja" in (decision.rejection_reason or "")


def test_high_spread_symbol_gets_size_haircut(db_session, settings):
    s = settings.model_copy(update={"high_spread_symbols": "SPY", "high_spread_size_scale": 0.5})
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 20, 0.9, "Szerokospreadowy."))
    decision = trading_engine.run_cycle(db_session, s, broker, FakeNews(), advisor, force=True)
    assert decision.executed is True
    assert decision.size_pct == 10.0  # 20% haircut by 0.5


def test_describe_position_plan_holds_below_targets(settings):
    """A small gain below the partial/trailing-arm thresholds reads as HOLD with
    an explanation -- this is exactly the '+3% nie sprzedany' case."""
    s = settings.model_copy(update={
        "stop_loss_pct": 2.0, "reward_risk_ratio": 2.0, "partial_take_profit_r": 2.0,
        "trailing_stop_enabled": True, "partial_take_profit_enabled": True,
    })
    # basis 100, price 103 (+3%). partial_at = 2*2 = 4%, tp_arm = 2*2 = 4%. +3% < both.
    plan = trading_engine.describe_position_plan(s, basis=100.0, price=103.0, peak=103.0)
    assert plan["action"] == "hold"
    assert plan["change_pct"] == 3.0
    assert "Trzymam" in plan["note"]


def test_describe_position_plan_adopted_has_no_basis(settings):
    plan = trading_engine.describe_position_plan(settings, basis=None, price=50.0, peak=52.0)
    assert plan["adopted"] is True and plan["change_pct"] is None
    assert "Adoptowana" in plan["note"]


def test_describe_position_plan_trailing_protected_when_armed(settings):
    s = settings.model_copy(update={
        "stop_loss_pct": 2.0, "reward_risk_ratio": 2.0, "trailing_stop_enabled": True,
    })
    # peak 110 vs basis 100 => +10% >= tp_arm(4%) => trailing armed.
    plan = trading_engine.describe_position_plan(s, basis=100.0, price=108.0, peak=110.0)
    assert plan["action"] == "trailing_protected"
    assert "trailingiem" in plan["note"]


def test_compute_portfolio_split_uses_live_db_whitelist(db_session, settings):
    """The venue split must follow the LIVE (DB) extended whitelist, not the
    config seed -- otherwise a name the Friday review added would be attributed
    to the wrong leg and the regular leg would force-close it."""
    from app.services import whitelist_review

    # SMH is NOT in the config seed; put it on the live DB whitelist.
    whitelist_review.set_extended_whitelist(db_session, ["SMH"])
    broker = FakeAlpaca(prices={"SMH": 30.0, "SPY": 500.0}, balances={"USD": 100.0, "SMH": 2.0, "SPY": 1.0})

    ext = trading_engine.compute_portfolio(db_session, settings, broker, venue="extended", whitelist=["SMH"])
    reg = trading_engine.compute_portfolio(db_session, settings, broker, venue="alpaca", whitelist=settings.whitelist_symbols)

    assert ext["balances"].get("SMH") == 2.0            # extended leg owns SMH
    assert "SMH" not in reg["balances"]                 # regular leg must NOT see it
    assert reg["balances"].get("SPY") == 1.0            # SPY stays with the regular leg


def test_hard_take_profit_floor_banks_strong_gain_even_with_trailing(settings):
    """A big gain is taken outright even with trailing enabled, so it can't
    fully round-trip while the trailing waits to arm ('+X% a nie sprzedany')."""
    s = settings.model_copy(update={"hard_take_profit_pct": 8.0, "trailing_stop_enabled": True})
    # +9% from entry, price == peak (trailing not triggered) -> hard floor fires.
    reason, pct, kind = trading_engine._decide_mechanical_exit(s, "SPY", 100.0, 109.0, 109.0)
    assert kind == "take_profit" and pct == 100.0
    assert "sufit" in reason

    # +5% (below the ceiling) -> the floor does NOT fire.
    reason2, _pct2, kind2 = trading_engine._decide_mechanical_exit(s, "SPY", 100.0, 105.0, 105.0)
    assert kind2 != "take_profit"
