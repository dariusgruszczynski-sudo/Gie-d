import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_control import router as control_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_push import router as push_router
from app.auth import SessionAuthMiddleware
from app.config import get_settings
from app.db import init_db
from app.services.scheduler import prime_portfolio_snapshots, start_scheduler, stop_scheduler
from app.session_secret import get_session_secret, init_session_secret

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_session_secret()
    # One read-only snapshot per venue so the dashboard shows the account right
    # away (no "oczekiwanie na dane" until the first poll / after a reset).
    prime_portfolio_snapshots()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="GielDarek Trading Bot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionAuthMiddleware, credentials=get_settings().dashboard_credentials, get_secret=get_session_secret)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(control_router)
app.include_router(push_router)

if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
