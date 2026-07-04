"""Optional crypto news headlines via CryptoPanic. Degrades gracefully to an
empty list if no API key is configured or the request fails, so the trading
engine never hard-depends on this data source."""

import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

CRYPTOPANIC_URL = "https://cryptopanic.com/api/v1/posts/"


class NewsClient:
    def __init__(self, settings: Settings):
        self._settings = settings

    def get_headlines(self, currencies: list[str], limit: int = 10) -> list[dict]:
        if not self._settings.cryptopanic_api_key:
            return []

        params = {
            "auth_token": self._settings.cryptopanic_api_key,
            "currencies": ",".join(currencies),
            "public": "true",
        }
        try:
            resp = httpx.get(CRYPTOPANIC_URL, params=params, timeout=10.0)
            resp.raise_for_status()
            results = resp.json().get("results", [])[:limit]
            return [
                {
                    "title": item.get("title", ""),
                    "published_at": item.get("published_at", ""),
                    "source": item.get("source", {}).get("title", ""),
                }
                for item in results
            ]
        except Exception:
            logger.warning("Failed to fetch news headlines, continuing without them", exc_info=True)
            return []
