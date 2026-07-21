"""Thin wrapper around Alpaca's Trading + Market Data REST APIs.

Unlike Kraken, Alpaca offers a real paper-trading environment with the exact
same API surface as live -- flip ALPACA_PAPER=true anytime to rehearse safely
on Alpaca's simulated $100k account; the rest of the app never needs to know
which one it's talking to, only the base URL + which key pair changes.

Authentication is a pair of plain headers (no HMAC signing needed, unlike
Kraken), which makes this considerably simpler and less error-prone.

US equities/ETFs only: both trading legs (regular session + extended hours)
run the SAME equities account -- the difference between them is the session
window and order type (handled by the trading engine / order helpers), not a
separate asset class here."""

import logging
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
# Extended-hours orders must be LIMIT (Alpaca rejects MARKET outside RTH). Price
# them slightly THROUGH the last trade (a "marketable limit") so they actually
# fill in thin pre-/after-market books without chasing far past fair value.
EXTENDED_LIMIT_BUFFER = 0.004  # 0.4%
_TIMEFRAMES = {"1m": "1Min", "5m": "5Min", "15m": "15Min", "1h": "1Hour", "1d": "1Day"}
_TIMEFRAME_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440}
# Calendar time needed per TRADING bar: the market trades ~6.5h out of 24 on
# ~5 of 7 days, so reaching back `limit` bars needs roughly 5x the naive bar
# span in wall-clock time. At 5x, 200 hourly bars needed a ~41.7-day window but
# only ~44-45 calendar days actually contain 200 regular-session hours -- SMA200
# (needs exactly 200) would ALWAYS come back "insufficient_data" on the "1h"
# signal_timeframe. 7x covers 1h (and the previously-marginal 15m) with a
# holiday buffer; still tiny relative to "1d"'s multi-year window.
_CALENDAR_SPAN_FACTOR = 7


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
        balances/positions, keyed by the plain equity ticker (== our whitelist
        convention)."""
        account = self._request(self._trading, "GET", "/v2/account")
        balances = {"USD": float(account["cash"])}
        positions = self._request(self._trading, "GET", "/v2/positions")
        for p in positions:
            qty = float(p["qty"])
            if qty > 0:
                balances[p["symbol"]] = qty
        return balances

    def get_account_summary(self) -> dict[str, float]:
        """The broker's OWN authoritative account figures -- Alpaca already sums
        cash + every position with no risk of the app double-counting a ticket
        that sits on two whitelists. `equity` = the real total portfolio value.
        Used to reconcile our reconstructed account view against the source of
        truth (see the /api reconcile check)."""
        a = self._request(self._trading, "GET", "/v2/account")
        return {
            "cash": float(a["cash"]),
            "equity": float(a["equity"]),
            "long_market_value": float(a.get("long_market_value", 0.0) or 0.0),
        }

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
            # 9 dp = Alpaca's max fractional precision; 6 dp used to round a
            # full-position SELL up past the held balance (403 insufficient qty).
            body["qty"] = f"{qty:.9f}"
        if order_type == "limit":
            body["limit_price"] = f"{limit_price:.2f}"
        if extended_hours:
            body["extended_hours"] = True
        return self._request(self._trading, "POST", "/v2/orders", json=body)

    def _resolve_fill(self, order: dict, fallback_price: float, symbol: str) -> OrderResult:
        """`symbol` is the plain equity ticker passed in by the caller (used
        directly, not read back from the order response) so the Trade table
        always keys on our whitelist convention for average_cost_basis,
        cooldowns, peaks, ..."""
        order_id = order.get("id", "")
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
        return self._resolve_fill(order, fallback_price, symbol)

    def place_market_order_quantity(self, symbol: str, side: str, raw_quantity: float) -> OrderResult:
        # Alpaca accepts fractional quantities to 9 decimal places. Rounding to
        # only 6 dp rounded a full-position SELL UP past the actual held
        # balance (available 0.20818759 -> 0.208188) -> 403 insufficient qty,
        # while flooring to 6 dp instead left an unsellable ~1e-7 dust
        # remainder that then jammed the exit loop. At 9 dp an <=9-decimal
        # balance is represented exactly: the request never exceeds what's held
        # and a full exit leaves no dust behind.
        quantity = round(raw_quantity, 9)
        if quantity <= 0:
            raise ValueError(f"Computed quantity for {symbol} rounds to 0, amount too small")
        order = self._submit_order(symbol, side, qty=quantity)
        fallback_price = self.get_price(symbol)
        return self._resolve_fill(order, fallback_price, symbol)

    def _resolve_fill_or_cancel(self, order: dict, fallback_price: float, symbol: str) -> OrderResult:
        """Like _resolve_fill, but for extended-hours LIMIT orders that may NOT
        fill in a thin book: poll for the fill, and if it doesn't land inside
        the window, CANCEL the order and raise -- so we never book a phantom
        trade that never happened (or let a stale limit fill later at a price we
        didn't record)."""
        order_id = order.get("id", "")
        side = (order.get("side") or "").upper()
        for _ in range(FILL_POLL_ATTEMPTS):
            if order.get("status") == "filled":
                qty = float(order.get("filled_qty") or 0)
                price = float(order.get("filled_avg_price") or fallback_price)
                if qty > 0:
                    return OrderResult(order_id, symbol, side, qty, price, qty * price)
            time.sleep(FILL_POLL_DELAY_SECONDS)
            try:
                order = self._request(self._trading, "GET", f"/v2/orders/{order_id}")
            except AlpacaAPIError:
                logger.warning("Extended-hours order poll failed for %s, retrying", order_id, exc_info=True)
        try:
            self._request(self._trading, "DELETE", f"/v2/orders/{order_id}")
        except AlpacaAPIError:
            logger.warning("Failed to cancel unfilled extended-hours order %s", order_id, exc_info=True)
        raise AlpacaAPIError(
            f"Zlecenie LIMIT {symbol} nie wypełniło się w oknie poza sesją — anulowano (cienki rynek)"
        )

    def place_extended_limit_order(
        self, symbol: str, side: str, *, usdt_amount: float | None = None, quantity: float | None = None
    ) -> OrderResult:
        """WHOLE-share marketable-LIMIT order for pre-/after-market. Alpaca
        rejects MARKET orders and fractional shares outside regular hours, so a
        notional BUY is converted to an integer share count at a limit priced
        slightly through the last trade; a SELL floors to whole shares."""
        price = self.get_price(symbol)
        if price <= 0:
            raise AlpacaAPIError(f"Brak ceny dla {symbol}, nie mogę wystawić zlecenia LIMIT poza sesją")
        if side.upper() == "BUY":
            limit_price = round(price * (1 + EXTENDED_LIMIT_BUFFER), 2)
            shares = int((usdt_amount or 0) // limit_price) if usdt_amount is not None else int(quantity or 0)
        else:
            limit_price = round(price * (1 - EXTENDED_LIMIT_BUFFER), 2)
            # Whole shares only after hours. Round-with-epsilon so a full exit of
            # a whole-share position (held qty stored as 2.9999999) doesn't floor
            # to 2 and strand a share; never rounds UP past what's actually held.
            shares = int((quantity or 0) + 1e-6)
        if shares < 1:
            raise AlpacaAPIError(
                f"Poza sesją tylko CAŁE akcje {symbol}: budżet/pozycja nie starcza na 1 sztukę "
                f"(cena ~${limit_price:.2f})"
            )
        order = self._submit_order(
            symbol, side, qty=float(shares), order_type="limit", limit_price=limit_price, extended_hours=True
        )
        return self._resolve_fill_or_cancel(order, price, symbol)

    def place_order_for_session(
        self,
        symbol: str,
        side: str,
        *,
        session: str = "regular",
        usdt_amount: float | None = None,
        quantity: float | None = None,
    ) -> OrderResult:
        """Routes by session: pre-/after-market ("pre"/"post") go through the
        whole-share extended-hours LIMIT path; the regular session uses plain
        MARKET/notional orders (fractional-friendly, essential for a small
        account)."""
        if session in ("pre", "post"):
            return self.place_extended_limit_order(symbol, side, usdt_amount=usdt_amount, quantity=quantity)
        if usdt_amount is not None:
            return self.place_market_order_usdt_amount(symbol, side, usdt_amount)
        return self.place_market_order_quantity(symbol, side, quantity)
