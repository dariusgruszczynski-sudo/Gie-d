"""OHLC candle provider for the eToro venue.

eToro's public API exposes live rates but NO candle/history endpoint (verified:
27 path/param variants all 404), so technical indicators (RSI/MACD/SMA) can't
be computed from eToro itself. Crypto and FX prices are fungible across venues,
so candles are pulled from Yahoo Finance's chart API (keyless, covers both
crypto `BTC-USD` and forex `EURUSD=X`). Degrades to an empty series on any
failure -- the engine already treats missing history as insufficient_data and
keeps trading on price/news, so this is never fatal."""

import logging

import httpx

logger = logging.getLogger(__name__)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
REQUEST_TIMEOUT = 10.0
# Yahoo needs a browser-ish UA or it 429s/403s.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GielDarek/1.0)"}
_INTERVAL = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "1h", "1d": "1d"}
# Enough history for a 200-bar indicator window at each interval.
_RANGE = {"1m": "5d", "5m": "1mo", "15m": "1mo", "1h": "3mo", "1d": "2y"}

# Our eToro whitelist symbol -> Yahoo symbol (crypto is <COIN>-USD, forex <PAIR>=X).
YAHOO_SYMBOL = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
    "BCH": "BCH-USD",
    "LTC": "LTC-USD",
    "XRP": "XRP-USD",
    "ADA": "ADA-USD",
    "DOGE": "DOGE-USD",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCHF": "CHF=X",
    "USDCAD": "CAD=X",
}


def get_candles(symbol: str, interval: str = "1h", limit: int = 200) -> list[list]:
    """Returns rows [open_time_ms, open, high, low, close, volume] oldest-first,
    matching the shape AlpacaClient.get_klines yields (close read from index 4
    by technical_indicators.py)."""
    ysym = YAHOO_SYMBOL.get(symbol.upper())
    if not ysym:
        logger.warning("No Yahoo mapping for eToro symbol %s, no candles", symbol)
        return []
    try:
        resp = httpx.get(
            YAHOO_CHART_URL.format(symbol=ysym),
            params={"interval": _INTERVAL.get(interval, "1h"), "range": _RANGE.get(interval, "3mo")},
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        result = resp.json()["chart"]["result"][0]
        timestamps = result.get("timestamp") or []
        quote = result["indicators"]["quote"][0]
        opens, highs, lows, closes, vols = (
            quote.get("open") or [],
            quote.get("high") or [],
            quote.get("low") or [],
            quote.get("close") or [],
            quote.get("volume") or [],
        )
        rows: list[list] = []
        for i, ts in enumerate(timestamps):
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]
            if None in (o, h, l, c):  # Yahoo pads gaps with nulls
                continue
            v = vols[i] if i < len(vols) and vols[i] is not None else 0
            rows.append([ts * 1000, o, h, l, c, v])
        return rows[-limit:]
    except Exception:
        logger.warning("Yahoo candles fetch failed for %s (%s), returning empty", symbol, ysym, exc_info=True)
        return []
