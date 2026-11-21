"""Klient Kraken (spot, EUR) — read-side adaptera brokera (Opcja D, prop. A1–A4).

Implementuje powierzchnię, której silnik oczekuje od brokera, ale dla Kraken:
mapowanie par/aktywów (BTC ↔ XXBTZEUR, ZEUR ↔ EUR), podpis prywatnego API
(nonce + HMAC-SHA512), parsowanie odpowiedzi do kształtów silnika.

Ta paczka to TYLKO ODCZYT (saldo/cena/świece). Składanie zleceń dojdzie OSOBNO,
dopiero po paper-teście (dyscyplina eskalacji uprawnień klucza, prop. I48).

Transport HTTP jest WSTRZYKIWANY (callable), więc rdzeń (mapowanie/podpis/parsowanie)
jest w pełni testowalny bez sieci. Klucz czytamy z env (KRAKEN_API_KEY/SECRET) — nigdy
z kodu/repo (prop. I47).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
import urllib.parse
from collections.abc import Callable

API_BASE = "https://api.kraken.com"

# Uniwersum (baza) -> nazwa pary Kraken w EUR (z AssetPairs). Jedno miejsce prawdy.
UNIVERSE_TO_KRAKEN = {
    "BTC": "XXBTZEUR", "ETH": "XETHZEUR", "SOL": "SOLEUR",
    "LINK": "LINKEUR", "AVAX": "AVAXEUR", "LTC": "XLTCZEUR", "DOGE": "XDGEUR",
}
# Kody aktywów Kraken w saldzie -> zwykły ticker.
KRAKEN_ASSET_TO_TICKER = {
    "ZEUR": "EUR", "XXBT": "BTC", "XBT": "BTC", "XETH": "ETH", "ETH": "ETH",
    "SOL": "SOL", "LINK": "LINK", "AVAX": "AVAX", "XLTC": "LTC", "LTC": "LTC",
    "XXDG": "DOGE", "XDG": "DOGE", "DOGE": "DOGE", "EUR": "EUR",
}
# Rama czasowa silnika -> interwał Kraken OHLC (minuty).
_INTERVAL_MIN = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}


def _base_of(symbol: str) -> str:
    """'BTC/USD' / 'BTC/EUR' / 'BTC' -> 'BTC'."""
    return (symbol or "").upper().split("/")[0]


def _fmt_num(x: float) -> str:
    """Liczba jako łańcuch dziesiętny bez notacji naukowej (Kraken odrzuca 1e-05).
    Do 10 miejsc po przecinku, obcięte zera końcowe."""
    s = f"{float(x):.10f}".rstrip("0").rstrip(".")
    return s or "0"


def to_kraken_pair(symbol: str) -> str | None:
    """Symbol uniwersum -> para Kraken EUR (albo None, gdy nieznana)."""
    return UNIVERSE_TO_KRAKEN.get(_base_of(symbol))


def from_kraken_asset(code: str) -> str:
    """Kod aktywa Kraken -> ticker (fallback: zdejmij wiodące X/Z Kraken-izmy)."""
    c = (code or "").upper()
    if c in KRAKEN_ASSET_TO_TICKER:
        return KRAKEN_ASSET_TO_TICKER[c]
    # Heurystyka dla nienazwanych: 'XETH'->'ETH', 'ZUSD'->'USD'
    if len(c) == 4 and c[0] in ("X", "Z"):
        return c[1:]
    return c


def sign(path: str, data: dict, secret: str) -> str:
    """Podpis prywatnego API Kraken: base64(HMAC-SHA512(path + SHA256(nonce+post))).
    `data` MUSI zawierać 'nonce'. Zweryfikowane na żywym API (Balance OK)."""
    post = urllib.parse.urlencode(data)
    encoded = (str(data["nonce"]) + post).encode()
    message = path.encode() + hashlib.sha256(encoded).digest()
    mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def parse_ohlc(result: dict, limit: int | None = None) -> list[list]:
    """Kraken OHLC result -> wiersze [czas, open, high, low, close, volume]
    (indeksy jak u Alpaki: close=4), najstarsze pierwsze. Pomija klucz 'last'."""
    rows: list[list] = []
    for key, series in (result or {}).items():
        if key == "last" or not isinstance(series, list):
            continue
        for r in series:
            # Kraken: [time, open, high, low, close, vwap, volume, count]
            try:
                rows.append([int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[6])])
            except (TypeError, ValueError, IndexError):
                continue
        break
    rows.sort(key=lambda x: x[0])
    return rows[-limit:] if limit else rows


def parse_balances(result: dict) -> dict[str, float]:
    """Kraken Balance result -> {ticker: ilość} dla niezerowych."""
    out: dict[str, float] = {}
    for code, amt in (result or {}).items():
        try:
            v = float(amt)
        except (TypeError, ValueError):
            continue
        if v == 0:
            continue
        out[from_kraken_asset(code)] = out.get(from_kraken_asset(code), 0.0) + v
    return out


def parse_ticker_price(result: dict) -> float | None:
    """Kraken Ticker result -> ostatnia cena transakcji (pole 'c'[0])."""
    for _pair, info in (result or {}).items():
        try:
            return float(info["c"][0])
        except (TypeError, ValueError, KeyError, IndexError):
            return None
    return None


class KrakenError(RuntimeError):
    pass


class KrakenClient:
    """Read-side klient Kraken. `transport(method, url, headers, body) -> dict`
    jest wstrzykiwany (domyślnie urllib przez proxy agenta). Klucz/sekret z env."""

    def __init__(self, key: str = "", secret: str = "", transport: Callable | None = None):
        self._key = key
        self._secret = secret
        self._transport = transport or _default_transport
        self._nonce_base = int(time.time() * 1000)

    @classmethod
    def from_env(cls, transport: Callable | None = None) -> KrakenClient:
        return cls(os.getenv("KRAKEN_API_KEY", ""), os.getenv("KRAKEN_API_SECRET", ""), transport)

    def _nonce(self) -> str:
        self._nonce_base += 1
        return str(self._nonce_base)

    def _public(self, path: str, params: dict) -> dict:
        url = f"{API_BASE}{path}?{urllib.parse.urlencode(params)}"
        resp = self._transport("GET", url, {}, None)
        if resp.get("error"):
            raise KrakenError(f"{path}: {resp['error']}")
        return resp.get("result") or {}

    def _private(self, path: str, data: dict | None = None) -> dict:
        if not self._key or not self._secret:
            raise KrakenError("brak klucza Kraken w env (KRAKEN_API_KEY/SECRET)")
        body = dict(data or {})
        body["nonce"] = self._nonce()
        headers = {"API-Key": self._key, "API-Sign": sign(path, body, self._secret),
                   "Content-Type": "application/x-www-form-urlencoded"}
        resp = self._transport("POST", f"{API_BASE}{path}", headers, urllib.parse.urlencode(body))
        if resp.get("error"):
            raise KrakenError(f"{path}: {resp['error']}")
        return resp.get("result") or {}

    # ---- odczyt (publiczny) ----
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 24) -> list[list]:
        pair = to_kraken_pair(symbol)
        if not pair:
            return []
        res = self._public("/0/public/OHLC", {"pair": pair, "interval": _INTERVAL_MIN.get(interval, 60)})
        return parse_ohlc(res, limit)

    def get_price(self, symbol: str) -> float:
        pair = to_kraken_pair(symbol)
        if not pair:
            return 0.0
        return parse_ticker_price(self._public("/0/public/Ticker", {"pair": pair})) or 0.0

    # ---- odczyt (prywatny) ----
    def get_account_balances(self) -> dict[str, float]:
        return parse_balances(self._private("/0/private/Balance"))

    def get_account_summary(self, quote: str = "EUR") -> dict[str, float]:
        """{quote: equity} z TradeBalance — spójne z użyciem w silniku (cash w walucie konta)."""
        res = self._private("/0/private/TradeBalance", {"asset": "ZEUR"})
        try:
            return {quote: float(res.get("eb", 0.0))}  # eb = equity balance
        except (TypeError, ValueError):
            return {quote: 0.0}

    # ---- zapis (zlecenia) — DOMYŚLNIE DRY-RUN ----
    def place_order(
        self, symbol: str, side: str, volume: float, *,
        ordertype: str = "market", price: float | None = None,
        leverage: int | None = None, validate: bool = True,
    ) -> dict:
        """Składa zlecenie przez AddOrder. `validate=True` (DOMYŚLNIE) = Kraken tylko
        WALIDUJE zlecenie (sprawdza środki/min/format), NIE wykonuje — bezpieczny dry-run.
        `leverage` ustawiamy TYLKO dla short-hedge (Opcja D, margin); None = spot.
        Realny handel wymaga jawnego validate=False (gated wyżej przez config + klucz z
        uprawnieniem 'Create Orders'). side: 'buy'|'sell'."""
        pair = to_kraken_pair(symbol)
        if not pair:
            raise KrakenError(f"nieznana para dla {symbol}")
        data: dict = {
            "pair": pair, "type": side.lower(), "ordertype": ordertype,
            "volume": _fmt_num(volume),
        }
        if ordertype == "limit":
            if price is None:
                raise KrakenError("limit wymaga ceny")
            data["price"] = _fmt_num(price)
        if leverage:
            data["leverage"] = str(leverage)
        if validate:
            data["validate"] = "true"
        return self._private("/0/private/AddOrder", data)

    def place_market_order_quantity(self, symbol: str, side: str, qty: float, *, validate: bool = True) -> dict:
        """Market po ILOŚCI bazowej (jak AlpacaClient.place_market_order_quantity)."""
        return self.place_order(symbol, side, abs(qty), ordertype="market", validate=validate)

    def place_market_order_eur_amount(
        self, symbol: str, side: str, eur_amount: float, price: float, *, validate: bool = True,
    ) -> dict:
        """Market po KWOCIE EUR (odpowiednik USDT-amount u Alpaki): przelicza na ilość
        bazową po podanej cenie. Cena z feedu; precyzję docina broker/min-order."""
        if price <= 0:
            raise KrakenError("brak ceny do przeliczenia kwoty EUR na ilość")
        return self.place_market_order_quantity(symbol, side, eur_amount / price, validate=validate)


def _default_transport(method: str, url: str, headers: dict, body: str | None) -> dict:
    """Domyślny transport: urllib przez proxy agenta + CA bundle. Izolowany, żeby
    testy mogły go podmienić. Zwraca sparsowany JSON Kraken."""
    import json
    import ssl
    import urllib.request

    ctx = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
    opener = urllib.request.build_opener(*handlers)
    data = body.encode() if body else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "gieldarek", **headers}, method=method)
    with opener.open(req, timeout=30) as r:
        return json.load(r)
