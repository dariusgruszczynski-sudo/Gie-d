from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    anthropic_api_key: str = ""
    claude_model: str = "claude-opus-4-8"

    binance_api_key: str = ""
    binance_api_secret: str = ""
    binance_testnet: bool = True

    cryptopanic_api_key: str = ""

    daily_loss_limit_pct: float = 50.0
    weekly_loss_limit_pct: float = 70.0
    max_position_pct: float = 25.0
    trading_whitelist: str = "BTCUSDT,ETHUSDT"

    poll_interval_minutes: int = 15
    price_move_trigger_pct: float = 2.0

    database_url: str = "sqlite:///./data/trading.db"

    @property
    def whitelist_symbols(self) -> list[str]:
        return [s.strip().upper() for s in self.trading_whitelist.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
