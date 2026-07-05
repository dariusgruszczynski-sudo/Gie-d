"""Market news headlines aggregated from many free sources so a single
outlet's spin or an outage never dominates/blocks what Claude sees. Each
source is fetched in parallel (bounded per-request timeout) and degrades
independently to nothing on failure -- the trading engine never hard-depends
on any one of them."""

import logging
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 6.0

# Free, keyless RSS feeds from well-known financial news outlets. Each
# contributes at most a handful of headlines (see PER_SOURCE_LIMIT below) --
# the point is breadth of sources, not volume, to keep prompt/token cost in
# check as more sources get added.
RSS_FEEDS: list[tuple[str, str]] = [
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("CNBC Markets", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("Investing.com", "https://www.investing.com/rss/news.rss"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Seeking Alpha", "https://seekingalpha.com/market_currents.xml"),
    ("Business Insider Markets", "https://markets.businessinsider.com/rss/news"),
]
PER_SOURCE_LIMIT = 3
# Per-ticker headlines (keyless) so news specific to symbols on the whitelist
# reaches Claude even when general market feeds don't mention them.
YAHOO_TICKER_RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"
PER_TICKER_LIMIT = 3
REDDIT_URL = "https://www.reddit.com/r/stocks/top.json"
# Reddit blocks the default httpx User-Agent -- needs a descriptive one.
REDDIT_HEADERS = {"User-Agent": "GielDarek-trading-bot/1.0"}


def _parse_rss(source: str, xml_text: str, limit: int) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")[:limit]
    out = []
    for item in items:
        title = item.findtext("title") or ""
        pub_date = item.findtext("pubDate") or ""
        if title:
            out.append({"title": title.strip(), "published_at": pub_date, "source": source})
    return out


def _get_rss(source: str, url: str, limit: int, params: dict | None = None) -> list[dict]:
    try:
        resp = httpx.get(url, params=params, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return _parse_rss(source, resp.text, limit)
    except Exception:
        logger.warning("Failed to fetch RSS feed %s, skipping it", source, exc_info=True)
        return []


def _get_ticker_headlines(ticker: str, limit: int) -> list[dict]:
    return _get_rss(
        f"Yahoo Finance ({ticker})",
        YAHOO_TICKER_RSS_URL,
        limit,
        params={"s": ticker, "region": "US", "lang": "en-US"},
    )


def _get_reddit(limit: int) -> list[dict]:
    try:
        resp = httpx.get(
            REDDIT_URL,
            params={"limit": limit, "t": "day"},
            headers=REDDIT_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        children = resp.json().get("data", {}).get("children", [])
        return [
            {
                "title": c["data"].get("title", ""),
                "published_at": "",
                "source": "Reddit r/stocks",
            }
            for c in children
            if c.get("data", {}).get("title")
        ]
    except Exception:
        logger.warning("Failed to fetch Reddit r/stocks, skipping it", exc_info=True)
        return []


class NewsClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    def get_headlines(self, tickers: list[str], limit: int = 25) -> list[dict]:
        with ThreadPoolExecutor(max_workers=len(RSS_FEEDS) + len(tickers) + 1) as pool:
            futures = [pool.submit(_get_rss, name, url, PER_SOURCE_LIMIT) for name, url in RSS_FEEDS]
            futures += [pool.submit(_get_ticker_headlines, ticker, PER_TICKER_LIMIT) for ticker in tickers]
            futures.append(pool.submit(_get_reddit, 5))

            headlines: list[dict] = []
            for future in futures:
                try:
                    headlines.extend(future.result())
                except Exception:
                    logger.warning("A news source future raised unexpectedly, skipping it", exc_info=True)

        return headlines[:limit]
