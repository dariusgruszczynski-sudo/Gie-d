"""Jedno miejsce konfiguracji logowania dla całej apki.

Dotąd log konfigurował inline `logging.basicConfig` w main.py, a hałaśliwe
biblioteki (APScheduler, httpx, urllib3) zalewały log INFO-ami, w których ginęły
realne ostrzeżenia z silnika. Tu ustawiamy jeden spójny format i przyciszamy te
biblioteki do WARNING, żeby log był czytelny i by dało się po fakcie odtworzyć,
co robił bot. Idempotentne (force=True), więc restart/testy nie mnożą handlerów."""

import logging

_LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

# Biblioteki, które przy INFO zalewają log rutyną (każdy tick schedulera, każde
# żądanie HTTP) -- podnosimy im próg do WARNING, żeby zostały tylko realne problemy.
_NOISY_LOGGERS = ("apscheduler", "httpx", "httpcore", "urllib3", "asyncio")


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format=_LOG_FORMAT, force=True)
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
