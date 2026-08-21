import json
import logging
import math
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.db import SessionLocal
from app.models import SystemState
from app.services.alpaca_client import AlpacaClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services import market_hours, news_client
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.push_notifier import send_daily_summary_push
from app.services.strategy_profiles import effective_settings
from app.services.trading_engine import build_alpaca_universe, compute_and_cache_regime, compute_portfolio, migrate_extended_into_session, run_cycle
from app.services.whitelist_review import get_extended_whitelist, run_whitelist_review

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
        eff = effective_settings(settings, "alpaca")
        # Dynamiczne uniwersum (whitelista zbędna): trzymane + trendujące w
        # newsach (walidowane) + seed. Błąd -> None -> run_cycle wraca do stałej
        # whitelisty, więc discovery nigdy nie psuje bazowego zachowania.
        universe = None
        if eff.dynamic_universe_enabled:
            try:
                universe = build_alpaca_universe(db, eff, broker, news)
            except Exception:
                logger.warning("Budowa dynamicznego uniwersum padła, fallback do whitelisty", exc_info=True)
                universe = None
        decision = run_cycle(db, eff, broker, news, advisor, market_ctx, whitelist=universe)
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
        # Whitelist comes from the DB (auto-managed by the Friday review), not the
        # static config, so add/remove takes effect without a redeploy.
        decision = run_cycle(
            db, effective_settings(settings, "extended"), broker, news, advisor, market_ctx,
            venue="extended", whitelist=get_extended_whitelist(db, settings), always_open=False,
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
        # Grzej cache sesji rynkowej w TLE, żeby /api/status nigdy nie musiało
        # dzwonić do Alpaca synchronicznie (patrz _serialize_session_info).
        try:
            market_hours.get_session_info(AlpacaClient(settings), force_refresh=True)
        except Exception:
            logger.warning("Session-info warmup failed", exc_info=True)
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
                    market_ctx, venue="extended", whitelist=get_extended_whitelist(db, settings),
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


def _db_backup_job() -> None:
    """Codzienna kopia zapasowa bazy SQLite (patrz db_backup). Best-effort."""
    from app.services import db_backup

    settings = get_settings()
    try:
        db_backup.run_backup(settings)
    except Exception:
        logger.exception("Kopia bazy (job) nie powiodła się")


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


def _parse_feed_pairs(raw: str | None) -> list[tuple[str, str]]:
    """Odczyt trwałej listy [[nazwa, url], ...] z kolumny DB -> lista krotek,
    odporny na śmieci (pomija wpisy o złym kształcie)."""
    try:
        data = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    out: list[tuple[str, str]] = []
    for x in data:
        if isinstance(x, (list, tuple)) and len(x) == 2 and x[0] and x[1]:
            out.append((str(x[0]), str(x[1])))
    return out


def load_discovered_feeds() -> None:
    """Przy starcie: wczytaj auto-odkryte feedy z DB do runtime'owego cache w
    news_client, żeby zakładka Newsy i fetchery używały ich OD RAZU (przed
    pierwszym codziennym odkrywaniem)."""
    db = SessionLocal()
    try:
        state = db.get(SystemState, 1)
        if state is not None:
            news_client.set_discovered_feeds(_parse_feed_pairs(state.discovered_feeds_json))
    except Exception:
        logger.warning("Nie udało się wczytać odkrytych feedów z DB", exc_info=True)
    finally:
        db.close()


def _news_discovery_job() -> None:
    """Raz dziennie: odkryj ~10% NOWYCH, osiągalnych źródeł newsów i dopisz do
    aktywnej listy (trwałe w DB). Rewaliduje wcześniej odkryte -- te, które
    przestały odpowiadać, wypadają. Wyłącznie próbne odczyty (read-only)."""
    settings = get_settings()
    if not settings.news_discovery_enabled:
        return
    db = SessionLocal()
    try:
        state = db.get(SystemState, 1)
        if state is None:
            return
        current = _parse_feed_pairs(state.discovered_feeds_json)
        news_client.set_discovered_feeds(current)
        # Rewaliduj już-odkryte: zostaw tylko te, które nadal odpowiadają.
        kept = [(n, u) for (n, u) in current if news_client.probe_feed(n, u)]
        news_client.set_discovered_feeds(kept)
        # Budżet: ~10% wbudowanej listy na przebieg (min 1 nowe źródło).
        budget = max(1, math.ceil(len(news_client.RSS_FEEDS) * settings.news_discovery_max_ratio))
        found = news_client.discover_feeds(budget)
        merged = kept + found
        news_client.set_discovered_feeds(merged)
        state.discovered_feeds_json = json.dumps([[n, u] for (n, u) in merged], ensure_ascii=False)
        state.discovered_feeds_meta_json = json.dumps({
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "added": len(found),
            "dropped": len(current) - len(kept),
            "total": len(merged),
        }, ensure_ascii=False)
        db.commit()
        logger.info("News discovery: +%s -%s (razem %s odkrytych)", len(found), len(current) - len(kept), len(merged))
    except Exception:
        logger.exception("News discovery failed")
    finally:
        db.close()


def _whitelist_review_job() -> None:
    """Friday-night auto-review of the POZA SESJĄ ETF whitelist. Only updates the
    DB list + pushes a summary -- removed-and-held names are force-closed by the
    next pre-market cycle (market is closed now, so we place no order here)."""
    settings = get_settings()
    if not settings.extended_whitelist_review_enabled:
        return
    db = SessionLocal()
    try:
        result = run_whitelist_review(db, settings, AlpacaClient(settings))
        logger.info("Whitelist review: +%s -%s", result["added"], result["removed"])
    except Exception:
        logger.exception("Whitelist review failed")
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
        # Jeden silnik: gdy POZA SESJĄ jest wyłączona, przenieś jej pozycje do
        # portfela sesji ZANIM zrobimy startowy snapshot -- wtedy pierwszy
        # snapshot alpaca już obejmuje te (teraz sesyjne) pozycje, a silnik
        # sesyjny zajmie się nimi po otwarciu rynku. To jedno konto Alpaca, więc
        # nic się nie przelewa; to tylko zmiana właściciela pozycji.
        if not settings.extended_enabled:
            try:
                migrate_extended_into_session(db)
            except Exception:
                logger.warning("Migracja POZA SESJĄ -> sesja nie powiodła się (spróbuję przy następnym starcie)", exc_info=True)
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
                    venue="extended", whitelist=get_extended_whitelist(db, settings),
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
    # First-run news-source discovery so a fresh deploy doesn't wait a full day
    # for its first extra feeds (runs in this background daemon thread already).
    try:
        _news_discovery_job()
    except Exception:
        logger.warning("Startup news discovery failed, will retry on the daily job", exc_info=True)


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    settings = get_settings()
    # Warm the auto-discovered news-feed cache from DB up front, so the Newsy tab
    # already reads yesterday's finds before today's discovery job runs.
    load_discovered_feeds()
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
    # Friday-night whitelist review: 20:15 ET (America/New_York, so DST-correct),
    # i.e. right AFTER the after-market close at 20:00. Re-picks the POZA SESJĄ
    # ETF whitelist from live candidate prices.
    scheduler.add_job(
        _whitelist_review_job,
        CronTrigger(day_of_week="fri", hour=20, minute=15, timezone="America/New_York"),
        id="whitelist_review",
    )
    # Codzienna kopia zapasowa bazy SQLite (job no-op, gdy wyłączona / nie-SQLite).
    if settings.db_backup_enabled:
        scheduler.add_job(
            _db_backup_job,
            CronTrigger(hour=settings.db_backup_hour, minute=30, timezone=settings.report_timezone),
            id="db_backup",
        )
    # Codzienne auto-odkrywanie źródeł newsów (~10% nowych osiągalnych feedów).
    if settings.news_discovery_enabled:
        scheduler.add_job(
            _news_discovery_job,
            CronTrigger(hour=settings.news_discovery_hour, minute=20, timezone=settings.report_timezone),
            id="news_discovery",
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
