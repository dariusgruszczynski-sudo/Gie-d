import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db import SessionLocal
from app.services.alpaca_client import AlpacaClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.push_notifier import send_daily_summary_push
from app.services.strategy_profiles import effective_settings
from app.services.trading_engine import compute_and_cache_regime, compute_portfolio, run_cycle

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
        # Equities brain: base settings == the medium-aggressive profile.
        decision = run_cycle(db, effective_settings(settings, "alpaca"), broker, news, advisor, market_ctx)
        if decision is not None:
            logger.info("Cycle produced decision: %s %s", decision.action, decision.symbol)
    except Exception:
        logger.exception("Trading cycle failed")
    finally:
        db.close()


def _extended_job() -> None:
    """The POZA SESJĄ (extended-hours) leg -- same Alpaca equities account.
    Runs only when EXTENDED_ENABLED; shares the same pause/halt STOP gate as the
    regular cycle, with its own (cheap-ETF) whitelist and isolated per-leg state.
    NOTE: pre-/after-market session gating + whole-share LIMIT orders land in the
    next package -- until then this stays session-gated like the regular leg
    (always_open=False), so it never fires orders into a closed market."""
    settings = get_settings()
    if not settings.extended_enabled:
        return
    db = SessionLocal()
    try:
        broker = AlpacaClient(settings)
        news = NewsClient(settings)
        advisor = ClaudeAdvisor(settings)
        market_ctx = MarketContextClient()
        # Extended-hours brain: conservative profile (extended_* overrides folded in).
        decision = run_cycle(
            db, effective_settings(settings, "extended"), broker, news, advisor, market_ctx,
            venue="extended", whitelist=settings.extended_whitelist_symbols, always_open=False,
        )
        if decision is not None:
            logger.info("Extended cycle produced decision: %s %s", decision.action, decision.symbol)
    except Exception:
        logger.exception("Extended trading cycle failed")
    finally:
        db.close()


def _regime_job() -> None:
    """Keeps the dashboard's market read ("temperatura rynku" + adaptive
    aggression) CURRENT independently of trading: refreshes + caches both
    venues' regimes every interval even while the engine is stopped, the market
    is closed, or nothing triggered. Read-only (klines + macro context only);
    never places or gates an order. Best-effort -- a hiccup just leaves the last
    cached read in place."""
    settings = get_settings()
    db = SessionLocal()
    try:
        market_ctx = MarketContextClient()
        try:
            compute_and_cache_regime(
                db, effective_settings(settings, "alpaca"), AlpacaClient(settings), market_ctx,
                venue="alpaca", whitelist=[settings.benchmark_symbol],
            )
        except Exception:
            logger.warning("Regime refresh (alpaca) failed", exc_info=True)
        if settings.extended_enabled:
            try:
                compute_and_cache_regime(
                    db, effective_settings(settings, "extended"), AlpacaClient(settings),
                    market_ctx, venue="extended", whitelist=settings.extended_whitelist_symbols,
                )
            except Exception:
                logger.warning("Regime refresh (extended) failed", exc_info=True)
    except Exception:
        logger.exception("Regime refresh job failed")
    finally:
        db.close()


def _report_job() -> None:
    """Codzienne podsumowanie stanu konta jako powiadomienie PUSH (nie mail) --
    ten sam baner dostępny na żądanie w Centrum sterowania. Best-effort, ale
    LOGUJE gdy nic nie poszło (brak kluczy VAPID, brak zapisanych urządzeń) --
    w przeciwieństwie do maila to jest cichy kanał, więc bez logu nikt by się
    nie dowiedział, że codzienne podsumowanie w ogóle przestało przychodzić."""
    settings = get_settings()
    db = SessionLocal()
    try:
        sent = send_daily_summary_push(db, settings)
        if not sent:
            logger.info(
                "Daily summary push not sent (push not configured, or no subscribed device yet)"
            )
    except Exception:
        logger.exception("Daily summary push failed")
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


def prime_portfolio_snapshots() -> None:
    """Take ONE read-only portfolio snapshot per venue at boot so the dashboard
    shows the account immediately instead of 'oczekiwanie na dane' until the
    first scheduled poll (up to poll_interval minutes, and especially right
    after a history reset). Best-effort: places/cancels/reads NO order beyond
    the balance/price reads compute_portfolio already does, and never blocks or
    breaks startup if the broker is briefly unreachable."""
    settings = get_settings()
    db = SessionLocal()
    try:
        try:
            compute_portfolio(
                db, settings, AlpacaClient(settings),
                venue="alpaca", whitelist=settings.whitelist_symbols,
            )
        except Exception:
            logger.warning("Startup snapshot (equities) failed, will populate on first poll", exc_info=True)
        if settings.extended_enabled:
            try:
                compute_portfolio(
                    db, settings, AlpacaClient(settings),
                    venue="extended", whitelist=settings.extended_whitelist_symbols,
                )
            except Exception:
                logger.warning("Startup snapshot (extended) failed, will populate on first poll", exc_info=True)
    finally:
        db.close()
    # Prime the market read too, so "temperatura rynku" isn't blank until the
    # first 15-min regime refresh fires.
    try:
        _regime_job()
    except Exception:
        logger.warning("Startup regime prime failed, will populate on first refresh", exc_info=True)


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
    # Extended (24-7, same Alpaca account) venue -- the job itself no-ops unless
    # EXTENDED_ENABLED, so it's always registered and just idles until enabled.
    scheduler.add_job(
        _extended_job,
        "interval",
        minutes=settings.extended_poll_interval_minutes,
        id="extended_trading_cycle",
    )
    # Keep the market read fresh even when nothing is trading (see _regime_job).
    scheduler.add_job(
        _regime_job,
        "interval",
        minutes=15,
        id="regime_refresh",
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


def scheduler_status() -> dict:
    """Live view of the background scheduler for the Health-check panel: is it
    running, and when does each job next fire. Returns running=False if it was
    never started or got shut down (a stuck/dead scheduler)."""
    running = _scheduler is not None and getattr(_scheduler, "running", False)
    jobs = []
    if _scheduler is not None:
        for job in _scheduler.get_jobs():
            nxt = getattr(job, "next_run_time", None)
            jobs.append({"id": job.id, "next_run_at": nxt.isoformat() if nxt else None})
    return {"running": bool(running), "jobs": jobs}


def restart_scheduler() -> dict:
    """Hard-reset the scheduler (stop then start) -- the Health-check 'reset'
    for a wedged/stopped scheduler, without restarting the whole process."""
    stop_scheduler()
    start_scheduler()
    return scheduler_status()
