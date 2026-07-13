import os
import time
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.serialization import serialize
from app.services import risk_manager
from app.services.alpaca_client import AlpacaAPIError, AlpacaClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services import push_notifier
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
def pause(venue: str = "alpaca", db: Session = Depends(get_db)):
    state = risk_manager.pause(db, venue)
    return serialize(state)


@router.post("/resume")
def resume(venue: str = "alpaca", db: Session = Depends(get_db)):
    state = risk_manager.resume(db, venue)
    return serialize(state)


def _broker_for(venue: str, settings: Settings):
    if venue == "crypto":
        return AlpacaClient(settings, asset_class="crypto"), settings.crypto_whitelist_symbols, True
    return AlpacaClient(settings), settings.whitelist_symbols, False


@router.post("/sell-all")
def sell_all(symbol: str, venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """One-click full exit of a held position: sells the EXACT quantity the
    account currently holds (read live from the broker), so a dollar amount that
    rounds to more shares than held can't cause an 'insufficient qty' reject.
    Works for any held symbol -- including adopted / off-whitelist ones."""
    if venue == "crypto" and not settings.crypto_enabled:
        raise HTTPException(status_code=400, detail="Silnik krypto jest wyłączony (CRYPTO_ENABLED=false)")
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
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    return serialize(trade)


class ManualTradeRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    usdt_amount: float | None = None
    quantity: float | None = None
    venue: Literal["alpaca", "crypto"] = "alpaca"

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
):
    if req.venue == "crypto":
        if not settings.crypto_enabled:
            raise HTTPException(status_code=400, detail="Portfel krypto jest wyłączony (CRYPTO_ENABLED=false)")
        broker = AlpacaClient(settings, asset_class="crypto")
        whitelist = settings.crypto_whitelist_symbols
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize(trade)


@router.post("/run-cycle-now")
def run_cycle_now(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Forces one full Claude analysis immediately (bypassing the price/schedule
    trigger gate) instead of waiting for the scheduler's next poll -- this is
    the dashboard's "Wymuś analizę" button, so it must always produce a
    decision rather than returning 'no trigger'. Per venue (equities/crypto)."""
    if venue == "crypto" and not settings.crypto_enabled:
        raise HTTPException(status_code=400, detail="Portfel krypto jest wyłączony (CRYPTO_ENABLED=false)")
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


@router.post("/refresh-portfolio")
def refresh_portfolio(venue: str = "alpaca", db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Reads the live account balance + current prices from the venue's broker
    and records one portfolio snapshot -- WITHOUT calling Claude and WITHOUT
    placing any order. This is the safe "sprawdź czy widzę konto" button: it
    proves the API key works and populates the dashboard (saldo, ceny, pozycje)
    on demand, at zero Claude cost and zero trading risk, even while the automat
    is stopped before START."""
    if venue == "crypto" and not settings.crypto_enabled:
        raise HTTPException(status_code=400, detail="Portfel krypto jest wyłączony (CRYPTO_ENABLED=false)")
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
def restart(background_tasks: BackgroundTasks):
    """Restarts the backend process -- useful for clearing a stuck scheduler
    or in-memory state without SSH-ing into the server."""
    background_tasks.add_task(_exit_after_response)
    return {"message": "Restart zainicjowany, aplikacja wróci za kilka sekund."}
