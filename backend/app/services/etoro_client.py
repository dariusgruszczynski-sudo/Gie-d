"""Thin wrapper around eToro's public API for the crypto/forex (24-7 overnight)
venue -- mirrors the AlpacaClient interface (get_price / get_klines /
get_account_balances / place_order_for_session) so the trading engine can drive
either broker without knowing which one it's talking to.

Verified against the live API (2026-07):
  auth      = headers x-api-key (public key) + x-user-key (private key)
  price     = GET /api/v1/market-data/instruments/rates?instrumentIds=<id>  -> ask/bid
  portfolio = GET /api/v1/trading/info/portfolio -> clientPortfolio.{credit, positions}
  catalogue = GET /api/v1/market-data/instruments -> instrumentDisplayDatas[]
  (demo is NOT permitted for this token -> live only; candles are unavailable
   on eToro, so they come from etoro_market_data instead.)

NOTE: the ORDER-EXECUTION path could not be verified read-only (it's a POST and
the account was unfunded during discovery). place_order_for_session is written
against the documented shape and surfaces the full API error, so the first
funded smoke-test pins the exact endpoint/body if this needs adjusting."""

import logging
import uuid
from dataclasses import dataclass

import httpx

from app.config import Settings
from app.services import etoro_market_data

logger = logging.getLogger(__name__)

ETORO_BASE = "https://public-api.etoro.com"
CRYPTO_TYPE_ID = 10
FOREX_TYPE_ID = 1
# Best-effort order endpoint (see module docstring). Overridable once verified.
ORDER_PATH = "/api/v1/trading/execution/orders"

# Our whitelist ticker -> eToro instrument display name, resolved to a numeric
# instrumentID via the catalogue. KNOWN_IDS short-circuits the ones already
# verified so the client works even if the catalogue fetch is briefly down.
SYMBOL_TO_ETORO_NAME = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "BCH": "Bitcoin Cash",
    "XRP": "XRP",
    "LTC": "Litecoin",
    "ADA": "Cardano",
    "DOGE": "Dogecoin",
    "EURUSD": "EUR/USD",
    "GBPUSD": "GBP/USD",
    "USDJPY": "USD/JPY",
    "AUDUSD": "AUD/USD",
    "USDCHF": "USD/CHF",
    "USDCAD": "USD/CAD",
}
KNOWN_IDS = {"BTC": 100000, "ETH": 100001, "SOL": 100063, "EURUSD": 1}


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float


class EToroAPIError(RuntimeError):
    pass


class EToroClient:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._http = httpx.Client(base_url=ETORO_BASE, timeout=20.0)
        self._id_by_symbol: dict[str, int] = dict(KNOWN_IDS)
        self._symbol_by_id: dict[int, str] = {v: k for k, v in KNOWN_IDS.items()}
        self._catalogue_loaded = False

    @property
    def mode(self) -> str:
        # The Agent Portfolio token only has live permission (demo returns 403).
        return "paper" if self._settings.etoro_paper else "live"

    def _headers(self) -> dict:
        return {
            "x-api-key": self._settings.etoro_api_key,
            "x-user-key": self._settings.etoro_user_key,
            "x-request-id": str(uuid.uuid4()),
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs):
        resp = self._http.request(method, path, headers=self._headers(), **kwargs)
        if resp.status_code >= 400:
            raise EToroAPIError(f"eToro {method} {path}: {resp.status_code} {resp.text}")
        return resp.json()

    # ---- instrument id resolution ----

    def _load_catalogue(self) -> None:
        if self._catalogue_loaded:
            return
        data = self._request("GET", "/api/v1/market-data/instruments")
        name_to_id = {
            (it.get("instrumentDisplayName") or "").strip(): it.get("instrumentID")
            for it in data.get("instrumentDisplayDatas", [])
        }
        for symbol, name in SYMBOL_TO_ETORO_NAME.items():
            iid = name_to_id.get(name)
            if iid is not None:
                self._id_by_symbol[symbol] = iid
                self._symbol_by_id[iid] = symbol
        self._catalogue_loaded = True

    def instrument_id(self, symbol: str) -> int:
        symbol = symbol.upper()
        if symbol in self._id_by_symbol:
            return self._id_by_symbol[symbol]
        self._load_catalogue()
        if symbol not in self._id_by_symbol:
            raise EToroAPIError(f"Nieznany instrument eToro dla symbolu {symbol}")
        return self._id_by_symbol[symbol]

    # ---- market data ----

    def get_price(self, symbol: str) -> float:
        iid = self.instrument_id(symbol)
        data = self._request("GET", "/api/v1/market-data/instruments/rates", params={"instrumentIds": iid})
        rates = data.get("rates") or []
        if not rates:
            raise EToroAPIError(f"Brak notowania eToro dla {symbol} (id={iid})")
        r = rates[0]
        return (float(r["ask"]) + float(r["bid"])) / 2.0

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[list]:
        # eToro has no candle endpoint -> external OHLC (see etoro_market_data).
        return etoro_market_data.get_candles(symbol, interval, limit)

    # ---- account / positions ----

    def get_account_balances(self) -> dict[str, float]:
        """Returns {"USD": cash, "<TICKER>": units_held, ...}. Cash is
        clientPortfolio.credit; open positions are summed per instrument and
        mapped back to our tickers."""
        data = self._request("GET", "/api/v1/trading/info/portfolio")
        cp = data.get("clientPortfolio", {})
        balances: dict[str, float] = {"USD": float(cp.get("credit", 0.0))}
        for pos in cp.get("positions", []) or []:
            iid = pos.get("instrumentID")
            if iid is None:
                continue
            symbol = self._symbol_by_id.get(iid)
            if symbol is None:
                self._load_catalogue()
                symbol = self._symbol_by_id.get(iid)
            if symbol is None:
                continue
            # eToro reports position size by invested amount and/or units;
            # prefer units, fall back to amount. (Shape confirmed on the first
            # funded smoke-test; both keys are handled defensively.)
            units = pos.get("units")
            if units is None:
                units = pos.get("amount", 0.0)
            balances[symbol] = balances.get(symbol, 0.0) + float(units or 0.0)
        return balances

    # ---- orders ----

    def place_order_for_session(
        self,
        symbol: str,
        side: str,
        *,
        session: str = "regular",
        usdt_amount: float | None = None,
        quantity: float | None = None,
    ) -> OrderResult:
        """Crypto/forex trade sized by USD notional (usdt_amount) or units
        (quantity). session is accepted for interface parity with AlpacaClient
        but ignored -- crypto/forex trade 24/7."""
        iid = self.instrument_id(symbol)
        price = self.get_price(symbol)
        is_buy = side.upper() == "BUY"
        if usdt_amount is not None:
            amount_usd = float(usdt_amount)
            units = amount_usd / price if price > 0 else 0.0
        else:
            units = float(quantity or 0.0)
            amount_usd = units * price
        if amount_usd <= 0:
            raise EToroAPIError(f"Kwota zlecenia eToro dla {symbol} <= 0")

        body = {
            "instrumentId": iid,
            "isBuy": is_buy,
            "amount": round(amount_usd, 2),
            "leverage": 1,
        }
        result = self._request("POST", ORDER_PATH, json=body)
        order_id = str(result.get("orderId") or result.get("id") or result.get("positionId") or "")
        return OrderResult(order_id, symbol, side.upper(), units, price, amount_usd)
