"""Market news headlines aggregated from a broad set of free sources so a
single outlet's spin or an outage never dominates/blocks what Claude sees.
Each source is fetched in parallel (bounded per-request timeout) and
degrades independently to nothing on failure -- the trading engine never
hard-depends on any one of them. Results are interleaved round-robin across
sources before truncating to `limit`, so a handful of prolific feeds can't
crowd out the rest (e.g. per-ticker headlines or SEC filings) once capped."""

import logging
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from itertools import zip_longest

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 6.0

# Free, keyless RSS/Atom feeds curated for swing-trading US stocks/ETFs:
# general market news, sector coverage relevant to a tech-heavy whitelist
# (AAPL/NVDA/QQQ), and SEC filings for material corporate events. Each
# contributes at most a handful of headlines (see PER_SOURCE_LIMIT below) --
# the point is breadth of sources, not volume, to keep prompt/token cost in
# check as more sources get added.
RSS_FEEDS: list[tuple[str, str]] = [
    # General market news
    ("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("CNBC Markets", "https://www.cnbc.com/id/20910258/device/rss/rss.html"),
    ("Investing.com", "https://www.investing.com/rss/news.rss"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Seeking Alpha", "https://seekingalpha.com/market_currents.xml"),
    ("Business Insider Markets", "https://markets.businessinsider.com/rss/news"),
    ("WSJ Markets", "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"),
    ("Bloomberg Markets", "https://feeds.bloomberg.com/markets/news.rss"),
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("Forbes Markets", "https://www.forbes.com/markets/feed/"),
    ("Barron's", "https://www.barrons.com/feed/rssheadlines"),
    ("The Motley Fool", "https://www.fool.com/feeds/index.aspx"),
    ("Zacks", "https://www.zacks.com/rss/rss_news_stock.php"),
    ("Benzinga", "https://www.benzinga.com/feed"),
    ("TheStreet", "https://www.thestreet.com/.rss/full/"),
    ("Kiplinger", "https://www.kiplinger.com/rss"),
    ("Nasdaq", "https://www.nasdaq.com/feed/rssoutbound?category=Stocks"),
    ("ETF.com", "https://www.etf.com/rss"),
    ("Investopedia", "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline"),
    ("StockTitan", "https://www.stocktitan.net/rss"),
    # Sector coverage relevant to a tech-heavy whitelist (AAPL, NVDA, QQQ)
    ("TechCrunch", "https://techcrunch.com/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    # Regulatory -- material corporate events / insider activity that
    # generic news coverage often lags or misses entirely
    ("SEC EDGAR 8-K filings", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=40&output=atom"),
    ("SEC EDGAR Form 4 (insider trades)", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb=&owner=include&count=40&output=atom"),
    # Crypto -- the 24/7 crypto venue trades BTC/ETH/..., driven far more by
    # crypto-native flow (ETF news, on-chain, exchange/regulatory events) than
    # by the general stock feeds above.
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("Cointelegraph", "https://cointelegraph.com/rss"),
    ("Decrypt", "https://decrypt.co/feed"),
    ("The Block", "https://www.theblock.co/rss.xml"),
    ("CryptoSlate", "https://cryptoslate.com/feed/"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
    ("NewsBTC", "https://www.newsbtc.com/feed/"),
    ("Bitcoinist", "https://bitcoinist.com/feed/"),
    ("CoinJournal", "https://coinjournal.net/news/feed/"),
    ("Investing.com Crypto", "https://www.investing.com/rss/news_301.rss"),
]
PER_SOURCE_LIMIT = 3
# Per-ticker headlines (keyless) so news specific to symbols on the whitelist
# reaches Claude even when general market feeds don't mention them. Google
# News RSS -- the old Yahoo per-ticker feed (feeds.finance.yahoo.com) started
# returning 404 for every symbol (verified in production logs, 07/2026),
# which silently killed the news trigger.
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
PER_TICKER_LIMIT = 3
# Broad retail-sentiment cross-section: measured (r/stocks, r/investing) and
# the deliberately noisier, momentum/meme-driven r/wallstreetbets -- useful
# as a crowd-positioning signal precisely because it's unfiltered, not
# despite it. Bounded to a few headlines each like every other source, so it
# can't dominate the prompt.
REDDIT_SUBREDDITS = [
    "stocks",
    "investing",
    "wallstreetbets",
    # Crypto crowd-positioning for the 24/7 venue.
    "CryptoCurrency",
    "Bitcoin",
    "ethereum",
]
PER_SUBREDDIT_LIMIT = 5
# Reddit blocks the default httpx User-Agent -- needs a descriptive one.
REDDIT_HEADERS = {"User-Agent": "GielDarek-trading-bot/1.0"}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_feed(source: str, xml_text: str, limit: int) -> list[dict]:
    """Handles both RSS 2.0 (<item>/<title>/<pubDate>) and Atom
    (<entry>/<title>/<updated>) by matching on local tag names, since SEC
    EDGAR's filing feeds are Atom while most news feeds are RSS 2.0."""
    root = ET.fromstring(xml_text)
    entries = [el for el in root.iter() if _local_name(el.tag) in ("item", "entry")][:limit]
    out = []
    for entry in entries:
        title = ""
        published_at = ""
        for child in entry:
            name = _local_name(child.tag)
            if name == "title" and not title:
                title = (child.text or "").strip()
            elif name in ("pubDate", "updated", "published") and not published_at:
                published_at = (child.text or "").strip()
        if title:
            out.append({"title": title, "published_at": published_at, "source": source})
    return out


def _get_rss(source: str, url: str, limit: int, params: dict | None = None) -> list[dict]:
    try:
        resp = httpx.get(url, params=params, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return _parse_feed(source, resp.text, limit)
    except Exception:
        logger.warning("Failed to fetch feed %s, skipping it", source, exc_info=True)
        return []


# Per-ticker news query needs the right noun per asset class: "BTCUSD stock" is
# nonsense and starves the crypto trigger of relevant hits. Map crypto to its
# full name + "crypto"; equities keep "TICKER stock". Keyed by our whitelist
# convention ("BTCUSD", with the quote-currency suffix).
_CRYPTO_NAMES = {
    "BTCUSD": "Bitcoin", "ETHUSD": "Ethereum", "LTCUSD": "Litecoin",
    "BCHUSD": "Bitcoin Cash", "DOGEUSD": "Dogecoin", "LINKUSD": "Chainlink",
    "AVAXUSD": "Avalanche", "ADAUSD": "Cardano",
}


def _ticker_query(ticker: str) -> str:
    t = ticker.upper()
    if t in _CRYPTO_NAMES:
        return f"{_CRYPTO_NAMES[t]} crypto"
    return f"{ticker} stock"


def _get_ticker_headlines(ticker: str, limit: int) -> list[dict]:
    return _get_rss(
        f"Google News ({ticker})",
        GOOGLE_NEWS_RSS_URL,
        limit,
        params={"q": _ticker_query(ticker), "hl": "en-US", "gl": "US", "ceid": "US:en"},
    )


def _get_reddit(subreddit: str, limit: int) -> list[dict]:
    try:
        resp = httpx.get(
            f"https://www.reddit.com/r/{subreddit}/top.json",
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
                "source": f"Reddit r/{subreddit}",
            }
            for c in children
            if c.get("data", {}).get("title")
        ]
    except Exception:
        logger.warning("Failed to fetch Reddit r/%s, skipping it", subreddit, exc_info=True)
        return []


def _interleave(groups: list[list[dict]]) -> list[dict]:
    """Round-robins across sources (one headline from each in turn) instead
    of concatenating -- otherwise a handful of prolific general-news feeds
    would fill the entire `limit` before per-ticker or SEC-filing headlines
    ever get a look-in."""
    return [item for round_ in zip_longest(*groups) for item in round_ if item is not None]


class NewsClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    def get_new_ticker_headlines(
        self, tickers: list[str], seen: dict[str, list[str]]
    ) -> tuple[list[dict], dict[str, list[str]]]:
        """Cheap, per-ticker-only fetch (no Claude cost) used to detect a
        brand-new headline -- earnings release, material single-stock news --
        the moment it's published, independent of any price move. `seen` is
        the previous cycle's {ticker: [recent titles]}; returns (genuinely
        new headlines across all tickers, updated seen-state to persist)."""
        new_headlines: list[dict] = []
        updated_seen: dict[str, list[str]] = {}

        with ThreadPoolExecutor(max_workers=max(len(tickers), 1)) as pool:
            futures = {ticker: pool.submit(_get_ticker_headlines, ticker, PER_TICKER_LIMIT) for ticker in tickers}
            for ticker, future in futures.items():
                try:
                    headlines = future.result()
                except Exception:
                    logger.warning("Failed to fetch ticker headlines for %s, skipping it", ticker, exc_info=True)
                    headlines = []

                previously_seen = set(seen.get(ticker, []))
                new_headlines.extend(h for h in headlines if h["title"] not in previously_seen)
                # Snapshot this cycle's titles as the new baseline; if the
                # fetch failed, keep whatever we had rather than forgetting it.
                updated_seen[ticker] = [h["title"] for h in headlines] if headlines else list(previously_seen)

        return new_headlines, updated_seen

    def get_headlines(self, tickers: list[str], limit: int = 40) -> list[dict]:
        worker_count = len(RSS_FEEDS) + len(tickers) + len(REDDIT_SUBREDDITS)
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_get_rss, name, url, PER_SOURCE_LIMIT) for name, url in RSS_FEEDS]
            futures += [pool.submit(_get_ticker_headlines, ticker, PER_TICKER_LIMIT) for ticker in tickers]
            futures += [pool.submit(_get_reddit, sub, PER_SUBREDDIT_LIMIT) for sub in REDDIT_SUBREDDITS]

            per_source: list[list[dict]] = []
            for future in futures:
                try:
                    per_source.append(future.result())
                except Exception:
                    logger.warning("A news source future raised unexpectedly, skipping it", exc_info=True)
                    per_source.append([])

        return _interleave(per_source)[:limit]
