import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db import SessionLocal
from app.services.alpaca_client import AlpacaClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.email_reporter import send_daily_report
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.trading_engine import run_cycle

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _job() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        broker = AlpacaClient(settings)
        news = NewsClient(settings)
        advisor = ClaudeAdvisor(settings)
        market_ctx = MarketContextClient()
        decision = run_cycle(db, settings, broker, news, advisor, market_ctx)
        if decision is not None:
            logger.info("Cycle produced decision: %s %s", decision.action, decision.symbol)
    except Exception:
        logger.exception("Trading cycle failed")
    finally:
        db.close()


def _report_job() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        send_daily_report(db, settings)
    except Exception:
        logger.exception("Daily report email failed")
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
    scheduler.add_job(
        _report_job,
        CronTrigger(
            hour=settings.report_hour,
            minute=settings.report_minute,
            timezone=settings.report_timezone,
        ),
        id="daily_report",
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
