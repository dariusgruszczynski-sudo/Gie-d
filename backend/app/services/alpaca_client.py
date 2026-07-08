"""Thin wrapper around Alpaca's Trading + Market Data REST APIs.

Unlike Kraken, Alpaca offers a real paper-trading environment with the exact
same API surface as live -- flip ALPACA_PAPER=true anytime to rehearse safely
on Alpaca's simulated $100k account; the rest of the app never needs to know
which one it's talking to, only the base URL + which key pair changes.

Authentication is a pair of plain headers (no HMAC signing needed, unlike
Kraken), which makes this considerably simpler and less error-prone."""

import logging
import math
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

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
_TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440}
# Calendar time needed per TRADING bar: the market trades ~6.5h out of 24 on
# ~5 of 7 days, so reaching back `limit` bars needs roughly 5x the naive bar
# span in wall-clock time.
_CALENDAR_SPAN_FACTOR = 5
# Extended-hours (pre-market/after-hours) orders must be whole-share LIMIT
# orders -- fractional and notional/market orders are regular-session only,
# an industry-wide rule (not Alpaca-specific) tied to thinner liquidity
# outside the regular session. The limit price is offset from the last trade
# to raise fill odds without materially chasing price in a thin book.
EXTENDED_HOURS_LIMIT_BUFFER_PCT = 0.3


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

    def get_calendar(self, start: str, end: str) -> list[dict]:
        """Trading days with their actual regular-session open/close for
        that date (accounts for holidays and early closes), used by
        market_hours.py to derive pre-market/after-hours windows on top."""
        return self._request(self._trading, "GET", "/v2/calendar", params={"start": start, "end": end})

    # ---- market data ----

    def get_price(self, symbol: str) -> float:
        data = self._request(self._data, "GET", f"/v2/stocks/{symbol}/trades/latest", params={"feed": DATA_FEED})
        return float(data["trade"]["p"])

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[list]:
        """Returns rows shaped like [open_time, open, high, low, close, volume]
        to match the shape the rest of the app already expects (close read
        from index 4 by technical_indicators.py).

        `start` is passed explicitly: without it Alpaca only returns bars from
        the CURRENT trading day, so a 200-bar indicator request silently came
        back with 6-7 bars and RSI/MACD sat at insufficient_data forever --
        Claude was deciding blind all session (and citing the missing
        technicals as its reason to HOLD)."""
        timeframe = _TIMEFRAMES.get(interval, "1Hour")
        minutes = _TIMEFRAME_MINUTES.get(interval, 60)
        start = datetime.now(timezone.utc) - timedelta(minutes=minutes * limit * _CALENDAR_SPAN_FACTOR)
        data = self._request(
            self._data,
            "GET",
            f"/v2/stocks/{symbol}/bars",
            params={
                "timeframe": timeframe,
                "limit": limit,
                "feed": DATA_FEED,
                "start": start.isoformat(),
                # Newest-first, otherwise start+limit returns the OLDEST bars
                # in the window (Alpaca paginates ascending from `start`).
                "sort": "desc",
            },
        )
        bars = list(reversed(data.get("bars") or []))  # back to oldest-first for the indicators
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

    def _submit_order(
        self,
        symbol: str,
        side: str,
        *,
        notional: float | None = None,
        qty: float | None = None,
        order_type: str = "market",
        limit_price: float | None = None,
        extended_hours: bool = False,
    ) -> dict:
        body: dict = {"symbol": symbol, "side": side.lower(), "type": order_type, "time_in_force": "day"}
        if notional is not None:
            body["notional"] = f"{notional:.2f}"
        else:
            body["qty"] = f"{qty:.6f}"
        if order_type == "limit":
            body["limit_price"] = f"{limit_price:.2f}"
        if extended_hours:
            body["extended_hours"] = True
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
        # round() rounds to nearest and can round UP past the actual held
        # balance on a full-position SELL (e.g. available 0.20818759 ->
        # round(.., 6) = 0.208188, which Alpaca rejects with 403 insufficient
        # qty). Floor instead so the submitted qty never exceeds what's held;
        # the tiny epsilon guards against float representation error (e.g.
        # 0.4 stored as 0.40000000000000002) flooring a whole number down.
        quantity = math.floor(raw_quantity * 1_000_000 + 1e-7) / 1_000_000
        if quantity <= 0:
            raise ValueError(f"Computed quantity for {symbol} rounds to 0, amount too small")
        order = self._submit_order(symbol, side, qty=quantity)
        fallback_price = self.get_price(symbol)
        return self._resolve_fill(order, fallback_price)

    def place_order_for_session(
        self,
        symbol: str,
        side: str,
        *,
        session: str,
        usdt_amount: float | None = None,
        quantity: float | None = None,
    ) -> OrderResult:
        """Routes to a plain market/notional order during the regular
        session (fast, fractional-friendly), or a whole-share LIMIT order
        with `extended_hours=True` during pre-market/after-hours, since
        those sessions reject fractional and market/notional orders.
        `session` is one of market_hours.{PRE_MARKET,REGULAR,AFTER_HOURS} --
        passed in rather than queried here so callers make exactly one
        market_hours lookup per cycle."""
        if session == "regular":
            if usdt_amount is not None:
                return self.place_market_order_usdt_amount(symbol, side, usdt_amount)
            return self.place_market_order_quantity(symbol, side, quantity)

        price = self.get_price(symbol)
        buffer = 1 + EXTENDED_HOURS_LIMIT_BUFFER_PCT / 100 if side.upper() == "BUY" else 1 - EXTENDED_HOURS_LIMIT_BUFFER_PCT / 100
        limit_price = round(price * buffer, 2)

        raw_qty = usdt_amount / price if usdt_amount is not None else quantity
        whole_qty = math.floor(raw_qty)
        if whole_qty <= 0:
            raise ValueError(
                f"Rozszerzone godziny handlu wymagają całych akcji -- "
                f"{usdt_amount if usdt_amount is not None else quantity} przy cenie {price} "
                f"daje 0 całych akcji {symbol}"
            )

        order = self._submit_order(
            symbol, side, qty=whole_qty, order_type="limit", limit_price=limit_price, extended_hours=True
        )
        return self._resolve_fill(order, fallback_price=price)
