"""Crypto news headlines aggregated from many free sources so a single
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

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"
REQUEST_TIMEOUT = 6.0

# Free, keyless RSS feeds from well-known crypto news outlets. Each
# contributes at most a handful of headlines (see PER_SOURCE_LIMIT below) --
# the point is breadth of sources, not volume, to keep prompt/token cost in
# check as more sources get added.
RSS_FEEDS: list[tuple[str, str]] = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("The Block", "https://www.theblock.co/rss.xml"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/feed"),
    ("CryptoSlate", "https://cryptoslate.com/feed/"),
    ("NewsBTC", "https://www.newsbtc.com/feed/"),
    ("CryptoBriefing", "https://cryptobriefing.com/feed/"),
]
PER_SOURCE_LIMIT = 3
REDDIT_URL = "https://www.reddit.com/r/CryptoCurrency/top.json"
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


def _get_rss(source: str, url: str, limit: int) -> list[dict]:
    try:
        resp = httpx.get(url, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return _parse_rss(source, resp.text, limit)
    except Exception:
        logger.warning("Failed to fetch RSS feed %s, skipping it", source, exc_info=True)
        return []


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
                "source": "Reddit r/CryptoCurrency",
            }
            for c in children
            if c.get("data", {}).get("title")
        ]
    except Exception:
        logger.warning("Failed to fetch Reddit r/CryptoCurrency, skipping it", exc_info=True)
        return []


class NewsClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    def _get_cryptopanic(self, currencies: list[str], limit: int) -> list[dict]:
        if not self._settings.cryptopanic_api_key:
            return []
        params = {
            "auth_token": self._settings.cryptopanic_api_key,
            "currencies": ",".join(currencies),
            "public": "true",
        }
        try:
            resp = httpx.get(CRYPTOPANIC_URL, params=params, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            results = resp.json().get("results", [])[:limit]
            return [
                {
                    "title": item.get("title", ""),
                    "published_at": item.get("published_at", ""),
                    "source": item.get("source", {}).get("title", "CryptoPanic"),
                }
                for item in results
            ]
        except Exception:
            logger.warning("Failed to fetch CryptoPanic headlines, continuing without them", exc_info=True)
            return []

    def get_headlines(self, currencies: list[str], limit: int = 25) -> list[dict]:
        with ThreadPoolExecutor(max_workers=len(RSS_FEEDS) + 2) as pool:
            futures = [pool.submit(self._get_cryptopanic, currencies, 5)]
            futures += [pool.submit(_get_rss, name, url, PER_SOURCE_LIMIT) for name, url in RSS_FEEDS]
            futures.append(pool.submit(_get_reddit, 5))

            headlines: list[dict] = []
            for future in futures:
                try:
                    headlines.extend(future.result())
                except Exception:
                    logger.warning("A news source future raised unexpectedly, skipping it", exc_info=True)

        return headlines[:limit]
