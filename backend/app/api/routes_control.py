from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.serialization import serialize
from app.services import risk_manager
from app.services.binance_client import BinanceClient
from app.services.claude_advisor import ClaudeAdvisor
from app.services.email_reporter import send_daily_report
from app.services.market_context import MarketContextClient
from app.services.news_client import NewsClient
from app.services.trading_engine import execute_manual_trade, run_cycle

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
    binance = BinanceClient(settings)
    try:
        trade = execute_manual_trade(
            db,
            settings,
            binance,
            symbol=req.symbol.upper(),
            side=req.side,
            usdt_amount=req.usdt_amount,
            quantity=req.quantity,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize(trade)


@router.post("/run-cycle-now")
def run_cycle_now(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    """Forces one analysis cycle immediately instead of waiting for the
    scheduler's next poll -- useful for testing/debugging without needing to
    wait POLL_INTERVAL_MINUTES."""
    binance = BinanceClient(settings)
    news = NewsClient(settings)
    advisor = ClaudeAdvisor(settings)
    market_ctx = MarketContextClient()
    try:
        decision = run_cycle(db, settings, binance, news, advisor, market_ctx)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc
    return serialize(decision) if decision is not None else {"message": "Brak wyzwolenia (no trigger) w tym cyklu"}


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
