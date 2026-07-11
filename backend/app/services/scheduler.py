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


def _crypto_job() -> None:
    """The 24-7 crypto venue -- same Alpaca account, a separate asset-class
    client. Runs only when CRYPTO_ENABLED -- shares the same pause/halt STOP
    gate as the equities cycle, but trades round the clock (always_open) with
    its own whitelist and isolated per-venue state."""
    settings = get_settings()
    if not settings.crypto_enabled:
        return
    db = SessionLocal()
    try:
        broker = AlpacaClient(settings, asset_class="crypto")
        news = NewsClient(settings)
        advisor = ClaudeAdvisor(settings)
        market_ctx = MarketContextClient()
        decision = run_cycle(
            db, settings, broker, news, advisor, market_ctx,
            venue="crypto", whitelist=settings.crypto_whitelist_symbols, always_open=True,
        )
        if decision is not None:
            logger.info("Crypto cycle produced decision: %s %s", decision.action, decision.symbol)
    except Exception:
        logger.exception("Crypto trading cycle failed")
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


def _self_review_job() -> None:
    from app.services.self_review import run_self_review

    settings = get_settings()
    db = SessionLocal()
    try:
        run_self_review(db, settings)
    except Exception:
        logger.exception("Weekly self-review failed")
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
    # Crypto (24-7, same Alpaca account) venue -- the job itself no-ops unless
    # CRYPTO_ENABLED, so it's always registered and just idles until enabled.
    scheduler.add_job(
        _crypto_job,
        "interval",
        minutes=settings.poll_interval_minutes,
        id="crypto_trading_cycle",
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
    # Daily self-review: every morning before the US open, so each session
    # starts with fresh lessons distilled from the last 7 days of trades. Moved
    # from weekly to daily -- a bot trading every day needs faster feedback than
    # one review a week (the review itself is a single cheap fast-model call).
    scheduler.add_job(
        _self_review_job,
        CronTrigger(hour=12, minute=0, timezone=settings.report_timezone),
        id="daily_self_review",
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
