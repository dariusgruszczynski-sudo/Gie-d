"""Thin wrapper around Kraken's REST API (public market data + private
trading/balance), signed manually per Kraken's authentication scheme.

Unlike Binance, Kraken has no official Python SDK bundled in requirements and
-- more importantly -- no public sandbox/testnet for the spot market, so
there is no test/live switch here: every call against /private/* is real and
moves real EUR."""

import base64
import hashlib
import hmac
import logging
import math
import time
import urllib.parse
from dataclasses import dataclass

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

API_URL = "https://api.kraken.com"
# Kraken's AddOrder response for a market order doesn't include the fill --
# poll QueryOrders briefly until it closes rather than guessing the price.
FILL_POLL_ATTEMPTS = 6
FILL_POLL_DELAY_SECONDS = 0.5


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float  # quote-currency (EUR) notional value of the fill


class KrakenAPIError(RuntimeError):
    pass


class KrakenClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = httpx.Client(base_url=API_URL, timeout=15.0)
        self._asset_altnames: dict[str, str] | None = None

    @property
    def mode(self) -> str:
        return "live"

    # ---- public (unauthenticated) endpoints ----

    def _public(self, path: str, params: dict | None = None) -> dict:
        resp = self._client.get(f"/0/public/{path}", params=params or {})
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise KrakenAPIError(f"Kraken public/{path}: {data['error']}")
        return data["result"]

    def get_price(self, symbol: str) -> float:
        result = self._public("Ticker", {"pair": symbol})
        (ticker,) = result.values()
        return float(ticker["c"][0])

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[list]:
        """Returns rows shaped like [open_time, open, high, low, close, volume]
        to match the shape the rest of the app already expects (close read
        from index 4 by technical_indicators.py)."""
        minutes = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}.get(interval, 60)
        result = self._public("OHLC", {"pair": symbol, "interval": minutes})
        rows = next(v for k, v in result.items() if k != "last")
        # Kraken row: [time, open, high, low, close, vwap, volume, count]
        return [[r[0], r[1], r[2], r[3], r[4], r[6]] for r in rows[-limit:]]

    def _asset_altname(self, kraken_code: str) -> str:
        """Kraken's private Balance endpoint returns its own internal asset
        codes (e.g. "XXBT", "ZEUR"), not the pair altnames used in
        trading_whitelist (e.g. "XBT", "EUR") -- translate via the public
        Assets endpoint (cached) rather than hardcoding the X/Z-prefix
        convention, since it doesn't apply uniformly to newer assets."""
        if self._asset_altnames is None:
            result = self._public("Assets")
            self._asset_altnames = {code: info["altname"] for code, info in result.items()}
        return self._asset_altnames.get(kraken_code, kraken_code)

    def get_symbol_info(self, symbol: str) -> dict:
        result = self._public("AssetPairs", {"pair": symbol})
        (info,) = result.values()
        return info

    # ---- private (authenticated) endpoints ----

    def _sign(self, path: str, data: dict) -> str:
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data["nonce"]) + postdata).encode()
        message = path.encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self._settings.kraken_api_secret), message, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def _private(self, path: str, data: dict | None = None) -> dict:
        data = dict(data or {})
        data["nonce"] = int(time.time() * 1000)
        full_path = f"/0/private/{path}"
        headers = {
            "API-Key": self._settings.kraken_api_key,
            "API-Sign": self._sign(full_path, data),
        }
        resp = self._client.post(full_path, data=data, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise KrakenAPIError(f"Kraken private/{path}: {result['error']}")
        return result["result"]

    def get_account_balances(self) -> dict[str, float]:
        """Returns {asset: free_balance} for non-zero balances, keyed by
        Kraken's friendly altnames (XBT, ETH, EUR, ...) so callers can match
        them against trading_whitelist pairs with a plain string suffix strip."""
        raw = self._private("Balance")
        balances: dict[str, float] = {}
        for code, amount_str in raw.items():
            amount = float(amount_str)
            if amount > 0:
                balances[self._asset_altname(code)] = amount
        return balances

    def _round_step_size(self, quantity: float, symbol: str) -> float:
        """Kraken expresses order-size precision as lot_decimals (decimal
        places), unlike Binance's stepSize -- floor to that many places."""
        info = self.get_symbol_info(symbol)
        decimals = int(info.get("lot_decimals", 8))
        factor = 10**decimals
        return math.floor(quantity * factor) / factor

    def _await_fill(self, order_id: str, fallback_qty: float, fallback_price: float) -> tuple[float, float]:
        """Market orders on Kraken fill almost immediately but AddOrder's
        response doesn't carry the executed price/qty -- poll QueryOrders
        briefly for the real fill. Falls back to the pre-order quote (with a
        warning) rather than raising, since the order has already gone
        through and we must still record *something* for it."""
        if not order_id:
            return fallback_qty, fallback_price
        for _ in range(FILL_POLL_ATTEMPTS):
            try:
                result = self._private("QueryOrders", {"txid": order_id})
                info = result.get(order_id)
                if info and info.get("status") == "closed":
                    vol_exec = float(info.get("vol_exec", 0) or 0)
                    cost = float(info.get("cost", 0) or 0)
                    if vol_exec > 0 and cost > 0:
                        return vol_exec, cost / vol_exec
                    break
            except KrakenAPIError:
                logger.warning("QueryOrders failed for %s, retrying", order_id, exc_info=True)
            time.sleep(FILL_POLL_DELAY_SECONDS)
        logger.warning(
            "Could not confirm fill for order %s within %ss, recording estimated qty/price instead",
            order_id,
            FILL_POLL_ATTEMPTS * FILL_POLL_DELAY_SECONDS,
        )
        return fallback_qty, fallback_price

    def place_market_order_usdt_amount(self, symbol: str, side: str, usdt_amount: float) -> OrderResult:
        """Place a market order sized by a quote-currency (EUR) notional
        amount. Name kept as `usdt_amount` for interface parity with the
        rest of the app, which still calls this the same way it did for
        Binance/USDT."""
        price = self.get_price(symbol)
        raw_quantity = usdt_amount / price
        return self.place_market_order_quantity(symbol, side, raw_quantity)

    def place_market_order_quantity(self, symbol: str, side: str, raw_quantity: float) -> OrderResult:
        price = self.get_price(symbol)
        quantity = self._round_step_size(raw_quantity, symbol)
        if quantity <= 0:
            raise ValueError(f"Computed quantity for {symbol} rounds to 0, amount too small")

        result = self._private(
            "AddOrder",
            {
                "pair": symbol,
                "type": side.lower(),
                "ordertype": "market",
                "volume": f"{quantity:.8f}",
            },
        )
        order_id = (result.get("txid") or [""])[0]
        executed_qty, avg_price = self._await_fill(order_id, fallback_qty=quantity, fallback_price=price)
        return OrderResult(
            order_id=order_id,
            symbol=symbol,
            side=side.upper(),
            quantity=executed_qty,
            price=avg_price,
            usdt_value=executed_qty * avg_price,
        )
