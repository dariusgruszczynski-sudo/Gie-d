import json
from dataclasses import dataclass, field

import pytest

from app.services import risk_manager, trading_engine
from app.services.claude_advisor import TradingDecision


class FakeKraken:
    def __init__(self, prices=None, balances=None):
        self.prices = prices or {"XBTEUR": 50000.0, "ETHEUR": 3000.0}
        self.balances = balances or {"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0}
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
        base = symbol.replace("EUR", "")
        if side.upper() == "BUY":
            self.balances["EUR"] -= usdt_amount
            self.balances[base] = self.balances.get(base, 0.0) + quantity
        else:
            self.balances["EUR"] += usdt_amount
            self.balances[base] = self.balances.get(base, 0.0) - quantity
        order = _FakeOrder(str(len(self.orders) + 1), symbol, side.upper(), quantity, price, usdt_amount)
        self.orders.append(order)
        return order

    def place_market_order_quantity(self, symbol, side, raw_quantity):
        price = self.prices[symbol]
        usdt_value = raw_quantity * price
        base = symbol.replace("EUR", "")
        if side.upper() == "BUY":
            self.balances["EUR"] -= usdt_value
            self.balances[base] = self.balances.get(base, 0.0) + raw_quantity
        else:
            self.balances["EUR"] += usdt_value
            self.balances[base] = self.balances.get(base, 0.0) - raw_quantity
        order = _FakeOrder(str(len(self.orders) + 1), symbol, side.upper(), raw_quantity, price, usdt_value)
        self.orders.append(order)
        return order


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
    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor)

    assert decision is not None
    assert decision.action.value == "HOLD"
    assert decision.executed is False
    assert len(kraken.orders) == 0


def test_buy_decision_executes_trade(db_session, settings):
    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("BUY", "XBTEUR", 10, 0.9, "Silny sygnał wzrostowy."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor)

    assert decision.executed is True
    assert len(kraken.orders) == 1
    assert kraken.orders[0].symbol == "XBTEUR"
    assert kraken.orders[0].side == "BUY"
    # 10% of 1000 EUR starting balance
    assert abs(kraken.orders[0].usdt_value - 100.0) < 1e-6


def test_oversized_position_rejected_without_trade(db_session, settings):
    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("BUY", "XBTEUR", 90, 0.9, "Va banque."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert decision.executed is False
    assert len(kraken.orders) == 0


def test_automated_trade_blocked_while_halted(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)  # trips 10% daily limit
    state = risk_manager.get_state(db_session)
    assert state.is_halted is True

    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("BUY", "XBTEUR", 10, 0.9, "Kupujemy dołek."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert len(kraken.orders) == 0


def test_halted_scheduled_cycle_does_not_call_opus(db_session, settings):
    """Budget guard: when trading is halted, a scheduled cycle must NOT spend a
    Claude API call on a decision that could only ever be rejected."""
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)  # trips halt
    assert risk_manager.get_state(db_session).is_halted is True

    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("BUY", "XBTEUR", 10, 0.9, "Nie powinno zostać wywołane."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor)

    assert advisor.calls == 0  # Claude never asked
    assert decision.rejection_reason is not None
    assert decision.action.value == "HOLD"
    assert len(kraken.orders) == 0


def test_force_analysis_runs_opus_even_without_a_trigger(db_session, settings):
    """The 'Wymuś analizę' button (force=True) must always ask Claude, even when
    the daily analysis already ran and no price moved past the threshold --
    otherwise clicking it does nothing (the reported bug)."""
    risk_manager.get_state(db_session)
    # Mark today's analysis as already done so the scheduled trigger would NOT fire.
    trading_engine._mark_analysis_done_today(db_session)
    kraken = FakeKraken()
    # Seed last-check prices so no price-move trigger either.
    trading_engine.check_trigger(db_session, settings, {"XBTEUR": 50000.0, "ETHEUR": 3000.0})

    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.7, "Wymuszona analiza."))

    # Without force: nothing happens.
    assert trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor) is None
    assert advisor.calls == 0

    # With force: Claude is asked and a decision is produced.
    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor, force=True)
    assert decision is not None
    assert advisor.calls == 1
    assert decision.triggered_by.value == "manual"


def test_manual_trade_executes_even_when_halted(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)
    assert risk_manager.get_state(db_session).is_halted is True

    kraken = FakeKraken()
    trade = trading_engine.execute_manual_trade(
        db_session, settings, kraken, symbol="XBTEUR", side="BUY", usdt_amount=100.0
    )

    assert trade.is_manual is True
    assert len(kraken.orders) == 1


def test_manual_trade_rejects_symbol_outside_whitelist(db_session, settings):
    kraken = FakeKraken()

    with pytest.raises(ValueError, match="whiteli"):
        trading_engine.execute_manual_trade(
            db_session, settings, kraken, symbol="DOGEEUR", side="BUY", usdt_amount=100.0
        )
    assert len(kraken.orders) == 0


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
    kraken = FakeKraken()

    class PausingAdvisor:
        def decide(self, **kwargs):
            risk_manager.pause(db_session)
            return TradingDecision("BUY", "XBTEUR", 10, 0.9, "Silny sygnał.")

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), PausingAdvisor())

    assert decision.executed is False
    assert decision.rejection_reason is not None
    assert len(kraken.orders) == 0


def test_whitelist_supports_more_than_two_coins(db_session, settings):
    """Verifies the whitelist is fully generic -- SOL/XRP work the same way
    as BTC/ETH with no per-coin code changes required."""
    four_coin_settings = settings.model_copy(update={"trading_whitelist": "XBTEUR,ETHEUR,SOLEUR,XRPEUR"})
    kraken = FakeKraken(
        prices={"XBTEUR": 50000.0, "ETHEUR": 3000.0, "SOLEUR": 150.0, "XRPEUR": 0.5},
        balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0, "SOL": 0.0, "XRP": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("BUY", "SOLEUR", 10, 0.85, "SOL wygląda mocno."))

    decision = trading_engine.run_cycle(db_session, four_coin_settings, kraken, FakeNews(), advisor)

    assert decision.executed is True
    assert len(kraken.orders) == 1
    assert kraken.orders[0].symbol == "SOLEUR"
    # 10% of 1000 EUR starting balance
    assert abs(kraken.orders[0].usdt_value - 100.0) < 1e-6


def test_symbol_unavailable_on_kraken_does_not_abort_whole_cycle(db_session, settings):
    """Simulates SOLEUR failing to price (network hiccup, delisted pair, ...)
    -- the cycle must still succeed for the other coins instead of the whole
    analysis silently failing every time (which is exactly what happened
    before this fix: one bad symbol killed compute_portfolio, which killed
    the entire cycle, forever, for every coin)."""
    four_coin_settings = settings.model_copy(update={"trading_whitelist": "XBTEUR,ETHEUR,SOLEUR,XRPEUR"})
    kraken = FakeKraken(
        prices={"XBTEUR": 50000.0, "ETHEUR": 3000.0, "XRPEUR": 0.5},  # SOLEUR missing on purpose
        balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0, "SOL": 0.0, "XRP": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("BUY", "XBTEUR", 10, 0.9, "BTC wygląda mocno."))

    decision = trading_engine.run_cycle(db_session, four_coin_settings, kraken, FakeNews(), advisor)

    assert decision.executed is True
    assert len(kraken.orders) == 1
    assert kraken.orders[0].symbol == "XBTEUR"
    assert "SOLEUR" not in advisor.last_kwargs["whitelist"]
    assert set(advisor.last_kwargs["market_data"].keys()) == {"XBTEUR", "ETHEUR", "XRPEUR"}


def test_compute_portfolio_records_failed_symbols(db_session, settings):
    """The dashboard needs to tell 'Kraken genuinely doesn't have this pair'
    apart from 'no data yet' -- so a symbol that fails to price must be
    recorded on the snapshot, not just silently dropped."""
    from app.models import PortfolioSnapshot

    four_coin_settings = settings.model_copy(update={"trading_whitelist": "XBTEUR,ETHEUR,SOLEUR,XRPEUR"})
    kraken = FakeKraken(
        prices={"XBTEUR": 50000.0, "ETHEUR": 3000.0, "XRPEUR": 0.5},  # SOLEUR missing on purpose
        balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0, "SOL": 0.0, "XRP": 0.0},
    )

    portfolio = trading_engine.compute_portfolio(db_session, four_coin_settings, kraken)

    assert portfolio["failed_symbols"] == ["SOLEUR"]
    snapshot = db_session.query(PortfolioSnapshot).order_by(PortfolioSnapshot.id.desc()).first()
    assert json.loads(snapshot.failed_symbols_json) == ["SOLEUR"]


def test_whitelist_rejects_symbol_not_in_four_coin_list(db_session, settings):
    four_coin_settings = settings.model_copy(update={"trading_whitelist": "XBTEUR,ETHEUR,SOLEUR,XRPEUR"})
    kraken = FakeKraken(
        prices={"XBTEUR": 50000.0, "ETHEUR": 3000.0, "SOLEUR": 150.0, "XRPEUR": 0.5},
        balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0, "SOL": 0.0, "XRP": 0.0},
    )
    advisor = FakeAdvisor(TradingDecision("BUY", "DOGEEUR", 10, 0.85, "Poza whitelistą."))

    decision = trading_engine.run_cycle(db_session, four_coin_settings, kraken, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert len(kraken.orders) == 0


def test_failed_analysis_does_not_burn_the_daily_trigger(db_session, settings):
    kraken = FakeKraken()

    class FailingAdvisor:
        def decide(self, **kwargs):
            raise RuntimeError("Anthropic API down")

    with pytest.raises(RuntimeError):
        trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), FailingAdvisor())

    # last_full_analysis_date must NOT have been marked -- the next cycle
    # (e.g. after Claude recovers) should still be able to trigger today.
    state = risk_manager.get_state(db_session)
    assert state.last_full_analysis_date == ""


def test_market_context_reaches_advisor_and_gets_logged(db_session, settings):
    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor, FakeMarketContext())

    assert advisor.last_kwargs["market_context"] == {
        "fear_greed_index": 62,
        "btc_dominance_pct": 54.1,
        "global_market_cap_change_24h_pct": 1.8,
    }
    assert json.loads(decision.market_context_snapshot)["fear_greed_index"] == 62


def test_average_cost_basis_tracks_buys_and_sells(db_session, settings):
    kraken = FakeKraken(prices={"XBTEUR": 100.0, "ETHEUR": 3000.0}, balances={"EUR": 10000.0, "XBT": 0.0, "ETH": 0.0})
    # Buy 1 XBT @100, then 1 XBT @300 -> avg 200 over qty 2.
    kraken.prices["XBTEUR"] = 100.0
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="BUY", quantity=1.0)
    kraken.prices["XBTEUR"] = 300.0
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="BUY", quantity=1.0)

    assert abs(trading_engine.average_cost_basis(db_session, "XBTEUR") - 200.0) < 1e-6

    # Sell 1 -> still 1 held at the same average 200.
    kraken.prices["XBTEUR"] = 250.0
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="SELL", quantity=1.0)
    assert abs(trading_engine.average_cost_basis(db_session, "XBTEUR") - 200.0) < 1e-6


def test_average_cost_basis_none_when_flat(db_session, settings):
    assert trading_engine.average_cost_basis(db_session, "XBTEUR") is None


def test_take_profit_auto_sells_when_price_rises(db_session, settings):
    kraken = FakeKraken(prices={"XBTEUR": 100.0, "ETHEUR": 3000.0}, balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="BUY", usdt_amount=100.0)
    kraken.prices["XBTEUR"] = 104.0  # +4% > take_profit_pct (3)

    portfolio = trading_engine.compute_portfolio(db_session, settings, kraken)
    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, kraken, portfolio)

    assert len(exits) == 1
    assert exits[0].side == "SELL"
    assert "Take-profit" in exits[0].decision.reasoning


def test_stop_loss_auto_sells_when_price_drops(db_session, settings):
    kraken = FakeKraken(prices={"XBTEUR": 100.0, "ETHEUR": 3000.0}, balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="BUY", usdt_amount=100.0)
    kraken.prices["XBTEUR"] = 97.0  # -3% < -stop_loss_pct (2)

    portfolio = trading_engine.compute_portfolio(db_session, settings, kraken)
    exits = trading_engine.check_take_profit_stop_loss(db_session, settings, kraken, portfolio)

    assert len(exits) == 1
    assert exits[0].side == "SELL"
    assert "Stop-loss" in exits[0].decision.reasoning


def test_no_exit_within_thresholds(db_session, settings):
    kraken = FakeKraken(prices={"XBTEUR": 100.0, "ETHEUR": 3000.0}, balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="BUY", usdt_amount=100.0)
    kraken.prices["XBTEUR"] = 101.5  # +1.5%, between -2% and +3%

    portfolio = trading_engine.compute_portfolio(db_session, settings, kraken)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, kraken, portfolio) == []


def test_tpsl_does_not_fire_while_stopped(db_session, settings):
    kraken = FakeKraken(prices={"XBTEUR": 100.0, "ETHEUR": 3000.0}, balances={"EUR": 1000.0, "XBT": 0.0, "ETH": 0.0})
    trading_engine.execute_manual_trade(db_session, settings, kraken, symbol="XBTEUR", side="BUY", usdt_amount=100.0)
    kraken.prices["XBTEUR"] = 104.0  # would take-profit
    risk_manager.pause(db_session)  # user pressed STOP

    portfolio = trading_engine.compute_portfolio(db_session, settings, kraken)
    assert trading_engine.check_take_profit_stop_loss(db_session, settings, kraken, portfolio) == []


def test_run_cycle_without_market_ctx_does_not_crash(db_session, settings):
    """market_ctx is optional so existing callers/tests that omit it keep
    working, and the trading engine never hard-depends on this data source."""
    kraken = FakeKraken()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, kraken, FakeNews(), advisor)

    assert decision is not None
    assert advisor.last_kwargs["market_context"] == {}
