"""Market news headlines aggregated from a broad set of free sources so a
single outlet's spin or an outage never dominates/blocks what Claude sees.
Each source is fetched in parallel (bounded per-request timeout) and
degrades independently to nothing on failure -- the trading engine never
hard-depends on any one of them. Results are interleaved round-robin across
sources before truncating to `limit`, so a handful of prolific feeds can't
crowd out the rest (e.g. per-ticker headlines or SEC filings) once capped."""

import logging
import time
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
    ("Seeking Alpha ETFs", "https://seekingalpha.com/api/sa/combined/etf.xml"),
    ("MarketBeat", "https://www.marketbeat.com/feed/"),
    ("CNN Business", "http://rss.cnn.com/rss/money_latest.rss"),
    ("Reuters Markets", "https://www.reutersagency.com/feed/?best-topics=markets&post_type=best"),
    ("Yahoo Finance Headlines", "https://finance.yahoo.com/rss/topstories"),
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
]

# Pula KANDYDATÓW do auto-odkrywania: dodatkowe, wolne/keyless feedy, których NIE
# ma w RSS_FEEDS powyżej. Codzienny job (discover_feeds) próbnie sięga do nich i
# dopisuje ~10% tych, które REALNIE odpowiadają z serwera -- reszta (zablokowana
# na datacenter-IP / 404) po prostu odpada. Google News (topic feeds) jest tu
# celowo, bo jest udowodnienie-osiągalny z serwera, więc lista zawsze urośnie o
# coś sensownego, a nie utknie na samych blokadach.
CANDIDATE_FEEDS: list[tuple[str, str]] = [
    ("Google News — Biznes", "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"),
    ("Google News — Technologia", "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"),
    ("Google News — Rynki (PL)", "https://news.google.com/rss/search?q=gie%C5%82da%20akcje%20USA&hl=pl&gl=PL&ceid=PL:pl"),
    ("CNBC Investing", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
    ("CNBC Technology", "https://www.cnbc.com/id/19854910/device/rss/rss.html"),
    ("CNBC Earnings", "https://www.cnbc.com/id/15839135/device/rss/rss.html"),
    ("NYT Business", "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml"),
    ("NYT Economy", "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml"),
    ("Guardian Economics", "https://www.theguardian.com/business/economics/rss"),
    ("MarketWatch Bulletins", "https://feeds.content.dowjones.io/public/rss/mw_bulletins"),
    ("MarketWatch Personal Finance", "https://feeds.content.dowjones.io/public/rss/mw_personalfinance"),
    ("Investing.com Economy", "https://www.investing.com/rss/news_14.rss"),
    ("Investing.com Commodities", "https://www.investing.com/rss/news_11.rss"),
    ("Investing.com Forex", "https://www.investing.com/rss/news_1.rss"),
    ("Bloomberg Technology", "https://feeds.bloomberg.com/technology/news.rss"),
    ("Bloomberg Economics", "https://feeds.bloomberg.com/economics/news.rss"),
    ("Sky News Business", "https://feeds.skynews.com/feeds/rss/business.xml"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("Engadget", "https://www.engadget.com/rss.xml"),
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("SEC EDGAR 10-K", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=10-K&company=&dateb=&owner=include&count=40&output=atom"),
    ("SEC EDGAR 13F", "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=13F&company=&dateb=&owner=include&count=40&output=atom"),
    ("Federal Reserve speeches", "https://www.federalreserve.gov/feeds/speeches.xml"),
    ("ECB press", "https://www.ecb.europa.eu/rss/press.html"),
]

# Auto-odkryte feedy dołączane do RSS_FEEDS w RUNTIME (napełniane z DB przy
# starcie przez load_discovered_feeds i codziennym jobem). [(nazwa, url), ...].
_DISCOVERED_FEEDS: list[tuple[str, str]] = []


def active_rss_feeds() -> list[tuple[str, str]]:
    """Stałe RSS_FEEDS + auto-odkryte, zdeduplikowane po URL. To JEDNO źródło
    prawdy o tym, z jakich feedów news_client realnie czyta -- fetchery używają
    właśnie tej listy, więc odkryte źródła wchodzą do gry bez redeployu."""
    seen = {url for _, url in RSS_FEEDS}
    out = list(RSS_FEEDS)
    for name, url in _DISCOVERED_FEEDS:
        if url not in seen:
            seen.add(url)
            out.append((name, url))
    return out


def set_discovered_feeds(feeds: list[tuple[str, str]]) -> None:
    """Podmień runtime'ową listę odkrytych feedów (wołane po odczycie z DB i po
    codziennym odkrywaniu). Odfiltrowuje te, które i tak są już w RSS_FEEDS."""
    base = {url for _, url in RSS_FEEDS}
    _DISCOVERED_FEEDS.clear()
    for name, url in feeds:
        if url not in base:
            _DISCOVERED_FEEDS.append((str(name), str(url)))


def probe_feed(name: str, url: str) -> bool:
    """Czy feed JEST OSIĄGALNY z tego serwera i zwraca parsowalne nagłówki?
    Jedno próbne zapytanie; True tylko gdy wróciła co najmniej jedna pozycja."""
    try:
        return len(_get_rss(name, url, 1)) > 0
    except Exception:
        return False


def discover_feeds(budget: int) -> list[tuple[str, str]]:
    """Sprawdź pulę CANDIDATE_FEEDS (pomijając te już aktywne) i zwróć do
    `budget` NOWYCH, osiągalnych feedów. Próbowanie równoległe, żeby nie ciągnąć
    się w nieskończoność. Nie dotyka DB -- czysta logika, orkiestracja w
    schedulerze."""
    if budget <= 0:
        return []
    active = {url for _, url in active_rss_feeds()}
    candidates = [(n, u) for n, u in CANDIDATE_FEEDS if u not in active]
    if not candidates:
        return []
    found: list[tuple[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, min(len(candidates), 12))) as pool:
        futures = [(n, u, pool.submit(probe_feed, n, u)) for n, u in candidates]
        for name, url, fut in futures:
            try:
                ok = fut.result()
            except Exception:
                ok = False
            if ok:
                found.append((name, url))
            if len(found) >= budget:
                break
    return found
# Polish-language news band (display only) — sourced from Google News RSS with
# hl=pl so headlines come back in Polish. Google News is already the per-ticker
# source below, so it's proven-reachable from the server (unlike raw PL RSS,
# which is IP/UA-blocked on datacenter hosts). Topic queries relevant to our
# US-stock operation.
PL_NEWS_QUERIES: list[str] = [
    "giełda USA Wall Street",
    "S&P 500 Nasdaq notowania",
    "akcje spółek technologicznych USA",
    "Rezerwa Federalna stopy procentowe",
    "rynki akcji giełda świat",
    "gospodarka USA inflacja",
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


def _ticker_query(ticker: str) -> str:
    # US-equities/ETF only now (crypto venue removed) -- every whitelist symbol
    # is a plain ticker.
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


# --- Alpaca News (keyed, PRIMARY source) ------------------------------------
# https://data.alpaca.markets/v1beta1/news -- Benzinga-sourced JSON news that
# comes FREE with the Alpaca account we already trade through, and (crucially)
# resolves from the SAME host our order flow already uses, so unlike the RSS
# feeds it is NOT UA/IP-blocked on the datacenter server. This is the workhorse
# per-ticker + general news source; auth is the same APCA header pair as the
# trading/data clients. Degrades independently to [] on any error.
ALPACA_NEWS_URL = "https://data.alpaca.markets/v1beta1/news"
ALPACA_NEWS_GENERAL_LIMIT = 10
ALPACA_NEWS_COMPANY_LIMIT = 4


def _alpaca_news_get(params: dict, creds: tuple[str, str]) -> list:
    key_id, secret = creds
    try:
        resp = httpx.get(
            ALPACA_NEWS_URL,
            params=params,
            headers={"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret, "Accept": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("news", []) or []
    except Exception as exc:
        logger.warning("Alpaca News (%s) failed (%s), skipping it", params.get("symbols", "general"), type(exc).__name__)
        return []


def _alpaca_news_items(raw: list, limit: int, label: str) -> list[dict]:
    items: list[dict] = []
    for it in (raw if isinstance(raw, list) else [])[:limit]:
        title = (it.get("headline") or "").strip()
        if not title:
            continue
        published_at = it.get("created_at") or it.get("updated_at") or ""
        outlet = it.get("source") or "Alpaca"
        suffix = f" ({label})" if label else ""
        items.append({"title": title, "published_at": published_at, "source": f"Alpaca · {outlet}{suffix}"})
    return items


def _get_alpaca_general(creds: tuple[str, str]) -> list[dict]:
    return _alpaca_news_items(
        _alpaca_news_get({"limit": ALPACA_NEWS_GENERAL_LIMIT, "sort": "desc"}, creds), ALPACA_NEWS_GENERAL_LIMIT, ""
    )


def _get_alpaca_trending_symbols(creds: tuple[str, str], articles_limit: int = 50) -> list[str]:
    """Harvest the tickers most-mentioned across the latest Alpaca News
    articles (each carries a `symbols` array). This is the DISCOVERY feed for
    the no-whitelist universe -- 'co jest teraz w newsach' -- ordered by mention
    frequency. Junk/non-tradable tickers are filtered downstream by Alpaca's
    asset check; here we only keep plausibly-shaped US tickers."""
    from collections import Counter

    raw = _alpaca_news_get({"limit": articles_limit, "sort": "desc"}, creds)
    counter: Counter = Counter()
    for it in (raw if isinstance(raw, list) else []):
        for s in (it.get("symbols") or []):
            sym = str(s).upper().strip()
            if sym.isalpha() and 1 <= len(sym) <= 5:
                counter[sym] += 1
    return [sym for sym, _ in counter.most_common()]


def _get_alpaca_company(ticker: str, creds: tuple[str, str]) -> list[dict]:
    return _alpaca_news_items(
        _alpaca_news_get({"symbols": ticker.upper(), "limit": ALPACA_NEWS_COMPANY_LIMIT, "sort": "desc"}, creds),
        ALPACA_NEWS_COMPANY_LIMIT,
        ticker,
    )


# --- Alpha Vantage NEWS_SENTIMENT (keyed, sentiment-scored) -----------------
# https://www.alphavantage.co -- headlines WITH a computed sentiment label/score,
# qualitative colour the mechanical filter can't produce. Free tier is rate-
# capped (~25 calls/day), so this is a LIGHT general-market-sentiment source
# behind a process-wide TTL cache: at most one live call every _ALPHA_VANTAGE_
# TTL_S, regardless of how often the 5-min cycle asks. On throttle/error it
# returns the last good batch (stale but useful) rather than nothing.
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
_ALPHA_VANTAGE_TTL_S = 1800  # 30 min -> <= ~48 calls/day worst case, well under free cap in practice
_ALPHA_VANTAGE_LIMIT = 8
_av_cache: dict = {"at": 0.0, "items": []}


def _av_items(feed: list, limit: int) -> list[dict]:
    out: list[dict] = []
    for it in (feed if isinstance(feed, list) else [])[:limit]:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        raw_ts = it.get("time_published") or ""
        published_at = ""
        if raw_ts:
            try:
                published_at = datetime.strptime(raw_ts, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                published_at = ""
        outlet = it.get("source") or "AlphaVantage"
        entry = {"title": title, "published_at": published_at, "source": f"AlphaVantage · {outlet}"}
        label = it.get("overall_sentiment_label")
        if label:
            entry["sentiment_label"] = label
        score = it.get("overall_sentiment_score")
        if score is not None:
            try:
                entry["sentiment_score"] = round(float(score), 3)
            except (ValueError, TypeError):
                pass
        out.append(entry)
    return out


def _get_alpha_vantage_general(key: str) -> list[dict]:
    if not key:
        return []
    now = time.monotonic()
    if _av_cache["items"] and now - _av_cache["at"] < _ALPHA_VANTAGE_TTL_S:
        return _av_cache["items"]
    try:
        resp = httpx.get(
            ALPHA_VANTAGE_URL,
            params={
                "function": "NEWS_SENTIMENT",
                "topics": "financial_markets",
                "sort": "LATEST",
                "limit": _ALPHA_VANTAGE_LIMIT,
                "apikey": key,
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Alpha Vantage failed (%s), keeping last cache", type(exc).__name__)
        return _av_cache["items"] or []
    feed = data.get("feed")
    if not isinstance(feed, list):
        # AV signals throttle/error with HTTP 200 + {"Information"/"Note": ...}.
        note = data.get("Information") or data.get("Note") or ""
        logger.warning("Alpha Vantage no feed (%s), keeping last cache", (note[:80] if note else list(data.keys())))
        return _av_cache["items"] or []
    items = _av_items(feed, _ALPHA_VANTAGE_LIMIT)
    _av_cache["at"] = now
    _av_cache["items"] = items
    return items


# --- NewsAPI.org (keyed, general business headlines) ------------------------
# https://newsapi.org -- broad business/market headlines. Free/dev tier is
# ~100 calls/day, so it's a TTL-cached general source (like Alpha Vantage).
NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"
_NEWSAPI_TTL_S = 1800  # 30 min
_NEWSAPI_LIMIT = 8
_newsapi_cache: dict = {"at": 0.0, "items": []}


def _get_newsapi_general(key: str) -> list[dict]:
    if not key:
        return []
    now = time.monotonic()
    if _newsapi_cache["items"] and now - _newsapi_cache["at"] < _NEWSAPI_TTL_S:
        return _newsapi_cache["items"]
    try:
        resp = httpx.get(
            NEWSAPI_URL,
            params={"category": "business", "country": "us", "pageSize": _NEWSAPI_LIMIT, "apiKey": key},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("NewsAPI failed (%s), keeping last cache", type(exc).__name__)
        return _newsapi_cache["items"] or []
    if data.get("status") != "ok":
        logger.warning("NewsAPI non-ok (%s), keeping last cache", str(data.get("message"))[:80])
        return _newsapi_cache["items"] or []
    items: list[dict] = []
    for it in (data.get("articles") or [])[:_NEWSAPI_LIMIT]:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        outlet = (it.get("source") or {}).get("name") or "NewsAPI"
        items.append({"title": title, "published_at": it.get("publishedAt") or "", "source": f"NewsAPI · {outlet}"})
    _newsapi_cache["at"] = now
    _newsapi_cache["items"] = items
    return items


# --- SerpAPI Google News (keyed, tight monthly cap) -------------------------
# https://serpapi.com -- Google News search proxy. Free tier is only ~100
# searches/MONTH, so this sits behind a LONG TTL cache and is a light general
# source only.
SERPAPI_URL = "https://serpapi.com/search"
_SERPAPI_TTL_S = 21600  # 6h -> ~4 calls/day -> ~120/month worst case; usually far fewer
_SERPAPI_LIMIT = 8
_serpapi_cache: dict = {"at": 0.0, "items": []}


def _get_serpapi_general(key: str) -> list[dict]:
    if not key:
        return []
    now = time.monotonic()
    if _serpapi_cache["items"] and now - _serpapi_cache["at"] < _SERPAPI_TTL_S:
        return _serpapi_cache["items"]
    try:
        resp = httpx.get(
            SERPAPI_URL,
            params={"engine": "google_news", "q": "stock market", "gl": "us", "hl": "en", "api_key": key},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("SerpAPI failed (%s), keeping last cache", type(exc).__name__)
        return _serpapi_cache["items"] or []
    items: list[dict] = []
    for it in (data.get("news_results") or [])[:_SERPAPI_LIMIT]:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        outlet = (it.get("source") or {}).get("name") if isinstance(it.get("source"), dict) else (it.get("source") or "Google News")
        items.append({"title": title, "published_at": it.get("date") or "", "source": f"SerpAPI · {outlet}"})
    _serpapi_cache["at"] = now
    _serpapi_cache["items"] = items
    return items


def _get_ticker_all(
    ticker: str, limit: int, finnhub_key: str = "", alpaca_creds: tuple[str, str] | None = None
) -> list[dict]:
    """Per-ticker headlines from Alpaca News (primary) + Google News, plus
    Finnhub company-news when a key is set. Merged so a keyless deployment still
    works and a keyed one gets the reliable, non-IP-blocked sources on top."""
    items: list[dict] = []
    if alpaca_creds:
        items += _get_alpaca_company(ticker, alpaca_creds)
    items += _get_ticker_headlines(ticker, limit)
    if finnhub_key:
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

    @property
    def _alpaca_creds(self) -> tuple[str, str] | None:
        """Alpaca News reuses the trading account's key pair. Returns None (so
        the source is skipped) when either half is missing -- keeps tests and
        keyless runs behaving exactly as before."""
        kid = getattr(self._settings, "alpaca_api_key", "") or ""
        sec = getattr(self._settings, "alpaca_api_secret", "") or ""
        return (kid, sec) if kid and sec else None

    @property
    def _alpha_vantage_key(self) -> str:
        return getattr(self._settings, "alpha_vantage_api_key", "") or ""

    @property
    def _newsapi_key(self) -> str:
        return getattr(self._settings, "newsapi_api_key", "") or ""

    @property
    def _serpapi_key(self) -> str:
        return getattr(self._settings, "serpapi_api_key", "") or ""

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
        creds = self._alpaca_creds
        with ThreadPoolExecutor(max_workers=max(len(tickers), 1)) as pool:
            futures = {
                ticker: pool.submit(_get_ticker_all, ticker, PER_TICKER_LIMIT, key, creds) for ticker in tickers
            }
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

    def get_trending_symbols(self, limit: int = 20) -> list[str]:
        """Tickers currently trending in the news (Alpaca News `symbols`),
        ordered by mention frequency. Drives the dynamic, no-whitelist universe.
        Empty list when Alpaca creds are missing or the fetch fails -- the caller
        then falls back to the seed list, so discovery only ever ADDS names."""
        creds = self._alpaca_creds
        if not creds:
            return []
        try:
            return _get_alpaca_trending_symbols(creds)[:limit]
        except Exception:
            logger.warning("Trending-symbols fetch failed, skipping discovery", exc_info=True)
            return []

    def source_report(self, tickers: list[str]) -> dict:
        """Live status KAŻDEGO źródła osobno dla zakładki NEWSY: odpala każde
        źródło niezależnie i mówi ok/down + ile nagłówków ZWRÓCIŁO TERAZ (to jest
        'co widzę na żywo', nie tylko 'czy jest połączenie'). Zwraca też złączoną
        próbkę nagłówków (z sentymentem, gdy jest), żeby UI pokazał realny feed."""
        key = self._finnhub_key
        creds = self._alpaca_creds
        av = self._alpha_vantage_key

        jobs: list[tuple[str, str, object]] = []
        base_urls = {u for _, u in RSS_FEEDS}
        for name, url in active_rss_feeds():
            grp = "RSS / feedy" if url in base_urls else "RSS / auto-odkryte"
            jobs.append((name, grp, lambda u=url, nm=name: _get_rss(nm, u, PER_SOURCE_LIMIT)))
        for sub in REDDIT_SUBREDDITS:
            jobs.append((f"Reddit r/{sub}", "Reddit", lambda s=sub: _get_reddit(s, PER_SUBREDDIT_LIMIT)))
        for t in tickers[:6]:
            jobs.append((f"Per-ticker: {t}", "Per-ticker", lambda tt=t: _get_ticker_all(tt, PER_TICKER_LIMIT, key, creds)))
        if creds:
            jobs.append(("Alpaca News (Benzinga)", "Keyed (główne)", lambda: _get_alpaca_general(creds)))
        if av:
            jobs.append(("Alpha Vantage (sentyment)", "Keyed (główne)", lambda: _get_alpha_vantage_general(av)))
        if self._newsapi_key:
            jobs.append(("NewsAPI.org", "Keyed (główne)", lambda: _get_newsapi_general(self._newsapi_key)))
        if self._serpapi_key:
            jobs.append(("SerpAPI (Google News)", "Keyed (główne)", lambda: _get_serpapi_general(self._serpapi_key)))
        if key:
            jobs.append(("Finnhub", "Keyed (główne)", lambda: _get_finnhub_general(key)))

        sources: list[dict] = []
        per_source_items: list[list[dict]] = []
        with ThreadPoolExecutor(max_workers=max(len(jobs), 1)) as pool:
            futures = [(nm, grp, pool.submit(fn)) for nm, grp, fn in jobs]
            for nm, grp, fut in futures:
                try:
                    items = fut.result() or []
                except Exception:
                    items = []
                per_source_items.append(items)
                sources.append({"name": nm, "group": grp, "status": "ok" if items else "down", "count": len(items)})

        return {"sources": sources, "headlines": _interleave(per_source_items)[:30]}

    def get_pl_headlines(self, limit: int = 18) -> list[dict]:
        """Polish-language headlines for the on-screen news band (display only).

        Google News returns titles as "Nagłówek - Wydawca"; split the outlet off
        so the band shows a clean headline + a compact source tag."""
        with ThreadPoolExecutor(max_workers=max(1, len(PL_NEWS_QUERIES))) as pool:
            futures = [
                pool.submit(
                    _get_rss, "Google News PL", GOOGLE_NEWS_RSS_URL, PER_SOURCE_LIMIT,
                    {"q": q, "hl": "pl", "gl": "PL", "ceid": "PL:pl"},
                )
                for q in PL_NEWS_QUERIES
            ]
            per_source: list[list[dict]] = []
            for future in futures:
                try:
                    per_source.append(future.result())
                except Exception:
                    logger.warning("A PL news query raised, skipping it", exc_info=True)
                    per_source.append([])

        out: list[dict] = []
        seen: set[str] = set()
        for h in _interleave(per_source):
            title = (h.get("title") or "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            source = "Google News"
            if " - " in title:
                head, outlet = title.rsplit(" - ", 1)
                if head.strip():
                    title, source = head.strip(), outlet.strip()
            out.append({"title": title, "published_at": h.get("published_at"), "source": source})
            if len(out) >= limit:
                break
        return out

    def get_headlines(self, tickers: list[str], limit: int = 40) -> list[dict]:
        key = self._finnhub_key
        creds = self._alpaca_creds
        av_key = self._alpha_vantage_key
        feeds = active_rss_feeds()
        worker_count = len(feeds) + len(tickers) + len(REDDIT_SUBREDDITS) + 5
        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_get_rss, name, url, PER_SOURCE_LIMIT) for name, url in feeds]
            futures += [pool.submit(_get_ticker_all, ticker, PER_TICKER_LIMIT, key, creds) for ticker in tickers]
            futures += [pool.submit(_get_reddit, sub, PER_SUBREDDIT_LIMIT) for sub in REDDIT_SUBREDDITS]
            # Keyed primary source (only when configured): broad US market news.
            if key:
                futures.append(pool.submit(_get_finnhub_general, key, "general"))
            # Alpaca News general feed -- reliable, non-IP-blocked broad market news.
            if creds:
                futures.append(pool.submit(_get_alpaca_general, creds))
            # Alpha Vantage general market sentiment (TTL-cached; sentiment-scored).
            if av_key:
                futures.append(pool.submit(_get_alpha_vantage_general, av_key))
            # NewsAPI.org + SerpAPI general headlines (both TTL-cached).
            if self._newsapi_key:
                futures.append(pool.submit(_get_newsapi_general, self._newsapi_key))
            if self._serpapi_key:
                futures.append(pool.submit(_get_serpapi_general, self._serpapi_key))

            per_source: list[list[dict]] = []
            for future in futures:
                try:
                    per_source.append(future.result())
                except Exception:
                    logger.warning("A news source future raised unexpectedly, skipping it", exc_info=True)
                    per_source.append([])

        return _interleave(per_source)[:limit]
