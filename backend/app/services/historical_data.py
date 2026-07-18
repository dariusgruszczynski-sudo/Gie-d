"""Long-range (multi-year) DAILY price history from Yahoo Finance -- free,
keyless, no history-window limit. The free Alpaca/IEX feed only reaches back a
few years, which starves a backtest of the market REGIMES that matter most
(2008 financial crisis, 2020 COVID crash, 2022 rate-hike bear market) -- a
backtest that only sees one long bull run can't tell you whether the strategy
protects capital when it counts. Same defensive pattern as market_context.py:
any failure degrades to an empty series instead of raising, so one bad symbol
never aborts a whole multi-symbol backtest."""

import logging
import time

import httpx

logger = logging.getLogger(__name__)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
REQUEST_TIMEOUT = 15.0
# Yahoo blocks the default httpx User-Agent on some endpoints.
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GielDarek/1.0)"}
# Politeness delay between sequential requests when fetching a whole whitelist
# -- avoids tripping Yahoo's rate limiting on ~20+ symbols in a row.
BATCH_DELAY_SECONDS = 0.3
SECONDS_PER_YEAR = 365.25 * 86400

# Our extended whitelist ("BTCUSD") -> Yahoo chart symbol ("BTC-USD"), needed
# because Alpaca's own extended market data doesn't reach back far enough for a
# multi-year regime backtest (Alpaca extended only started ~2021-2022). Yahoo's
# extended history goes back to ~2014 (BTC) / 2017 (ETH), which is exactly the
# multi-year calibration a backtest needs.
EXTENDED_YAHOO_SYMBOL = {
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "SOLUSD": "SOL-USD",
    "LTCUSD": "LTC-USD",
    "BCHUSD": "BCH-USD",
    "DOGEUSD": "DOGE-USD",
    "LINKUSD": "LINK-USD",
    "AVAXUSD": "AVAX-USD",
    "ADAUSD": "ADA-USD",
    "DOTUSD": "DOT-USD",
    # Uniswap trades as UNI7083-USD on Yahoo (plain "UNI" was already taken).
    "UNIUSD": "UNI7083-USD",
    "AAVEUSD": "AAVE-USD",
    "XRPUSD": "XRP-USD",
    "SHIBUSD": "SHIB-USD",
}


def _yahoo_symbol(symbol: str) -> str:
    """Map a extended whitelist ticker to its Yahoo chart symbol so the backtest
    can pull deep extended history (BTCUSD -> BTC-USD). A plain US-equity ticker
    isn't in the map and passes through unchanged. Without this a extended
    symbol was sent to Yahoo verbatim and returned nothing, so the extended
    venue could never be backtested at all."""
    return EXTENDED_YAHOO_SYMBOL.get(symbol.upper(), symbol)


def get_daily_history(symbol: str, years: int = 20) -> list[list]:
    """Returns rows [open_time_ms, open, high, low, close, volume] oldest-first,
    covering up to `years` years of DAILY bars.

    Uses explicit period1/period2 (unix seconds) rather than range=max: with
    range=max Yahoo silently DOWNSAMPLES a 20-year window to MONTHLY bars (~241
    points), which is useless for a strategy whose stops/indicators are tuned on
    daily data. period1/period2 + interval=1d returns true daily bars. Still
    filters client-side to the requested window as a belt-and-suspenders guard.

    Extended tickers are mapped to their Yahoo symbol (BTCUSD -> BTC-USD) so the
    extended whitelist can be backtested on the same deep-history engine as stocks."""
    now = int(time.time())
    period1 = now - int(years * SECONDS_PER_YEAR)
    try:
        resp = httpx.get(
            YAHOO_CHART_URL.format(symbol=_yahoo_symbol(symbol)),
            params={"period1": period1, "period2": now, "interval": "1d"},
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
    except Exception:
        logger.warning("Yahoo daily history fetch failed for %s, returning empty", symbol, exc_info=True)
        return []

    cutoff = time.time() - years * SECONDS_PER_YEAR
    rows: list[list] = []
    for i, ts in enumerate(timestamps):
        if ts < cutoff:
            continue
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]
        if None in (o, h, l, c):  # Yahoo pads holidays/gaps with nulls
            continue
        v = vols[i] if i < len(vols) and vols[i] is not None else 0
        rows.append([ts * 1000, o, h, l, c, v])
    return rows


def get_history_for_symbols(
    symbols: list[str], years: int = 20, *, delay: float = BATCH_DELAY_SECONDS
) -> dict[str, list[list]]:
    """Best-effort fetch for a whole whitelist -- a symbol that fails or has no
    Yahoo history is simply omitted, never aborts the batch. Fetched
    sequentially with a small delay between requests (politeness/rate-limit
    guard for ~20+ symbols in one run)."""
    out: dict[str, list[list]] = {}
    for i, sym in enumerate(symbols):
        if i > 0 and delay > 0:
            time.sleep(delay)
        rows = get_daily_history(sym, years=years)
        if rows:
            out[sym] = rows
    return out
