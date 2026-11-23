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
from dataclasses import dataclass


@dataclass
class KrakenOrderResult:
    """Zgodny kształtem z AlpacaClient.OrderResult (duck-typing dla silnika)."""
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    usdt_value: float  # notional w walucie konta (EUR) — nazwa pola zachowana dla zgodności

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

# Kraken używa własnych tickerów dla kilku baz (wsname): XBT=BTC, XDG=DOGE.
# Normalizujemy do zwykłych, których używa uniwersum/silnik.
_BASE_ALIAS = {"XBT": "BTC", "XDG": "DOGE", "XXBT": "BTC", "XXDG": "DOGE"}
# Bazy, których NIE handlujemy jako krypto (stablecoiny i fiat sparowane z EUR).
_STABLE_FIAT = {
    "USDT", "USDC", "DAI", "PYUSD", "EURT", "USDG", "RLUSD", "TUSD", "USDR",
    "EURQ", "USDQ", "USDS", "EUR", "USD", "GBP", "AUD", "CHF", "CAD", "JPY", "USDD",
    "EURC", "EURR", "USDE", "FDUSD", "GUSD", "USDL", "USD0", "LUSD", "SUSD",
    "CRVUSD", "USDM", "GHO", "FRAX", "USTC",
}

# DYNAMICZNE uniwersum EUR z Krakena (cały rynek, nie 7 na sztywno). Budowane z
# publicznego AssetPairs + Ticker (ranking płynności), cache z TTL. Zasilane przez
# list_crypto_symbols (woła je skaner na starcie cyklu, PRZED get_price/get_klines),
# a to_kraken_pair z niego czyta. Fallback: zahardkodowane UNIVERSE_TO_KRAKEN.
_DYN_PAIRS: dict[str, str] = {}      # baza znormalizowana -> altname Kraken (np. 'SOL' -> 'SOLEUR')
_DYN_ORDER: list[str] = []           # '<BAZA>/EUR' posortowane po płynności (malejąco)
_DYN_PAIR_DEC: dict[str, int] = {}   # baza -> pair_decimals (precyzja CENY) — mech#2 limit
_DYN_PAIR_MIN: dict[str, float] = {} # baza -> ordermin (MIN. wolumen BAZY na zlecenie)
_DYN_AT: float = 0.0
_DYN_TTL_SEC: float = 1800.0          # 30 min — pary zmieniają się wolno


def pair_price_decimals(symbol: str) -> int | None:
    """Precyzja CENY pary (pair_decimals z AssetPairs) dla bazy symbolu. None gdy
    nieznana (pula fallback / cache pusty) — wołający wtedy NIE ryzykuje limitu z
    błędną precyzją i schodzi na market. mech#2."""
    base = _norm_base((symbol or "").split("/")[0])
    return _DYN_PAIR_DEC.get(base)


def pair_ordermin(symbol: str) -> float | None:
    """Minimalny WOLUMEN zlecenia (w bazie) dla pary — z AssetPairs 'ordermin'.
    None gdy nieznany (pula fallback / cache pusty). Kraken ODRZUCA zlecenia poniżej
    tego progu -> używamy do bramek rozmiaru, żeby nie słać sub-min i nie gubić
    realizacji zysku (fix#1/#2)."""
    base = _norm_base((symbol or "").split("/")[0])
    return _DYN_PAIR_MIN.get(base)


def round_price(symbol: str, price: float) -> float | None:
    """Zaokrągl cenę do precyzji pary Kraken (inaczej AddOrder odrzuca limit
    'Invalid price'). None gdy precyzja nieznana -> wołający robi market."""
    dec = pair_price_decimals(symbol)
    if dec is None or price <= 0:
        return None
    return round(price, dec)


def _norm_base(base: str) -> str:
    b = (base or "").upper()
    return _BASE_ALIAS.get(b, b)


def _base_of(symbol: str) -> str:
    """'BTC/USD' / 'BTC/EUR' / 'BTC' -> 'BTC'."""
    return (symbol or "").upper().split("/")[0]


def _fmt_num(x: float) -> str:
    """Liczba jako łańcuch dziesiętny bez notacji naukowej (Kraken odrzuca 1e-05).
    Do 10 miejsc po przecinku, obcięte zera końcowe."""
    s = f"{float(x):.10f}".rstrip("0").rstrip(".")
    return s or "0"


def to_kraken_pair(symbol: str) -> str | None:
    """Symbol uniwersum -> para Kraken EUR (altname), albo None gdy nieznana.
    Najpierw dynamiczna mapa (cały rynek EUR), potem zahardkodowany fallback (7)."""
    base = _norm_base(_base_of(symbol))
    return _DYN_PAIRS.get(base) or UNIVERSE_TO_KRAKEN.get(base)


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


def parse_ticker_quote(result: dict) -> tuple[float, float] | None:
    """Kraken Ticker result -> (bid, ask) z pól 'b'[0]/'a'[0]. mech#5: potrzebne do
    liczenia spreadu PRZED wejściem na żywej kasie. None gdy brak/0 (fail-open wyżej)."""
    for _pair, info in (result or {}).items():
        try:
            bid = float(info["b"][0])
            ask = float(info["a"][0])
            if bid > 0 and ask > 0:
                return (bid, ask)
            return None
        except (TypeError, ValueError, KeyError, IndexError):
            return None
    return None


class KrakenError(RuntimeError):
    pass


class KrakenClient:
    """Read-side klient Kraken. `transport(method, url, headers, body) -> dict`
    jest wstrzykiwany (domyślnie urllib przez proxy agenta). Klucz/sekret z env."""

    def __init__(self, key: str = "", secret: str = "", transport: Callable | None = None,
                 live_trading: bool = False):
        self._key = key
        self._secret = secret
        self._transport = transport or _default_transport
        self._nonce_base = int(time.time() * 1000)
        # Gdy False (DOMYŚLNIE): egzekucja przez silnik idzie w DRY-RUN (validate),
        # zero realnych zleceń — paper-on-Kraken. True tylko po dowodzie paper.
        self._live = bool(live_trading)

    @classmethod
    def from_env(cls, transport: Callable | None = None, live_trading: bool = False) -> KrakenClient:
        # Najpierw singleton Settings (tam broker_credentials nakłada override z panelu
        # „Podłącz Kraken"), potem surowy env. Dzięki temu klucz wpięty w panelu działa
        # od zaraz, bez restartu i bez dostępu do serwera.
        key = secret = ""
        try:
            from app.config import get_settings
            s = get_settings()
            key = (getattr(s, "kraken_api_key", "") or "").strip()
            secret = (getattr(s, "kraken_api_secret", "") or "").strip()
        except Exception:  # noqa: BLE001 — brak kontekstu Settings (np. test) => env
            pass
        key = key or os.getenv("KRAKEN_API_KEY", "")
        secret = secret or os.getenv("KRAKEN_API_SECRET", "")
        return cls(key, secret, transport, live_trading=live_trading)

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

    def get_quote(self, symbol: str) -> tuple[float, float] | None:
        """(bid, ask) z Ticker — do liczenia spreadu przed wejściem (mech#5). None
        gdy brak pary/danych (wołający traktuje jako fail-open: nie blokuje wejścia)."""
        pair = to_kraken_pair(symbol)
        if not pair:
            return None
        try:
            return parse_ticker_quote(self._public("/0/public/Ticker", {"pair": pair}))
        except Exception:  # noqa: BLE001 — best-effort, spread to filtr ochronny
            return None

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

    # ---- powierzchnia zgodna z AlpacaClient (drop-in dla nogi krypto) ----
    def is_tradable(self, symbol: str) -> bool:
        """Czy para jest w naszym uniwersum Kraken EUR (mapowalna)."""
        return to_kraken_pair(symbol) is not None

    def min_order_notional(self, symbol: str, price: float) -> float | None:
        """Minimalny NOTIONAL zlecenia w EUR = ordermin (baza) × cena. None gdy
        ordermin nieznany (pula fallback / cache pusty) -> wołający bierze własną
        podłogę. Służy bramkom rozmiaru (fix#1/#2), żeby nie słać sub-min zleceń."""
        omin = pair_ordermin(symbol)
        if omin is None or not price or price <= 0:
            return None
        return omin * price

    def list_crypto_symbols(self) -> list[str]:
        """CAŁY rynek EUR Krakena (setki par), posortowany po płynności (obrót 24h),
        w formie '<BASE>/EUR'. To jest pula dla skanera — on zawęża ją do max_scan
        najpłynniejszych, rankuje momentum i wybiera TOP-K. Dynamiczne z publicznego
        AssetPairs + Ticker (jeden call), cache 30 min. Zasila też to_kraken_pair.
        Fallback przy awarii: zahardkodowane 7 (UNIVERSE_TO_KRAKEN)."""
        global _DYN_PAIRS, _DYN_ORDER, _DYN_AT, _DYN_PAIR_DEC, _DYN_PAIR_MIN
        now = time.time()
        if _DYN_ORDER and (now - _DYN_AT) < _DYN_TTL_SEC:
            return list(_DYN_ORDER)
        try:
            pairs = self._public("/0/public/AssetPairs", {})
            amap: dict[str, str] = {}  # baza -> altname
            decmap: dict[str, int] = {}  # baza -> pair_decimals (precyzja ceny, mech#2)
            minmap: dict[str, float] = {}  # baza -> ordermin (min wolumen, fix#1/#2)
            for pid, info in pairs.items():
                if info.get("status") != "online":
                    continue
                ws = info.get("wsname") or ""
                if "/" not in ws:
                    continue
                base, quote = ws.split("/", 1)
                if quote != "EUR":
                    continue
                nb = _norm_base(base)
                if nb in _STABLE_FIAT:
                    continue
                amap[nb] = info.get("altname") or pid
                try:
                    decmap[nb] = int(info.get("pair_decimals"))
                except (TypeError, ValueError):
                    pass
                try:
                    minmap[nb] = float(info.get("ordermin"))
                except (TypeError, ValueError):
                    pass
            if not amap:
                raise KrakenError("AssetPairs: zero par EUR")
            # Ranking płynności: obrót 24h = ostatnia cena * wolumen (jeden call Ticker).
            order_bases = sorted(amap.keys())  # fallback alfabetyczny
            try:
                alt_to_base = {alt: b for b, alt in amap.items()}
                tick = self._public("/0/public/Ticker", {})
                turnover: dict[str, float] = {}
                for tid, tinfo in tick.items():
                    b = alt_to_base.get(tid)
                    if b is None:
                        continue
                    try:
                        last = float((tinfo.get("c") or [0])[0])
                        vol = float((tinfo.get("v") or [0, 0])[1])
                        turnover[b] = last * vol
                    except (TypeError, ValueError, IndexError):
                        continue
                order_bases = sorted(amap.keys(), key=lambda b: turnover.get(b, 0.0), reverse=True)
            except Exception:  # noqa: BLE001 — brak Ticker => zostaje ranking alfabetyczny
                pass
            _DYN_PAIRS = amap
            _DYN_PAIR_DEC = decmap
            _DYN_PAIR_MIN = minmap
            _DYN_ORDER = [f"{b}/EUR" for b in order_bases]
            _DYN_AT = now
            return list(_DYN_ORDER)
        except Exception:  # noqa: BLE001 — awaria => fallback na zahardkodowane 7
            import logging
            logging.getLogger(__name__).warning(
                "Kraken: dynamiczne uniwersum nieudane — fallback na 7", exc_info=True
            )
            return [f"{b}/EUR" for b in UNIVERSE_TO_KRAKEN]

    def place_order_for_session(
        self, symbol: str, side: str, *, session: str = "regular",
        usdt_amount: float | None = None, quantity: float | None = None,
        prefer_limit: bool = False, limit_buffer_pct: float = 0.0, validate: bool | None = None,
    ) -> KrakenOrderResult:
        """Egzekucja zgodna z AlpacaClient.place_order_for_session (krypto 24/7 = zawsze
        'regular'). `usdt_amount` traktujemy jako kwotę EUR. validate=None (gdy woła silnik)
        => dry-run, O ILE klient nie jest w trybie live_trading. Dry-run zwraca SYNTETYCZNY
        fill po bieżącej cenie (paper-on-Kraken), bez realnego zlecenia."""
        if validate is None:
            validate = not self._live
        price = self.get_price(symbol) or 0.0
        if quantity is not None:
            qty = abs(quantity)
        elif usdt_amount is not None and price > 0:
            qty = abs(usdt_amount) / price
        else:
            raise KrakenError("place_order_for_session: brak quantity i usdt_amount/ceny")
        # mech#2: marketable-LIMIT dla WEJŚĆ (prefer_limit) — cena limitu przez księgę
        # (BUY: powyżej, SELL: poniżej o bufor), więc zlecenie wypełnia się od razu, ale
        # NIE gorzej niż limit => twardy sufit poślizgu (ważne na cienkich monetach).
        # Fallback na MARKET, gdy: brak prefer_limit, brak ceny, albo nieznana precyzja
        # pary (inaczej Kraken odrzuca 'Invalid price'). Wyjścia/stopy wołają bez
        # prefer_limit -> zostają market (gwarantowane, szybkie wyjście).
        ordertype = "market"
        limit_price: float | None = None
        if prefer_limit and price > 0:
            buf = max(0.0, float(limit_buffer_pct or 0.0)) / 100.0
            raw = price * (1.0 + buf) if side.lower() == "buy" else price * (1.0 - buf)
            limit_price = round_price(symbol, raw)
            if limit_price and limit_price > 0:
                ordertype = "limit"
        resp = self.place_order(symbol, side, qty, ordertype=ordertype, price=limit_price, validate=validate)
        txids = (resp.get("txid") or []) if isinstance(resp, dict) else []
        oid = txids[0] if txids else ("dry-run" if validate else "kraken")
        fill_price = limit_price if ordertype == "limit" else price
        return KrakenOrderResult(oid, symbol, side, qty, fill_price, qty * fill_price)


def _default_transport(method: str, url: str, headers: dict, body: str | None) -> dict:
    """Domyślny transport: urllib przez proxy agenta + CA bundle. Izolowany, żeby
    testy mogły go podmienić. Zwraca sparsowany JSON Kraken."""
    import json
    import ssl
    import urllib.request

    # CA: na serwerze produkcyjnym używamy SYSTEMOWEGO zaufania (cert Kraken jest
    # publiczny). Custom CA (proxy sesji cloud) tylko GDY plik istnieje — inaczej
    # hardcode ścieżki wywracał każde wywołanie Kraken na serwerze (SSL/FileNotFound).
    ca = os.getenv("KRAKEN_CA_BUNDLE") or "/root/.ccr/ca-bundle.crt"
    try:
        ctx = ssl.create_default_context(cafile=ca)
    except (FileNotFoundError, ssl.SSLError, OSError):
        ctx = ssl.create_default_context()
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    handlers = [urllib.request.HTTPSHandler(context=ctx)]
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"https": proxy, "http": proxy}))
    opener = urllib.request.build_opener(*handlers)
    data = body.encode() if body else None
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "gieldarek", **headers}, method=method)
    with opener.open(req, timeout=30) as r:
        return json.load(r)
