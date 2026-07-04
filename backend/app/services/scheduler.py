import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import get_settings
from app.db import SessionLocal
from app.services.binance_client import BinanceClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.news_client import NewsClient
from app.services.trading_engine import run_cycle

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _job() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        binance = BinanceClient(settings)
        news = NewsClient(settings)
        advisor = ClaudeAdvisor(settings)
        decision = run_cycle(db, settings, binance, news, advisor)
        if decision is not None:
            logger.info("Cycle produced decision: %s %s", decision.action, decision.symbol)
    except Exception:
        logger.exception("Trading cycle failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _job,
        "interval",
        minutes=settings.poll_interval_minutes,
        id="trading_cycle",
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
