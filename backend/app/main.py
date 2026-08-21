import os
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_auth import router as auth_router
from app.api.routes_control import router as control_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_health import router as health_router
from app.api.routes_push import router as push_router
from app.auth import SessionAuthMiddleware
from app.config import get_settings
from app.db import init_db
from app.logging_setup import configure_logging
from app.security_headers import SecurityHeadersMiddleware
from app.services.scheduler import prime_portfolio_snapshots, start_scheduler, stop_scheduler
from app.session_secret import get_session_secret, init_session_secret

configure_logging()

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_session_secret()
    start_scheduler()
    # Priming (snapshot z brokera + odczyt reżimu) robi BLOKUJĄCE wywołania
    # sieciowe i potrafi trwać dziesiątki sekund. NIE wolno nim blokować startu
    # serwera: lifespan-startup biegnie PRZED rozpoczęciem obsługi żądań, więc
    # dopóki priming nie skończy, apka nie oddaje ani /api/status, ani plików --
    # to była przyczyna "panel bez bebechów" po każdym restarcie. Odpalamy w tle
    # (osobny wątek, żeby nie zablokować pętli zdarzeń); snapshoty dojdą za chwilę,
    # a dashboard i tak od razu pokazuje ostatni znany stan z bazy.
    threading.Thread(target=prime_portfolio_snapshots, name="prime", daemon=True).start()
    yield
    stop_scheduler()


app = FastAPI(title="GielDarek Trading Bot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionAuthMiddleware,
    credentials=get_settings().dashboard_credentials,
    get_secret=get_session_secret,
    get_share_token=lambda: get_settings().share_token,
)
# Dodane OSTATNIE = warstwa NAJBARDZIEJ zewnętrzna: nagłówki bezpieczeństwa
# (HSTS itd.) trafiają na KAŻDĄ odpowiedź, także 401/503 z bramki logowania.
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(control_router)
app.include_router(health_router)
app.include_router(push_router)

if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="static")
