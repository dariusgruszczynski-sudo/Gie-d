"""Free, keyless macro/sentiment context aggregated from several public data
APIs (Fear & Greed, CoinGecko global/trending/top-movers, DeFiLlama TVL).
Each source degrades independently to None/empty on failure, mirroring
news_client.py, so the trading engine never hard-depends on any one of them."""

import logging
from concurrent.futures import ThreadPoolExecutor

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 8.0
FEAR_GREED_URL = "https://api.alternative.me/fng/"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"
COINGECKO_TRENDING_URL = "https://api.coingecko.com/api/v3/search/trending"
COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
DEFILLAMA_TVL_URL = "https://api.llama.fi/v2/historicalChainTvl"


def _get_fear_greed_index() -> int | None:
    try:
        resp = httpx.get(FEAR_GREED_URL, params={"limit": 1}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return int(resp.json()["data"][0]["value"])
    except Exception:
        logger.warning("Failed to fetch Fear & Greed index, continuing without it", exc_info=True)
        return None


def _get_global_market_context() -> dict:
    try:
        resp = httpx.get(COINGECKO_GLOBAL_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()["data"]
        return {
            "btc_dominance_pct": round(data["market_cap_percentage"].get("btc", 0.0), 1),
            "global_market_cap_change_24h_pct": round(
                data.get("market_cap_change_percentage_24h_usd", 0.0), 1
            ),
        }
    except Exception:
        logger.warning("Failed to fetch CoinGecko global market data, continuing without it", exc_info=True)
        return {}


def _get_trending_coins() -> list[str]:
    try:
        resp = httpx.get(COINGECKO_TRENDING_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        coins = resp.json().get("coins", [])[:7]
        return [c["item"]["symbol"].upper() for c in coins if c.get("item", {}).get("symbol")]
    except Exception:
        logger.warning("Failed to fetch CoinGecko trending coins, continuing without it", exc_info=True)
        return []

def _get_top_movers() -> dict:
    try:
        resp = httpx.get(
            COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 50,
                "page": 1,
                "price_change_percentage": "24h",
            },
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        coins = resp.json()
        ranked = sorted(
            (c for c in coins if c.get("price_change_percentage_24h") is not None),
            key=lambda c: c["price_change_percentage_24h"],
        )
        top_gainers = [
            {"symbol": c["symbol"].upper(), "change_24h_pct": round(c["price_change_percentage_24h"], 1)}
            for c in ranked[-5:][::-1]
        ]
        top_losers = [
            {"symbol": c["symbol"].upper(), "change_24h_pct": round(c["price_change_percentage_24h"], 1)}
            for c in ranked[:5]
        ]
        return {"top_gainers_24h_top50cap": top_gainers, "top_losers_24h_top50cap": top_losers}
    except Exception:
        logger.warning("Failed to fetch CoinGecko top movers, continuing without it", exc_info=True)
        return {}


def _get_defi_tvl_change() -> float | None:
    try:
        resp = httpx.get(DEFILLAMA_TVL_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        points = resp.json()
        if len(points) < 8:
            return None
        latest = points[-1]["tvl"]
        week_ago = points[-8]["tvl"]
        if week_ago <= 0:
            return None
        return round((latest - week_ago) / week_ago * 100, 1)
    except Exception:
        logger.warning("Failed to fetch DeFiLlama TVL, continuing without it", exc_info=True)
        return None


class MarketContextClient:
    def get_market_context(self) -> dict:
        with ThreadPoolExecutor(max_workers=5) as pool:
            fear_greed = pool.submit(_get_fear_greed_index)
            global_ctx = pool.submit(_get_global_market_context)
            trending = pool.submit(_get_trending_coins)
            movers = pool.submit(_get_top_movers)
            tvl_change = pool.submit(_get_defi_tvl_change)

            context: dict = {
                "fear_greed_index": fear_greed.result(),
                **global_ctx.result(),
                "trending_coins": trending.result(),
                **movers.result(),
                "defi_tvl_change_7d_pct": tvl_change.result(),
            }
        return context
