"""Free, keyless macro/sentiment context: Fear & Greed Index (alternative.me)
and global crypto market stats (CoinGecko public API). Both degrade to
None/empty on any failure, mirroring news_client.py, so the trading engine
never hard-depends on this data."""

import logging

import httpx

logger = logging.getLogger(__name__)

FEAR_GREED_URL = "https://api.alternative.me/fng/"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"


class MarketContextClient:
    def get_market_context(self) -> dict:
        return {
            "fear_greed_index": self._get_fear_greed_index(),
            **self._get_global_market_context(),
        }

    def _get_fear_greed_index(self) -> int | None:
        try:
            resp = httpx.get(FEAR_GREED_URL, params={"limit": 1}, timeout=10.0)
            resp.raise_for_status()
            return int(resp.json()["data"][0]["value"])
        except Exception:
            logger.warning("Failed to fetch Fear & Greed index, continuing without it", exc_info=True)
            return None

    def _get_global_market_context(self) -> dict:
        try:
            resp = httpx.get(COINGECKO_GLOBAL_URL, timeout=10.0)
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
