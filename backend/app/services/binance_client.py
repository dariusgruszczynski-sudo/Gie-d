"""Thin wrapper around python-binance so the rest of the app never touches
the raw SDK directly. Supports a testnet/live switch driven by config."""

from dataclasses import dataclass

from binance.client import Client

from app.config import Settings


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float


class BinanceClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = Client(
            settings.binance_api_key,
            settings.binance_api_secret,
            testnet=settings.binance_testnet,
        )

    @property
    def mode(self) -> str:
        return "testnet" if self._settings.binance_testnet else "live"

    def get_price(self, symbol: str) -> float:
        ticker = self._client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[list]:
        """Returns raw kline rows: [open_time, open, high, low, close, volume, ...]."""
        return self._client.get_klines(symbol=symbol, interval=interval, limit=limit)

    def get_account_balances(self) -> dict[str, float]:
        """Returns {asset: free_balance} for non-zero balances."""
        account = self._client.get_account()
        balances = {}
        for b in account["balances"]:
            free = float(b["free"])
            if free > 0:
                balances[b["asset"]] = free
        return balances

    def get_symbol_info(self, symbol: str) -> dict:
        return self._client.get_symbol_info(symbol)

    def _round_step_size(self, quantity: float, symbol: str) -> float:
        info = self.get_symbol_info(symbol)
        step_size = 1.0
        for f in info.get("filters", []):
            if f.get("filterType") == "LOT_SIZE":
                step_size = float(f["stepSize"])
                break
        precision = max(0, str(step_size)[::-1].find(".")) if step_size < 1 else 0
        return float(f"{quantity:.{precision}f}")

    def place_market_order_usdt_amount(self, symbol: str, side: str, usdt_amount: float) -> OrderResult:
        """Place a market order sized by a USDT notional amount (buys/sells the
        equivalent quantity of the base asset at current market price)."""
        price = self.get_price(symbol)
        raw_quantity = usdt_amount / price
        return self.place_market_order_quantity(symbol, side, raw_quantity)

    def place_market_order_quantity(self, symbol: str, side: str, raw_quantity: float) -> OrderResult:
        """Place a market order for an exact (pre-rounding) base-asset quantity."""
        price = self.get_price(symbol)
        quantity = self._round_step_size(raw_quantity, symbol)
        if quantity <= 0:
            raise ValueError(f"Computed quantity for {symbol} rounds to 0, amount too small")

        order = self._client.create_order(
            symbol=symbol,
            side=side.upper(),
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity,
        )
        fills = order.get("fills", [])
        if fills:
            avg_price = sum(float(f["price"]) * float(f["qty"]) for f in fills) / sum(
                float(f["qty"]) for f in fills
            )
        else:
            avg_price = price
        executed_qty = float(order.get("executedQty", quantity))
        return OrderResult(
            order_id=str(order.get("orderId", "")),
            symbol=symbol,
            side=side.upper(),
            quantity=executed_qty,
            price=avg_price,
            usdt_value=executed_qty * avg_price,
        )
