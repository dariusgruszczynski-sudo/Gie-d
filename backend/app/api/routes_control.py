from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.serialization import serialize
from app.services import risk_manager
from app.services.binance_client import BinanceClient
from app.services.trading_engine import execute_manual_trade

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
