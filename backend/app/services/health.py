"""System health-check probes + one-click resets for the "Health check" tab.

Each probe returns a compact dict the dashboard renders as a traffic light:
  status: "ok" (green) | "warn" (amber) | "down" (red) | "off" (grey/n-a)
  action: an optional reset key the UI turns into a button (see RESET_ACTIONS)

Probes are deliberately read-only and each swallows its own errors -- a single
failing integration reports "down" instead of 500-ing the whole panel. The
external probes (broker, news) are the slow ones, so callers run this off a
threadpool endpoint and show a spinner.
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone

from sqlalchemy import func, select

from app.config import Settings
from app.db import SessionLocal
from app.models import Decision, PortfolioSnapshot, PushSubscription
from app.services import budget_tracker, push_notifier, risk_manager, scheduler
from app.services.alpaca_client import AlpacaClient
from app.services.news_client import NewsClient

logger = logging.getLogger(__name__)


def _check(key, label, group, status, detail, action=None):
    return {"key": key, "label": label, "group": group, "status": status, "detail": detail, "action": action}


def _age_minutes(ts: datetime | None) -> float | None:
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts).total_seconds() / 60.0


# --- individual probes ------------------------------------------------------
# Each takes (db, settings) and returns one _check dict. Kept tiny so they can
# be fanned out concurrently.


def _probe_alpaca_equities(db, settings):
    try:
        bals = AlpacaClient(settings).get_account_balances()
        held = sum(1 for k, v in bals.items() if k != settings.quote_currency and (v or 0) > 0)
        return _check("alpaca_equities", "Alpaca — konto (US)", "Integracje", "ok",
                      f"Konto osiągalne · {held} pozycji · {'PAPER' if settings.alpaca_paper else 'LIVE'}")
    except Exception as exc:
        return _check("alpaca_equities", "Alpaca — konto (US)", "Integracje", "down", f"{type(exc).__name__}: {exc}")


def _probe_alpaca_market_data(db, settings):
    try:
        rows = AlpacaClient(settings).get_klines(settings.benchmark_symbol, settings.signal_timeframe, 5)
        if rows:
            return _check("alpaca_data", "Dane rynkowe (US)", "Integracje", "ok",
                          f"Świece {settings.benchmark_symbol} OK ({len(rows)})")
        return _check("alpaca_data", "Dane rynkowe (US)", "Integracje", "warn", "Brak świec w odpowiedzi")
    except Exception as exc:
        return _check("alpaca_data", "Dane rynkowe (US)", "Integracje", "down", f"{type(exc).__name__}: {exc}")


def _probe_alpaca_extended(db, settings):
    if not settings.extended_enabled:
        return _check("alpaca_extended", "Alpaca — poza sesją", "Integracje", "off", "Silnik poza sesją wyłączony")
    try:
        AlpacaClient(settings).get_account_balances()
        return _check("alpaca_extended", "Alpaca — poza sesją", "Integracje", "ok", "Konto osiągalne (poza sesją)")
    except Exception as exc:
        return _check("alpaca_extended", "Alpaca — poza sesją", "Integracje", "down", f"{type(exc).__name__}: {exc}")


def _probe_claude(db, settings):
    # Cost/budget is intentionally NOT surfaced here anymore -- tokens are used
    # for many things and the spend is not a meaningful health signal. We only
    # confirm the brain has a key to reach the model.
    if not settings.anthropic_api_key:
        return _check("claude", "Claude (mózg)", "Integracje", "down", "Brak ANTHROPIC_API_KEY w .env")
    return _check("claude", "Claude (mózg)", "Integracje", "ok", "Klucz OK — model osiągalny")


def _probe_news(db, settings):
    """Data-level probe: nie sprawdza samego POŁĄCZENIA, tylko czy REALNIE
    spływają nagłówki -- i czy jest ich tyle, ile trzeba do decyzji. Poniżej
    progu blackoutu (news_min_headlines) raportuje 'down', bo silnik wstrzymuje
    wtedy nowe wejścia (patrz trading_engine._news_blackout_active)."""
    try:
        keyed_sources = []
        if getattr(settings, "alpaca_api_key", "") and getattr(settings, "alpaca_api_secret", ""):
            keyed_sources.append("Alpaca")
        if getattr(settings, "alpha_vantage_api_key", ""):
            keyed_sources.append("AlphaVantage")
        if getattr(settings, "finnhub_api_key", ""):
            keyed_sources.append("Finnhub")
        if getattr(settings, "newsapi_api_key", ""):
            keyed_sources.append("NewsAPI")
        if getattr(settings, "serpapi_api_key", ""):
            keyed_sources.append("SerpAPI")
        keyed = (" · keyed: " + ", ".join(keyed_sources)) if keyed_sources else " · tylko RSS (brak keyed)"

        headlines = NewsClient(settings).get_headlines(
            (settings.whitelist_symbols[:2] + settings.extended_whitelist_symbols[:1]), limit=40
        )
        n = len(headlines)
        floor = settings.news_min_headlines if getattr(settings, "news_blackout_halt_enabled", False) else 1
        if n < floor:
            return _check("news", "Newsy (dane)", "Integracje", "down",
                          f"BLACKOUT: {n} nagłówków < próg {floor} — handel wstrzymany{keyed}")
        if n >= 15:
            return _check("news", "Newsy (dane)", "Integracje", "ok", f"{n} nagłówków spływa{keyed}")
        return _check("news", "Newsy (dane)", "Integracje", "warn", f"Tylko {n} nagłówków (chudo){keyed}")
    except Exception as exc:
        return _check("news", "Newsy (dane)", "Integracje", "down", f"{type(exc).__name__}: {exc}")


def _probe_anthropic_usage(db, settings):
    """Realne zużycie Claude prosto od Anthropic (Admin API), gdy skonfigurowany
    Admin key; inaczej lokalny szacunek aplikacji (też live)."""
    from app.services import anthropic_usage, budget_tracker

    key = getattr(settings, "anthropic_admin_api_key", "") or ""
    b = budget_tracker.get_budget_status(db, settings)
    remaining = b["claude_budget_remaining_usd"]
    exhausted = settings.claude_pause_trading_at_budget and b["claude_monthly_budget_usd"] > 0 and remaining <= 0
    if not key:
        status = "down" if exhausted else "warn"
        note = " — WYCZERPANY, handel wstrzymany (kliknij reset)" if exhausted else ""
        return _check("anthropic_usage", "Tokeny Claude (koszt)", "Integracje", status,
                      f"Zostało ${remaining:.2f} z ${b['claude_monthly_budget_usd']:.0f} "
                      f"(wydane ${b['claude_spend_usd_this_month']:.2f}){note}",
                      action="reset_budget_meter")
    u = anthropic_usage.month_to_date(key)
    if u is None:
        return _check("anthropic_usage", "Tokeny Claude (koszt)", "Integracje", "down",
                      "Admin API nieosiągalne — sprawdź ANTHROPIC_ADMIN_API_KEY (musi być kluczem ADMIN)",
                      action="reset_budget_meter")
    tot_m = (u["input_tokens"] + u["output_tokens"]) / 1e6
    return _check("anthropic_usage", "Tokeny Claude (koszt)", "Integracje", "ok",
                  f"REALNY koszt m-c: ${u['cost_usd']:.2f} · {tot_m:.2f}M tok "
                  f"(in {u['input_tokens'] / 1e6:.2f}M / out {u['output_tokens'] / 1e6:.2f}M)",
                  action="reset_budget_meter")


def _probe_database(db, settings):
    try:
        db.execute(select(func.count(PortfolioSnapshot.id))).scalar()
        return _check("database", "Baza danych", "Połączenia", "ok", "SQLite odpowiada")
    except Exception as exc:
        return _check("database", "Baza danych", "Połączenia", "down", f"{type(exc).__name__}: {exc}")


def _probe_snapshots(db, settings):
    latest = db.execute(
        select(PortfolioSnapshot.timestamp).order_by(PortfolioSnapshot.timestamp.desc()).limit(1)
    ).scalar_one_or_none()
    age = _age_minutes(latest)
    if age is None:
        return _check("snapshots", "Snapshoty portfela", "Połączenia", "warn", "Brak snapshotów",
                      action="refresh_snapshots")
    if age <= 30:
        return _check("snapshots", "Snapshoty portfela", "Połączenia", "ok", f"Ostatni {age:.0f} min temu",
                      action="refresh_snapshots")
    if age <= 180:
        return _check("snapshots", "Snapshoty portfela", "Połączenia", "warn", f"Ostatni {age:.0f} min temu",
                      action="refresh_snapshots")
    return _check("snapshots", "Snapshoty portfela", "Połączenia", "down", f"Nieświeże ({age / 60:.1f} h temu)",
                  action="refresh_snapshots")


def _probe_push(db, settings):
    if not push_notifier.push_configured(settings):
        return _check("push", "Powiadomienia push", "Połączenia", "off", "VAPID nieskonfigurowany")
    subs = db.execute(select(func.count(PushSubscription.id))).scalar() or 0
    if subs > 0:
        return _check("push", "Powiadomienia push", "Połączenia", "ok", f"{subs} urządzeń zapisanych")
    return _check("push", "Powiadomienia push", "Połączenia", "warn", "Skonfigurowany, ale 0 urządzeń")


def _probe_scheduler(db, settings):
    st = scheduler.scheduler_status()
    if not st["running"]:
        return _check("scheduler", "Scheduler (automat)", "Funkcjonalności", "down", "NIE działa — zablokowany",
                      action="restart_scheduler")
    njobs = len(st["jobs"])
    return _check("scheduler", "Scheduler (automat)", "Funkcjonalności", "ok" if njobs else "warn",
                  f"Działa · {njobs} zadań", action="restart_scheduler")


def _probe_automat_us(db, settings):
    state = risk_manager.get_state(db)
    if state.is_halted:
        return _check("automat_us", "Silnik US", "Funkcjonalności", "down",
                      f"HALT: {state.halted_reason or 'bezpiecznik'}", action="clear_halt")
    if state.is_paused:
        return _check("automat_us", "Silnik US", "Funkcjonalności", "warn", "Zapauzowany", action="resume_alpaca")
    return _check("automat_us", "Silnik US", "Funkcjonalności", "ok", "Aktywny")


def _probe_automat_extended(db, settings):
    if not settings.extended_enabled:
        return _check("automat_extended", "Silnik poza sesją", "Funkcjonalności", "off", "Wyłączony")
    state = risk_manager.get_state(db)
    if state.extended_paused:
        return _check("automat_extended", "Silnik poza sesją", "Funkcjonalności", "warn", "Zapauzowany",
                      action="resume_extended")
    return _check("automat_extended", "Silnik poza sesją", "Funkcjonalności", "ok", "Aktywny")


def _probe_loop_freshness(db, settings):
    last = db.execute(
        select(Decision.timestamp).where(Decision.venue == "alpaca").order_by(Decision.timestamp.desc()).limit(1)
    ).scalar_one_or_none()
    age = _age_minutes(last)
    interval = max(settings.poll_interval_minutes, 1)
    if age is None:
        return _check("loop_us", "Pętla decyzji US", "Funkcjonalności", "warn", "Brak decyzji w historii")
    # Allow a few missed polls before flagging (equities also idle outside the
    # session, so this is a soft, informational signal rather than a hard error).
    if age <= interval * 4:
        return _check("loop_us", "Pętla decyzji US", "Funkcjonalności", "ok", f"Ostatnia {age:.0f} min temu")
    return _check("loop_us", "Pętla decyzji US", "Funkcjonalności", "warn",
                  f"Ostatnia {age:.0f} min temu (poza sesją to normalne)")


_PROBES = [
    _probe_alpaca_equities,
    _probe_alpaca_market_data,
    _probe_alpaca_extended,
    _probe_claude,
    _probe_anthropic_usage,
    _probe_news,
    _probe_database,
    _probe_snapshots,
    _probe_push,
    _probe_scheduler,
    _probe_automat_us,
    _probe_automat_extended,
    _probe_loop_freshness,
]


def run_health_checks(db, settings: Settings) -> dict:
    """Fan every probe out concurrently (external calls dominate the latency),
    then summarize. Each probe gets its OWN db session -- SQLAlchemy sessions
    aren't safe to share across threads."""

    def _run(probe):
        s = SessionLocal()
        try:
            return probe(s, settings)
        except Exception as exc:  # a probe must never take the panel down
            logger.warning("Health probe %s crashed", getattr(probe, "__name__", "?"), exc_info=True)
            return _check(getattr(probe, "__name__", "?"), "Nieznany test", "Funkcjonalności", "down",
                          f"{type(exc).__name__}: {exc}")
        finally:
            s.close()

    with ThreadPoolExecutor(max_workers=len(_PROBES)) as pool:
        checks = list(pool.map(_run, _PROBES))

    order = {"down": 0, "warn": 1, "off": 2, "ok": 3}
    worst = min((c["status"] for c in checks), key=lambda s: order[s], default="ok")
    counts = {k: sum(1 for c in checks if c["status"] == k) for k in ("ok", "warn", "down", "off")}
    return {"overall": worst, "counts": counts, "checks": checks, "checked_at": datetime.now(timezone.utc).isoformat()}


# --- resets -----------------------------------------------------------------
# Keyed by the `action` a probe attaches. Each returns a short human message.


def _reset_budget_meter(db, settings):
    state = risk_manager.get_state(db)
    state.claude_spend_usd_this_month = 0.0
    state.claude_input_tokens_this_month = 0
    state.claude_output_tokens_this_month = 0
    db.commit()
    return "Licznik tokenów/wydatku wyzerowany — 'zostało' wraca do pełnego budżetu, automat znów może pytać Claude."


def _reset_resume_alpaca(db, settings):
    risk_manager.resume(db, "alpaca")
    return "Silnik US wznowiony (halt i pauza zdjęte)."


def _reset_resume_extended(db, settings):
    risk_manager.resume(db, "extended")
    return "Silnik poza sesją wznowiony."


def _reset_clear_halt(db, settings):
    risk_manager.resume(db, "alpaca")
    return "Bezpiecznik (halt) zdjęty, baseline strat przeliczy się na nowo."


def _reset_refresh_snapshots(db, settings):
    scheduler.prime_portfolio_snapshots()
    return "Snapshoty portfela odświeżone dla obu silników."


def _reset_restart_scheduler(db, settings):
    st = scheduler.restart_scheduler()
    return f"Scheduler zrestartowany — działa, {len(st['jobs'])} zadań."


def _reset_rebaseline_pnl(db, settings):
    """Re-anchor the day/week P&L baselines (and the all-time peak) to the
    CURRENT combined account value. Use after an external cash move -- an eToro
    top-up or a withdrawal isn't trading profit/loss, but it jumps the account
    total, so without re-baselining "zysk dziś/tydzień" reads a fake gain/loss.
    Resets both windows to 'from now' because a mid-period deposit leaves no
    clean earlier baseline."""
    from app.api.routes_dashboard import _account_view  # lazy: avoid import cycle

    account = _account_view(db)
    if account is None:
        return "Brak danych o koncie — najpierw odśwież snapshoty, potem przelicz P&L."
    total = account["total_value"]
    state = risk_manager.get_state(db)
    today = date.today().isoformat()
    state.day_start_value = total
    state.day_start_date = today
    state.week_start_value = total
    state.week_start_date = today
    # Re-anchor the drawdown peak too, so a deposit doesn't inflate the peak and
    # make a later, normal dip look like a halt-worthy drawdown.
    state.peak_account_value = total
    # Re-anchor the SPY benchmark as well. alpha = konto - (SPY od baseline'u):
    # a deposit jumps the account total but NOT the benchmark, so without this a
    # wpłata would fake an equal "outperformance vs SPY". Restart the comparison
    # from now (like the day/week windows): baseline value = current total,
    # baseline SPY price = current SPY. Alpha startuje od zera od tej wpłaty.
    from app.api.routes_dashboard import _latest_snapshot  # lazy: avoid import cycle

    snap = _latest_snapshot(db, "alpaca")
    spy_now = None
    if snap is not None:
        try:
            import json

            spy_now = json.loads(snap.prices_json or "{}").get(settings.benchmark_symbol)
        except (TypeError, ValueError):
            spy_now = None
    if spy_now and spy_now > 0:
        state.benchmark_start_value = total
        state.benchmark_start_price = spy_now
        state.benchmark_start_date = today
    db.commit()
    bench_note = "" if (spy_now and spy_now > 0) else " (benchmark SPY nietknięty — brak ceny SPY w ostatnim snapshocie; odśwież snapshoty i powtórz)"
    return f"P&L przeliczony od nowa — baseline dnia/tygodnia, szczyt i benchmark SPY = ${total:,.2f}. Zysk i alfa startują od zera.{bench_note}"


def _reset_fresh_start(db, settings):
    """ŚWIEŻY START pomiaru — dla „zresetuj statystyki od ostatniej zmiany" +
    „wpłata nie ma być liczona jako zysk" w jednym:
      1) stempluje stats_epoch = TERAZ, więc skuteczność/edge liczą się od zera
         (historia transakcji ZOSTAJE — nic nie kasujemy),
      2) re-kotwiczy baseline dnia/tygodnia, szczyt i benchmark SPY do bieżącego
         stanu (rebaseline_pnl), więc wpłata/wypłata nie udaje zysku ani obsunięcia.
    """
    from datetime import datetime, timezone

    state = risk_manager.get_state(db)
    state.stats_epoch = datetime.now(timezone.utc).isoformat()
    db.commit()
    base = _reset_rebaseline_pnl(db, settings)
    return "Świeży start — skuteczność i edge liczone OD TERAZ (historia zostaje). " + base


def _reset_restart_app(db, settings):
    """Twardy restart CAŁEJ aplikacji bez SSH: ubijamy własny proces (SIGTERM),
    a Docker (restart: unless-stopped w docker-compose.yml) podnosi kontener z
    powrotem w kilka sekund. To czyści zawieszone stany (np. zacinający się
    guzik / wiszący wątek). Zabójstwo odpalamy z KRÓTKIM opóźnieniem w osobnym
    wątku, żeby ta odpowiedź HTTP zdążyła wrócić do przeglądarki PRZED zejściem
    procesu. Otwarte pozycje są bezpieczne -- stan siedzi w bazie (wolumen),
    a scheduler wstaje od nowa po restarcie."""
    import os
    import signal
    import threading
    import time

    def _die():
        time.sleep(1.2)
        os.kill(os.getpid(), signal.SIGTERM)

    threading.Thread(target=_die, daemon=True).start()
    return "Restartuję aplikację… wróci za ~10 s. Odśwież stronę za chwilę."


RESET_ACTIONS = {
    "restart_app": _reset_restart_app,
    "reset_budget_meter": _reset_budget_meter,
    "resume_alpaca": _reset_resume_alpaca,
    "resume_extended": _reset_resume_extended,
    "clear_halt": _reset_clear_halt,
    "refresh_snapshots": _reset_refresh_snapshots,
    "restart_scheduler": _reset_restart_scheduler,
    "rebaseline_pnl": _reset_rebaseline_pnl,
    "fresh_start": _reset_fresh_start,
}


def run_reset(action: str, db, settings: Settings) -> dict:
    fn = RESET_ACTIONS.get(action)
    if fn is None:
        raise KeyError(action)
    message = fn(db, settings)
    return {"action": action, "message": message}
