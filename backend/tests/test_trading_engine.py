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
        pre_market_start=now,
        regular_open=now,
        regular_close=now,
        after_hours_end=now,
    )


@pytest.fixture(autouse=True)
def _default_regular_session(monkeypatch):
    """Most tests don't care about market-hours gating -- default every test
    to the regular session so run_cycle/check_take_profit_stop_loss behave as
    if the market is simply open, unless a test overrides this explicitly."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.REGULAR)
    )


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

    def place_order_for_session(self, symbol, side, *, session, usdt_amount=None, quantity=None):
        # The real extended-hours whole-share/limit-price mechanics are unit
        # tested directly against AlpacaClient in test_alpaca_client.py --
        # here we just record which session a trade was routed through.
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


def test_tpsl_does_not_fire_during_extended_hours_when_disabled(db_session, settings):
    disabled = settings.model_copy(update={"extended_hours_trading_enabled": False})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, disabled, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # would take-profit if tradable

    portfolio = trading_engine.compute_portfolio(db_session, disabled, broker)
    pre_market = _session_info(market_hours.PRE_MARKET)
    assert trading_engine.check_take_profit_stop_loss(db_session, disabled, broker, portfolio, pre_market) == []


def test_tpsl_fires_during_extended_hours_when_enabled(db_session, settings):
    fixed = settings.model_copy(update={"trailing_stop_enabled": False})
    broker = FakeAlpaca(prices={"SPY": 100.0, "QQQ": 400.0}, balances={"USD": 1000.0, "SPY": 0.0, "QQQ": 0.0})
    trading_engine.execute_manual_trade(db_session, fixed, broker, symbol="SPY", side="BUY", usdt_amount=100.0)
    broker.prices["SPY"] = 104.0  # +4% > take_profit_pct (3) -> immediate sell, fixed take-profit

    portfolio = trading_engine.compute_portfolio(db_session, fixed, broker)
    after_hours = _session_info(market_hours.AFTER_HOURS)
    exits = trading_engine.check_take_profit_stop_loss(db_session, fixed, broker, portfolio, after_hours)

    assert len(exits) == 1
    assert broker.last_order_session == market_hours.AFTER_HOURS


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
    """Stocks/ETFs aren't 24/7 like crypto -- a scheduled poll outside market
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


def test_scheduled_cycle_runs_during_pre_market_when_extended_hours_enabled(db_session, settings, monkeypatch):
    """The whole point of extended-hours support: a scheduled cycle during
    pre-market must actually execute (via a session-routed order), not just
    passively let Claude look without acting."""
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.PRE_MARKET)
    )
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Silny sygnał przedsesyjny."))

    decision = trading_engine.run_cycle(db_session, settings, broker, FakeNews(), advisor, force=True)

    assert decision.executed is True
    assert len(broker.orders) == 1
    assert broker.last_order_session == market_hours.PRE_MARKET


def test_scheduled_cycle_skipped_during_after_hours_when_extended_disabled(db_session, settings, monkeypatch):
    disabled = settings.model_copy(update={"extended_hours_trading_enabled": False})
    monkeypatch.setattr(
        trading_engine.market_hours, "get_session_info", lambda broker: _session_info(market_hours.AFTER_HOURS)
    )
    broker = FakeAlpaca()
    advisor = FakeAdvisor(TradingDecision("BUY", "SPY", 10, 0.9, "Nie powinno zostać wywołane."))

    decision = trading_engine.run_cycle(db_session, disabled, broker, FakeNews(), advisor)

    assert decision is None
    assert advisor.calls == 0
    assert len(broker.orders) == 0


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
