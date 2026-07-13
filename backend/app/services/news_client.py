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
from datetime import date, datetime, timedelta, timezone
from itertools import zip_longest

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 6.0

# Without an explicit User-Agent, httpx sends "python-httpx/..", which a large
# share of outlets (CNBC, Barron's, Investopedia, ETF.com, Bitcoin Magazine,
# Nasdaq, ...) reject outright with 403/429. A realistic browser UA + Accept
# revives the bulk of them -- this was the single reason the feeds looked
# "empty" on the datacenter-hosted server.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
# SEC EDGAR's access policy REQUIRES an identifying User-Agent (declared name +
# contact) and 403s both python's default and generic browser UAs -- give it
# its own compliant header instead.
SEC_HEADERS = {
    "User-Agent": "GielDarek Research admin@gieldarek.example",
    "Accept-Encoding": "gzip, deflate",
}

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
    # Reuters retired its public RSS host (feeds.reuters.com no longer resolves)
    # and Forbes' /markets/feed/ 404s -- both removed rather than failing every
    # cycle.
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
    # World / macro / index coverage -- broad global + economic headlines so the
    # brains see the big picture (central banks, geopolitics, indices), not only
    # US single-stock news. Keyless; each degrades independently on failure.
    ("BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Guardian Business", "https://www.theguardian.com/business/rss"),
    ("NPR Economy", "https://feeds.npr.org/1017/rss.xml"),
    ("CNBC Top News", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("CNBC Finance", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ("MarketWatch Real-time", "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"),
    ("MarketWatch Market Pulse", "https://feeds.content.dowjones.io/public/rss/mw_marketpulse"),
    ("Federal Reserve", "https://www.federalreserve.gov/feeds/press_all.xml"),
    ("FT Home", "https://www.ft.com/rss/home"),
    ("The Economist Finance", "https://www.economist.com/finance-and-economics/rss.xml"),
    ("Investing.com Stock Market", "https://www.investing.com/rss/news_25.rss"),
    ("Fortune", "https://fortune.com/feed/"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
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
    headers = SEC_HEADERS if "sec.gov" in url else BROWSER_HEADERS
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return _parse_feed(source, resp.text, limit)
    except Exception as exc:
        # Feeds degrade independently; log compactly (no stack trace) so one
        # server-side block doesn't bury the log in tracebacks every cycle.
        logger.warning("Failed to fetch feed %s (%s), skipping it", source, type(exc).__name__)
        return []


# Per-ticker news query needs the right noun per asset class: "BTCUSD stock" is
# nonsense and starves the crypto trigger of relevant hits. Map crypto to its
# full name + "crypto"; equities keep "TICKER stock". Keyed by our whitelist
# convention ("BTCUSD", with the quote-currency suffix).
_CRYPTO_NAMES = {
    "BTCUSD": "Bitcoin", "ETHUSD": "Ethereum", "SOLUSD": "Solana",
    "LTCUSD": "Litecoin", "BCHUSD": "Bitcoin Cash", "DOGEUSD": "Dogecoin",
    "LINKUSD": "Chainlink", "AVAXUSD": "Avalanche", "ADAUSD": "Cardano",
    "DOTUSD": "Polkadot", "UNIUSD": "Uniswap", "AAVEUSD": "Aave",
    "XRPUSD": "XRP", "SHIBUSD": "Shiba Inu",
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


# --- Finnhub (optional, keyed, reliable primary source) ---------------------
# https://finnhub.io -- a JSON news API that (unlike the free RSS feeds) is not
# User-Agent/IP-blocked on datacenter hosts, so it guarantees coverage even when
# CNBC/Barron's/Reddit reject the server. Enabled only when finnhub_api_key is
# set; every call degrades independently to [] on any error, like every other
# source here.
FINNHUB_BASE = "https://finnhub.io/api/v1"
FINNHUB_GENERAL_LIMIT = 8
FINNHUB_COMPANY_LIMIT = 3


def _finnhub_get(path: str, key: str, params: dict) -> list | dict:
    try:
        resp = httpx.get(f"{FINNHUB_BASE}{path}", params={**params, "token": key}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Finnhub %s failed (%s), skipping it", path, type(exc).__name__)
        return []


def _finnhub_items(raw: list | dict, limit: int, label: str) -> list[dict]:
    items: list[dict] = []
    for it in (raw if isinstance(raw, list) else [])[:limit]:
        title = (it.get("headline") or "").strip()
        if not title:
            continue
        published_at = ""
        ts = it.get("datetime")
        if ts:
            try:
                published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
            except (ValueError, OSError, OverflowError):
                published_at = ""
        outlet = it.get("source") or "Finnhub"
        suffix = f" ({label})" if label else ""
        items.append({"title": title, "published_at": published_at, "source": f"Finnhub · {outlet}{suffix}"})
    return items


def _get_finnhub_general(key: str, category: str = "general") -> list[dict]:
    return _finnhub_items(_finnhub_get("/news", key, {"category": category}), FINNHUB_GENERAL_LIMIT, category)


def _get_finnhub_company(ticker: str, key: str) -> list[dict]:
    today = date.today()
    raw = _finnhub_get(
        "/company-news",
        key,
        {"symbol": ticker.upper(), "from": (today - timedelta(days=3)).isoformat(), "to": today.isoformat()},
    )
    return _finnhub_items(raw, FINNHUB_COMPANY_LIMIT, ticker)


def _get_ticker_all(ticker: str, limit: int, finnhub_key: str = "") -> list[dict]:
    """Per-ticker headlines from Google News, plus Finnhub company-news when a
    key is set (equities only -- Finnhub company-news doesn't cover crypto
    pairs). Merged so both a keyless and a keyed deployment work."""
    items = _get_ticker_headlines(ticker, limit)
    if finnhub_key and ticker.upper() not in _CRYPTO_NAMES:
        items += _get_finnhub_company(ticker, finnhub_key)
    return items


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
    except Exception as exc:
        # Reddit hard-blocks datacenter IPs (403 "Blocked") regardless of UA --
        # log compactly instead of a full traceback each cycle.
        logger.warning("Failed to fetch Reddit r/%s (%s), skipping it", subreddit, type(exc).__name__)
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

    @property
    def _finnhub_key(self) -> str:
        # Safe even when settings is None (used in tests) -- returns "" so the
        # keyed source is simply skipped and behaviour matches an RSS-only run.
        return getattr(self._settings, "finnhub_api_key", "") or ""

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

        key = self._finnhub_key
        with ThreadPoolExecutor(max_workers=max(len(tickers), 1)) as pool:
            futures = {ticker: pool.submit(_get_ticker_all, ticker, PER_TICKER_LIMIT, key) for ticker in tickers}
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
        key = self._finnhub_key
        crypto_enabled = bool(getattr(self._settings, "crypto_enabled", False))
        worker_count = len(RSS_FEEDS) + len(tickers) + len(REDDIT_SUBREDDITS) + 2
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_get_rss, name, url, PER_SOURCE_LIMIT) for name, url in RSS_FEEDS]
            futures += [pool.submit(_get_ticker_all, ticker, PER_TICKER_LIMIT, key) for ticker in tickers]
            futures += [pool.submit(_get_reddit, sub, PER_SUBREDDIT_LIMIT) for sub in REDDIT_SUBREDDITS]
            # Keyed primary source (only when configured): broad market news, plus
            # a crypto-category pull for the 24/7 venue.
            if key:
                futures.append(pool.submit(_get_finnhub_general, key, "general"))
                if crypto_enabled:
                    futures.append(pool.submit(_get_finnhub_general, key, "crypto"))

            per_source: list[list[dict]] = []
            for future in futures:
                try:
                    per_source.append(future.result())
                except Exception:
                    logger.warning("A news source future raised unexpectedly, skipping it", exc_info=True)
                    per_source.append([])

        return _interleave(per_source)[:limit]
