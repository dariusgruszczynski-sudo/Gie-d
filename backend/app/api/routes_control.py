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
from app.services.etoro_client import EToroAPIError, EToroClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.email_reporter import send_daily_report
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.trading_engine import compute_portfolio, execute_manual_trade, run_cycle

router = APIRouter(prefix="/api/control", tags=["control"])


@router.post("/pause")
def pause(db: Session = Depends(get_db)):
    state = risk_manager.pause(db)
    return serialize(state)


@router.post("/resume")
def resume(db: Session = Depends(get_db)):
    state = risk_manager.resume(db)
    return serialize(state)


class ManualTradeRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    usdt_amount: float | None = None
    quantity: float | None = None
    venue: Literal["alpaca", "etoro"] = "alpaca"

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
    if req.venue == "etoro":
        if not settings.etoro_enabled:
            raise HTTPException(status_code=400, detail="Portfel eToro jest wyłączony (ETORO_ENABLED=false)")
        broker = EToroClient(settings)
        whitelist = settings.etoro_whitelist_symbols
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
    except (ValueError, AlpacaAPIError, EToroAPIError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize(trade)


@router.post("/run-cycle-now")
def run_cycle_now(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Forces one full Claude analysis immediately (bypassing the price/schedule
    trigger gate) instead of waiting for the scheduler's next poll -- this is
    the dashboard's "Wymuś analizę" button, so it must always produce a
    decision rather than returning 'no trigger'."""
    broker = AlpacaClient(settings)
    news = NewsClient(settings)
    advisor = ClaudeAdvisor(settings)
    market_ctx = MarketContextClient()
    try:
        decision = run_cycle(db, settings, broker, news, advisor, market_ctx, force=True)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    return serialize(decision) if decision is not None else {"message": "Brak danych rynkowych z Alpaca w tym cyklu"}


@router.post("/refresh-portfolio")
def refresh_portfolio(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Reads the live account balance + current prices from Alpaca and records
    one portfolio snapshot -- WITHOUT calling Claude and WITHOUT placing any
    order. This is the safe "sprawdź czy widzę konto" button: it proves the
    API key works and populates the dashboard (saldo, ceny, pozycje) on demand,
    at zero Claude cost and zero trading risk, even while the automat is
    stopped before START."""
    broker = AlpacaClient(settings)
    try:
        portfolio = compute_portfolio(db, settings, broker)
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
    """Sends the daily email report immediately -- useful for testing SMTP
    config without waiting for the scheduled hour."""
    if not settings.smtp_username or not settings.smtp_password:
        raise HTTPException(
            status_code=400,
            detail="SMTP nie jest skonfigurowane (SMTP_USERNAME/SMTP_PASSWORD puste w .env)",
        )
    try:
        send_daily_report(db, settings)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    return {"message": f"Raport wysłany na {settings.report_recipient_email}"}


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
