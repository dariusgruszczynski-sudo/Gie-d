"""Darmowy, bezkluczowy kontekst STRUKTURY RYNKU KRYPTO -- odpowiednik
market_context.py dla akcji, ale zamiast indeksów/VIX czyta sygnały specyficzne
dla krypto, które bywają informatywne (szczególnie jako KONTRARIAŃSKIE w
ekstremum): funding rate, zmiana open interest, long/short ratio oraz indeks
Fear & Greed. BTC traktujemy jak barometr całego rynku krypto (tak jak SPX/VIX
dla akcji).

Każde źródło degraduje się NIEZALEŻNIE do None przy błędzie (jak news_client /
market_context), więc cykl handlowy nigdy nie zależy twardo od żadnego z nich.
Zapisywane w global_context -> decision.market_context_snapshot, więc wpada do
logu/pamięci automatycznie i -- gdy właściciel włączy LLM -- do promptu.

Uwaga: te endpointy są publiczne, ale pobierane na PRODZIE (VPS ma sieć);
w izolowanym sandboxie proxy może je blokować -> wtedy po prostu None."""

import logging
from concurrent.futures import ThreadPoolExecutor

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8.0
# Binance USDT-perp jako najpłynniejszy barometr derywatów krypto.
BINANCE_FAPI = "https://fapi.binance.com"
FNG_URL = "https://api.alternative.me/fng/"
HEADERS = {"User-Agent": "GielDarek-crypto-bot/1.0"}


def _funding_rate_pct(symbol: str = "BTCUSDT") -> float | None:
    """Bieżący funding rate (%). Dodatni = longi płacą shortom (tłum long);
    skrajnie dodatni bywa sygnałem kontrariańskim (ryzyko long-squeeze)."""
    try:
        r = httpx.get(f"{BINANCE_FAPI}/fapi/v1/premiumIndex", params={"symbol": symbol},
                      headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            return None
        return round(float(r.json()["lastFundingRate"]) * 100, 4)
    except Exception:
        logger.info("Funding rate niedostępny (%s)", symbol, exc_info=True)
        return None


def _oi_change_pct(symbol: str = "BTCUSDT") -> float | None:
    """Zmiana % open interest w ostatnich ~24h (1h×24). Rosnące OI + rosnąca
    cena = zdrowy trend; rosnące OI + płaska/spadająca cena = napięcie."""
    try:
        r = httpx.get(f"{BINANCE_FAPI}/futures/data/openInterestHist",
                      params={"symbol": symbol, "period": "1h", "limit": 24},
                      headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            return None
        rows = r.json()
        if len(rows) < 2:
            return None
        first = float(rows[0]["sumOpenInterest"])
        last = float(rows[-1]["sumOpenInterest"])
        return round((last - first) / first * 100, 2) if first > 0 else None
    except Exception:
        logger.info("Open interest niedostępny (%s)", symbol, exc_info=True)
        return None


def _long_short_ratio(symbol: str = "BTCUSDT") -> float | None:
    """Globalny long/short account ratio. >1 = więcej kont long; skrajne
    wartości bywają kontrariańskie (tłum zwykle po złej stronie w ekstremum)."""
    try:
        r = httpx.get(f"{BINANCE_FAPI}/futures/data/globalLongShortAccountRatio",
                      params={"symbol": symbol, "period": "1h", "limit": 1},
                      headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            return None
        rows = r.json()
        return round(float(rows[-1]["longShortRatio"]), 2) if rows else None
    except Exception:
        logger.info("Long/short ratio niedostępny (%s)", symbol, exc_info=True)
        return None


def _fear_greed() -> tuple[int, str] | None:
    """Crypto Fear & Greed Index (0-100) + etykieta. Skrajna chciwość =
    ostrożność, skrajny strach = okazje (kontrarianizm)."""
    try:
        r = httpx.get(FNG_URL, params={"limit": 1}, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        if r.status_code >= 400:
            return None
        d = r.json()["data"][0]
        return int(d["value"]), str(d["value_classification"])
    except Exception:
        logger.info("Fear&Greed niedostępny", exc_info=True)
        return None


def get_crypto_structure() -> dict:
    """Zbiera (równolegle) strukturę rynku krypto. Zwraca dict tylko z tym, co
    się udało -- brakujące pola po prostu nie wchodzą. Nigdy nie rzuca."""
    out: dict = {}
    try:
        with ThreadPoolExecutor(max_workers=4) as ex:
            f_funding = ex.submit(_funding_rate_pct)
            f_oi = ex.submit(_oi_change_pct)
            f_ls = ex.submit(_long_short_ratio)
            f_fng = ex.submit(_fear_greed)
            funding, oi, ls, fng = f_funding.result(), f_oi.result(), f_ls.result(), f_fng.result()
    except Exception:
        logger.warning("Pobieranie struktury rynku krypto padło w całości", exc_info=True)
        return out
    if funding is not None:
        out["btc_funding_rate_pct"] = funding
    if oi is not None:
        out["btc_open_interest_change_24h_pct"] = oi
    if ls is not None:
        out["btc_long_short_ratio"] = ls
    if fng is not None:
        out["fear_greed"] = fng[0]
        out["fear_greed_label"] = fng[1]
    return out
