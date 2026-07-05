"""Free, keyless macro/sentiment context for US equities, aggregated from
several public data endpoints (major index moves, VIX as a fear proxy, top
gainers/losers). Each source degrades independently to None/empty on
failure, mirroring news_client.py, so the trading engine never hard-depends
on any one of them."""

import logging
from concurrent.futures import ThreadPoolExecutor

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8.0
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SCREENER_URL = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
# Yahoo blocks the default httpx User-Agent on some endpoints.
YAHOO_HEADERS = {"User-Agent": "Mozilla/5.0 (GielDarek-trading-bot/1.0)"}

# Major US indices -- used to describe the broad market's direction, since a
# single stock's move often just tracks (or diverges meaningfully from) these.
INDEX_SYMBOLS = {"^GSPC": "sp500", "^IXIC": "nasdaq", "^DJI": "dow"}
# CBOE Volatility Index -- standard proxy for market-wide fear/complacency,
# the equity-market equivalent of the crypto Fear & Greed index.
VIX_SYMBOL = "^VIX"


def _get_index_change_pct(symbol: str) -> float | None:
    try:
        resp = httpx.get(
            YAHOO_CHART_URL.format(symbol=symbol),
            params={"range": "5d", "interval": "1d"},
            headers=YAHOO_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        meta = resp.json()["chart"]["result"][0]["meta"]
        prev_close = meta["chartPreviousClose"]
        current = meta["regularMarketPrice"]
        if not prev_close:
            return None
        return round((current - prev_close) / prev_close * 100, 2)
    except Exception:
        logger.warning("Failed to fetch Yahoo Finance chart data for %s, continuing without it", symbol, exc_info=True)
        return None


def _get_indices_context() -> dict:
    with ThreadPoolExecutor(max_workers=len(INDEX_SYMBOLS)) as pool:
        results = {name: pool.submit(_get_index_change_pct, symbol) for symbol, name in INDEX_SYMBOLS.items()}
        return {f"{name}_change_pct": future.result() for name, future in results.items()}


def _get_vix_level() -> float | None:
    try:
        resp = httpx.get(
            YAHOO_CHART_URL.format(symbol=VIX_SYMBOL),
            params={"range": "1d", "interval": "1d"},
            headers=YAHOO_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        meta = resp.json()["chart"]["result"][0]["meta"]
        return round(float(meta["regularMarketPrice"]), 2)
    except Exception:
        logger.warning("Failed to fetch VIX level, continuing without it", exc_info=True)
        return None


def _get_screener(scr_id: str) -> list[dict]:
    try:
        resp = httpx.get(
            YAHOO_SCREENER_URL,
            params={"scrIds": scr_id, "count": 5},
            headers=YAHOO_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        quotes = resp.json()["finance"]["result"][0]["quotes"]
        return [
            {"symbol": q["symbol"], "change_pct": round(q.get("regularMarketChangePercent", 0.0), 1)}
            for q in quotes
        ]
    except Exception:
        logger.warning("Failed to fetch Yahoo Finance screener %s, continuing without it", scr_id, exc_info=True)
        return []


class MarketContextClient:
    def get_market_context(self) -> dict:
        with ThreadPoolExecutor(max_workers=4) as pool:
            indices = pool.submit(_get_indices_context)
            vix = pool.submit(_get_vix_level)
            gainers = pool.submit(_get_screener, "day_gainers")
            losers = pool.submit(_get_screener, "day_losers")

            context: dict = {
                **indices.result(),
                "vix_level": vix.result(),
                "top_gainers_today": gainers.result(),
                "top_losers_today": losers.result(),
            }
        return context
