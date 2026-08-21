import os
import time
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.serialization import serialize
from app.services import audit, push_notifier, risk_manager
from app.services.alpaca_client import AlpacaAPIError, AlpacaClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.strategy_profiles import effective_settings
from app.services.trading_engine import compute_portfolio, execute_manual_trade, run_cycle

router = APIRouter(prefix="/api/control", tags=["control"])


@router.get("/share-link")
def share_link(settings: Settings = Depends(get_settings)):
    """Read-only share token for the owner to build a view-only link. Lives under
    /api/control (auth-gated) so a read-only share viewer can NEVER reach it --
    the token is only ever handed to an authenticated owner. The frontend builds
    the final URL from the browser's own origin (robust behind the proxy)."""
    return {"enabled": bool(settings.share_token), "token": settings.share_token}


@router.post("/pause")
def pause(venue: str = "alpaca", db: Session = Depends(get_db), request: Request = None):
    state = risk_manager.pause(db, venue)
    audit.record(db, "pause", detail=f"venue={venue}", request=request)
    return serialize(state)


@router.post("/resume")
def resume(venue: str = "alpaca", db: Session = Depends(get_db), request: Request = None):
    state = risk_manager.resume(db, venue)
    audit.record(db, "resume", detail=f"venue={venue}", request=request)
    return serialize(state)


@router.get("/audit-log")
def audit_log(db: Session = Depends(get_db)):
    """Dziennik operacji wrażliwych (najnowsze pierwsze). Pod /api/control, więc
    dostęp TYLKO dla zalogowanego właściciela -- link RO nigdy go nie zobaczy."""
    return {"entries": audit.recent(db, limit=100)}


@router.post("/set-budget")
def set_budget(amount: float, db: Session = Depends(get_db), settings: Settings = Depends(get_settings), request: Request = None):
    """Ręczne ustawienie miesięcznego budżetu tokenów z aplikacji (bez wchodzenia
    na serwer). Zapisuje nadpisanie w bazie (wygrywa nad .env). amount<=0 zdejmuje
    nadpisanie (wraca wartość z .env)."""
    from app.services import budget_tracker

    state = risk_manager.get_state(db)
    state.claude_monthly_budget_override = max(0.0, float(amount))
    db.commit()
    audit.record(db, "set-budget", detail=f"amount={max(0.0, float(amount)):.2f}", request=request)
    return {"claude_budget": budget_tracker.get_budget_status(db, settings)}


@router.post("/reset-budget-meter")
def reset_budget_meter(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Zeruje licznik wydatku/tokenów tego miesiąca -> 'zostało' wraca do pełnego
    budżetu i automat znów może pytać Claude."""
    from app.services import budget_tracker

    state = risk_manager.get_state(db)
    state.claude_spend_usd_this_month = 0.0
    state.claude_input_tokens_this_month = 0
    state.claude_output_tokens_this_month = 0
    db.commit()
    return {"claude_budget": budget_tracker.get_budget_status(db, settings)}


def _broker_for(venue: str, settings: Settings):
    if venue == "extended":
        return AlpacaClient(settings), settings.extended_whitelist_symbols, True
    return AlpacaClient(settings), settings.whitelist_symbols, False


@router.post("/sell-all")
def sell_all(symbol: str, venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings), request: Request = None):
    """One-click full exit of a held position: sells the EXACT quantity the
    account currently holds (read live from the broker), so a dollar amount that
    rounds to more shares than held can't cause an 'insufficient qty' reject.
    Works for any held symbol -- including adopted / off-whitelist ones."""
    if venue == "extended" and not settings.extended_enabled:
        raise HTTPException(status_code=400, detail="Silnik poza sesją jest wyłączony (EXTENDED_ENABLED=false)")
    broker, whitelist, _ = _broker_for(venue, settings)
    sym = symbol.upper()
    try:
        balances = broker.get_account_balances()
    except AlpacaAPIError as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    qty = float(balances.get(sym, 0.0) or 0.0)
    if qty <= 0:
        raise HTTPException(status_code=404, detail=f"Brak pozycji {sym} do sprzedania.")
    # Allow selling a held name even if it's off the trading whitelist (adopted).
    wl = list(dict.fromkeys(list(whitelist or []) + [sym]))
    try:
        trade = execute_manual_trade(
            db, settings, broker, symbol=sym, side="SELL", quantity=qty, venue=venue, whitelist=wl
        )
    except (ValueError, AlpacaAPIError) as exc:
        audit.record(db, "sell-all", detail=f"{sym} venue={venue} FAILED", request=request, outcome="error")
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    audit.record(db, "sell-all", detail=f"{sym} qty={qty:g} venue={venue}", request=request)
    return serialize(trade)


@router.post("/set-push-mode")
def set_push_mode(mode: Literal["all", "big", "daily", "off"], db: Session = Depends(get_db), request: Request = None):
    """Tryb powiadomień push per-transakcja (Centrum sterowania): all / big /
    daily / off. Dzienne podsumowanie leci niezależnie od tego ustawienia."""
    state = risk_manager.get_state(db)
    state.push_mode = mode
    db.commit()
    audit.record(db, "set-push-mode", detail=f"mode={mode}", request=request)
    labels = {"all": "każda transakcja", "big": "tylko duże ruchy", "daily": "tylko dzienne podsumowanie", "off": "wyłączone"}
    return {"push_mode": mode, "message": f"Powiadomienia: {labels[mode]}."}


@router.post("/set-plan")
def set_plan(monthly_deposit: float = 0.0, goal: float = 0.0, db: Session = Depends(get_db), request: Request = None):
    """Zapisuje plan oszczędzania: miesięczną wpłatę i cel kwotowy (wygoda —
    panel pokazuje postęp i prognozę). Wartości <0 przycinane do 0."""
    state = risk_manager.get_state(db)
    state.monthly_deposit_plan = max(0.0, float(monthly_deposit))
    state.goal_amount = max(0.0, float(goal))
    db.commit()
    audit.record(db, "set-plan", detail=f"wpłata={state.monthly_deposit_plan:.0f} cel={state.goal_amount:.0f}", request=request)
    return {"monthly_deposit": state.monthly_deposit_plan, "goal": state.goal_amount}


@router.post("/set-widget-metric")
def set_widget_metric(metric: Literal["total", "day", "account", "positions"], db: Session = Depends(get_db), request: Request = None):
    """Co widżet iOS pokazuje jako główną liczbę (total/day/account/positions)."""
    state = risk_manager.get_state(db)
    state.widget_metric = metric
    db.commit()
    audit.record(db, "set-widget-metric", detail=f"metric={metric}", request=request)
    return {"widget_metric": metric}


@router.post("/panic")
def panic(db: Session = Depends(get_db), settings: Settings = Depends(get_settings), request: Request = None):
    """STOP WSZYSTKO (przycisk paniki): (1) wstrzymuje bota, (2) sprzedaje
    WSZYSTKIE trzymane pozycje sesji. Saldo czytane na żywo z brokera; każda
    nazwa best-effort — jedna nieudana sprzedaż nie blokuje reszty. Zwraca, co
    sprzedano i co się nie udało."""
    risk_manager.pause(db, "alpaca")
    broker = AlpacaClient(settings)
    try:
        balances = broker.get_account_balances()
    except AlpacaAPIError as exc:
        audit.record(db, "panic", detail="paused; balances read FAILED", request=request, outcome="error")
        raise HTTPException(status_code=502, detail=f"Wstrzymano bota, ale nie odczytano pozycji: {exc}") from exc
    sold: list[str] = []
    failed: list[str] = []
    for raw, q in balances.items():
        sym = str(raw).upper()
        qty = float(q or 0.0)
        if qty <= 0:
            continue
        try:
            execute_manual_trade(db, settings, broker, symbol=sym, side="SELL", quantity=qty, venue="alpaca", whitelist=[sym])
            sold.append(sym)
        except Exception:  # best-effort: nie przerywaj na jednej nazwie
            failed.append(sym)
    audit.record(db, "panic", detail=f"paused; sold={','.join(sold) or '—'}; failed={','.join(failed) or '—'}",
                 request=request, outcome="error" if failed else "ok")
    return {"paused": True, "sold": sold, "failed": failed,
            "message": f"Wstrzymano bota. Sprzedano: {len(sold)}." + (f" Nie udało się: {', '.join(failed)}." if failed else "")}


class ManualTradeRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    usdt_amount: float | None = None
    quantity: float | None = None
    venue: Literal["alpaca", "extended"] = "alpaca"

    @model_validator(mode="after")
    def check_amount(self):
        if self.usdt_amount is None and self.quantity is None:
            raise ValueError("Provide either usdt_amount or quantity")
        return self


@router.post("/manual-trade")
def manual_trade(
    req: ManualTradeRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    request: Request = None,
):
    if req.venue == "extended":
        if not settings.extended_enabled:
            raise HTTPException(status_code=400, detail="Silnik poza sesją jest wyłączony (EXTENDED_ENABLED=false)")
        broker = AlpacaClient(settings)
        whitelist = settings.extended_whitelist_symbols
    else:
        broker = AlpacaClient(settings)
        whitelist = settings.whitelist_symbols
    try:
        trade = execute_manual_trade(
            db,
            settings,
            broker,
            symbol=req.symbol.upper(),
            side=req.side,
            usdt_amount=req.usdt_amount,
            quantity=req.quantity,
            venue=req.venue,
            whitelist=whitelist,
        )
    except (ValueError, AlpacaAPIError) as exc:
        audit.record(db, "manual-trade", detail=f"{req.side} {req.symbol.upper()} venue={req.venue} FAILED",
                     request=request, outcome="error")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    amt = f"${req.usdt_amount:g}" if req.usdt_amount is not None else f"{req.quantity:g} szt."
    audit.record(db, "manual-trade", detail=f"{req.side} {req.symbol.upper()} {amt} venue={req.venue}", request=request)
    return serialize(trade)


@router.post("/run-cycle-now")
def run_cycle_now(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Forces one full Claude analysis immediately (bypassing the price/schedule
    trigger gate) instead of waiting for the scheduler's next poll -- this is
    the dashboard's "Wymuś analizę" button, so it must always produce a
    decision rather than returning 'no trigger'. Per venue (equities/extended)."""
    if venue == "extended" and not settings.extended_enabled:
        raise HTTPException(status_code=400, detail="Silnik poza sesją jest wyłączony (EXTENDED_ENABLED=false)")
    broker, whitelist, always_open = _broker_for(venue, settings)
    news = NewsClient(settings)
    advisor = ClaudeAdvisor(settings)
    market_ctx = MarketContextClient()
    try:
        decision = run_cycle(
            db, effective_settings(settings, venue), broker, news, advisor, market_ctx, force=True,
            venue=venue, whitelist=whitelist, always_open=always_open,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    return serialize(decision) if decision is not None else {"message": "Brak danych rynkowych w tym cyklu"}


@router.post("/dry-run")
def dry_run(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """SYMULACJA: odpala pełną analizę Claude na ŻYWYCH danych (jak „Przemyśl
    teraz"), ale NIC nie zleca, nie persystuje decyzji ani nie oznacza analizy
    jako zrobionej. Zwraca propozycje (co bot BY zrobił) z orientacyjnym rozmiarem
    liczonym tą samą mechaniką co egzekucja. Do sprawdzenia strategii bez ryzyka.
    Koszt Claude jest realny (wywołanie się odbyło)."""
    if venue == "extended" and not settings.extended_enabled:
        raise HTTPException(status_code=400, detail="Silnik poza sesją jest wyłączony (EXTENDED_ENABLED=false)")
    broker, whitelist, always_open = _broker_for(venue, settings)
    news = NewsClient(settings)
    advisor = ClaudeAdvisor(settings)
    market_ctx = MarketContextClient()
    try:
        result = run_cycle(
            db, effective_settings(settings, venue), broker, news, advisor, market_ctx, force=True,
            venue=venue, whitelist=whitelist, always_open=always_open, dry_run=True,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    if isinstance(result, dict):
        return result
    # Wczesny wyjątek toru (np. brak danych rynkowych) -> pusty podgląd z notką.
    return {"dry_run": True, "venue": venue, "proposals": [], "note": "Brak danych rynkowych w tym cyklu."}


@router.post("/refresh-portfolio")
def refresh_portfolio(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Reads the live account balance + current prices from the venue's broker
    and records one portfolio snapshot -- WITHOUT calling Claude and WITHOUT
    placing any order. This is the safe "sprawdź czy widzę konto" button: it
    proves the API key works and populates the dashboard (saldo, ceny, pozycje)
    on demand, at zero Claude cost and zero trading risk, even while the automat
    is stopped before START."""
    if venue == "extended" and not settings.extended_enabled:
        raise HTTPException(status_code=400, detail="Silnik poza sesją jest wyłączony (EXTENDED_ENABLED=false)")
    broker, whitelist, _ = _broker_for(venue, settings)
    try:
        portfolio = compute_portfolio(db, settings, broker, venue=venue, whitelist=whitelist)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    return {
        "total_value": portfolio["total_value_usdt"],
        "quote_balance": portfolio["usdt_balance"],
        "balances": portfolio["balances"],
        "prices": portfolio["prices"],
        "failed_symbols": portfolio["failed_symbols"],
        "quote_currency": settings.quote_currency,
    }


@router.post("/send-report-now")
def send_report_now(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Wysyła podsumowanie stanu konta jako powiadomienie push NATYCHMIAST --
    ten sam baner, który leci automatycznie raz dziennie o report_hour.
    Zastępuje mailowy raport dzienny (mail nadal działa dla pojedynczych
    transakcji, jeśli SMTP jest skonfigurowane -- patrz send_trade_alert)."""
    if not push_notifier.push_configured(settings):
        raise HTTPException(
            status_code=400,
            detail="Push nie jest skonfigurowany (brak kluczy VAPID w .env) -- zobacz Centrum sterowania.",
        )
    try:
        sent = push_notifier.send_daily_summary_push(db, settings)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    if not sent:
        raise HTTPException(status_code=404, detail="Brak zapisanych urządzeń albo brak jeszcze danych o koncie.")
    return {"message": "Podsumowanie wysłane na zapisane urządzenia."}


def _exit_after_response() -> None:
    # Small delay so the HTTP response reaches the browser before the process
    # dies. Docker's `restart: unless-stopped` policy brings the same
    # container straight back up -- this does NOT pick up new code or .env
    # changes, since those are fixed at container creation (needs
    # `docker compose up -d --build` for that).
    time.sleep(0.5)
    os._exit(0)


@router.post("/restart")
def restart(background_tasks: BackgroundTasks, db: Session = Depends(get_db), request: Request = None):
    """Restarts the backend process -- useful for clearing a stuck scheduler
    or in-memory state without SSH-ing into the server."""
    audit.record(db, "restart", detail="proces backendu", request=request)
    background_tasks.add_task(_exit_after_response)
    return {"message": "Restart zainicjowany, aplikacja wróci za kilka sekund."}
