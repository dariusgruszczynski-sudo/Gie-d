"""Thin wrapper around Alpaca's Trading + Market Data REST APIs.

Unlike Kraken, Alpaca offers a real paper-trading environment with the exact
same API surface as live -- flip ALPACA_PAPER=true anytime to rehearse safely
on Alpaca's simulated $100k account; the rest of the app never needs to know
which one it's talking to, only the base URL + which key pair changes.

Authentication is a pair of plain headers (no HMAC signing needed, unlike
Kraken), which makes this considerably simpler and less error-prone."""

import logging
import time
from dataclasses import dataclass

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

TRADING_LIVE_URL = "https://api.alpaca.markets"
TRADING_PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
# Free-tier market data only includes the IEX feed, not the full-market SIP
# feed -- requesting it explicitly avoids a subscription error on free accounts.
DATA_FEED = "iex"
# Market orders fill almost immediately during regular hours, but the AddOrder
# response doesn't carry the fill synchronously -- poll briefly for it.
FILL_POLL_ATTEMPTS = 10
FILL_POLL_DELAY_SECONDS = 0.5
_TIMEFRAMES = {"1m": "1Min", "5m": "5Min", "15m": "15Min", "1h": "1Hour", "1d": "1Day"}


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float  # quote-currency (USD) notional value of the fill


class AlpacaAPIError(RuntimeError):
    pass


class AlpacaClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": settings.alpaca_api_secret,
        }
        trading_base = TRADING_PAPER_URL if settings.alpaca_paper else TRADING_LIVE_URL
        self._trading = httpx.Client(base_url=trading_base, headers=headers, timeout=15.0)
        self._data = httpx.Client(base_url=DATA_URL, headers=headers, timeout=15.0)

    @property
    def mode(self) -> str:
        return "paper" if self._settings.alpaca_paper else "live"

    def _request(self, client: httpx.Client, method: str, path: str, **kwargs):
        resp = client.request(method, path, **kwargs)
        if resp.status_code >= 400:
            raise AlpacaAPIError(f"Alpaca {method} {path}: {resp.status_code} {resp.text}")
        return resp.json()

    def is_market_open(self) -> bool:
        clock = self._request(self._trading, "GET", "/v2/clock")
        return bool(clock.get("is_open"))

    # ---- market data ----

    def get_price(self, symbol: str) -> float:
        data = self._request(self._data, "GET", f"/v2/stocks/{symbol}/trades/latest", params={"feed": DATA_FEED})
        return float(data["trade"]["p"])

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[list]:
        """Returns rows shaped like [open_time, open, high, low, close, volume]
        to match the shape the rest of the app already expects (close read
        from index 4 by technical_indicators.py)."""
        timeframe = _TIMEFRAMES.get(interval, "1Hour")
        data = self._request(
            self._data,
            "GET",
            f"/v2/stocks/{symbol}/bars",
            params={"timeframe": timeframe, "limit": limit, "feed": DATA_FEED},
        )
        bars = data.get("bars") or []
        return [[b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]] for b in bars[-limit:]]

    # ---- account / positions ----

    def get_account_balances(self) -> dict[str, float]:
        """Returns {"USD": cash, "<TICKER>": qty_held, ...} for non-zero
        balances/positions -- tickers have no quote-currency suffix (unlike
        crypto pairs), so they're used as-is for both the traded symbol and
        the balance key."""
        account = self._request(self._trading, "GET", "/v2/account")
        balances = {"USD": float(account["cash"])}
        positions = self._request(self._trading, "GET", "/v2/positions")
        for p in positions:
            qty = float(p["qty"])
            if qty > 0:
                balances[p["symbol"]] = qty
        return balances

    # ---- orders ----

    def _submit_order(self, symbol: str, side: str, *, notional: float | None = None, qty: float | None = None) -> dict:
        body: dict = {"symbol": symbol, "side": side.lower(), "type": "market", "time_in_force": "day"}
        if notional is not None:
            body["notional"] = f"{notional:.2f}"
        else:
            body["qty"] = f"{qty:.6f}"
        return self._request(self._trading, "POST", "/v2/orders", json=body)

    def _resolve_fill(self, order: dict, fallback_price: float) -> OrderResult:
        order_id = order.get("id", "")
        symbol = order.get("symbol", "")
        side = (order.get("side") or "").upper()

        for _ in range(FILL_POLL_ATTEMPTS):
            if order.get("status") == "filled":
                qty = float(order.get("filled_qty") or 0)
                price = float(order.get("filled_avg_price") or fallback_price)
                if qty > 0:
                    return OrderResult(order_id, symbol, side, qty, price, qty * price)
                break
            time.sleep(FILL_POLL_DELAY_SECONDS)
            try:
                order = self._request(self._trading, "GET", f"/v2/orders/{order_id}")
            except AlpacaAPIError:
                logger.warning("Order status poll failed for %s, retrying", order_id, exc_info=True)

        logger.warning(
            "Could not confirm fill for order %s within %ss, recording estimated qty/price instead",
            order_id,
            FILL_POLL_ATTEMPTS * FILL_POLL_DELAY_SECONDS,
        )
        requested_qty = order.get("qty")
        requested_notional = order.get("notional")
        if requested_qty is not None:
            qty = float(requested_qty)
        elif requested_notional is not None and fallback_price > 0:
            qty = float(requested_notional) / fallback_price
        else:
            qty = 0.0
        return OrderResult(order_id, symbol, side, qty, fallback_price, qty * fallback_price)

    def place_market_order_usdt_amount(self, symbol: str, side: str, usdt_amount: float) -> OrderResult:
        """Place a market order sized by a quote-currency (USD) notional
        amount -- Alpaca supports fractional shares via `notional`, which is
        essential for a small account to actually buy into higher-priced
        tickers. Name kept as `usdt_amount` for interface parity with the
        rest of the app."""
        order = self._submit_order(symbol, side, notional=usdt_amount)
        fallback_price = self.get_price(symbol)
        return self._resolve_fill(order, fallback_price)

    def place_market_order_quantity(self, symbol: str, side: str, raw_quantity: float) -> OrderResult:
        quantity = round(raw_quantity, 6)
        if quantity <= 0:
            raise ValueError(f"Computed quantity for {symbol} rounds to 0, amount too small")
        order = self._submit_order(symbol, side, qty=quantity)
        fallback_price = self.get_price(symbol)
        return self._resolve_fill(order, fallback_price)
