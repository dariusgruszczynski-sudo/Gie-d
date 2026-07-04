from dataclasses import dataclass, field

from app.services import risk_manager, trading_engine
from app.services.claude_advisor import TradingDecision


class FakeBinance:
    def __init__(self, prices=None, balances=None):
        self.prices = prices or {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0}
        self.balances = balances or {"USDT": 1000.0, "BTC": 0.0, "ETH": 0.0}
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
        base = symbol.replace("USDT", "")
        if side.upper() == "BUY":
            self.balances["USDT"] -= usdt_amount
            self.balances[base] = self.balances.get(base, 0.0) + quantity
        else:
            self.balances["USDT"] += usdt_amount
            self.balances[base] = self.balances.get(base, 0.0) - quantity
        order = _FakeOrder(str(len(self.orders) + 1), symbol, side.upper(), quantity, price, usdt_amount)
        self.orders.append(order)
        return order

    def place_market_order_quantity(self, symbol, side, raw_quantity):
        price = self.prices[symbol]
        usdt_value = raw_quantity * price
        base = symbol.replace("USDT", "")
        if side.upper() == "BUY":
            self.balances["USDT"] -= usdt_value
            self.balances[base] = self.balances.get(base, 0.0) + raw_quantity
        else:
            self.balances["USDT"] += usdt_value
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

    def decide(self, **kwargs):
        self.calls += 1
        return self.decision


def test_hold_decision_creates_no_trade(db_session, settings):
    binance = FakeBinance()
    advisor = FakeAdvisor(TradingDecision("HOLD", None, 0, 0.8, "Rynek stabilny, czekamy."))

    decision = trading_engine.run_cycle(db_session, settings, binance, FakeNews(), advisor)

    assert decision is not None
    assert decision.action.value == "HOLD"
    assert decision.executed is False
    assert len(binance.orders) == 0


def test_buy_decision_executes_trade(db_session, settings):
    binance = FakeBinance()
    advisor = FakeAdvisor(TradingDecision("BUY", "BTCUSDT", 10, 0.9, "Silny sygnał wzrostowy."))

    decision = trading_engine.run_cycle(db_session, settings, binance, FakeNews(), advisor)

    assert decision.executed is True
    assert len(binance.orders) == 1
    assert binance.orders[0].symbol == "BTCUSDT"
    assert binance.orders[0].side == "BUY"
    # 10% of 1000 USDT starting balance
    assert abs(binance.orders[0].usdt_value - 100.0) < 1e-6


def test_oversized_position_rejected_without_trade(db_session, settings):
    binance = FakeBinance()
    advisor = FakeAdvisor(TradingDecision("BUY", "BTCUSDT", 90, 0.9, "Va banque."))

    decision = trading_engine.run_cycle(db_session, settings, binance, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert decision.executed is False
    assert len(binance.orders) == 0


def test_automated_trade_blocked_while_halted(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)  # trips 10% daily limit
    state = risk_manager.get_state(db_session)
    assert state.is_halted is True

    binance = FakeBinance()
    advisor = FakeAdvisor(TradingDecision("BUY", "BTCUSDT", 10, 0.9, "Kupujemy dołek."))

    decision = trading_engine.run_cycle(db_session, settings, binance, FakeNews(), advisor)

    assert decision.rejection_reason is not None
    assert len(binance.orders) == 0


def test_manual_trade_executes_even_when_halted(db_session, settings):
    risk_manager.update_portfolio_value(db_session, settings, 1000.0)
    risk_manager.update_portfolio_value(db_session, settings, 850.0)
    assert risk_manager.get_state(db_session).is_halted is True

    binance = FakeBinance()
    trade = trading_engine.execute_manual_trade(
        db_session, settings, binance, symbol="BTCUSDT", side="BUY", usdt_amount=100.0
    )

    assert trade.is_manual is True
    assert len(binance.orders) == 1
