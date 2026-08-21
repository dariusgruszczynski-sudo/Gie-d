"""Testy ścieżek bezpieczeństwa z paczki 1: ślad audytowy operacji wrażliwych
oraz alarm po serii nieudanych logowań. Fail-closed auth i zawężenie tokenu RO
są pokryte w test_auth.py."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import routes_auth
from app.api.routes_auth import router as auth_router
from app.config import Settings, get_settings
from app.db import get_db
from app.services import audit

# ---- Ślad audytowy ---------------------------------------------------------

def test_audit_record_and_recent_newest_first(db_session):
    audit.record(db_session, "manual-trade", detail="BUY SPY $50", request=None)
    audit.record(db_session, "panic", detail="paused; sold=SPY", request=None)

    rows = audit.recent(db_session, limit=10)
    assert len(rows) == 2
    assert rows[0]["action"] == "panic"            # najnowszy pierwszy
    assert rows[1]["action"] == "manual-trade"
    assert rows[1]["detail"] == "BUY SPY $50"
    assert rows[0]["outcome"] == "ok"


def test_audit_record_never_raises_on_bad_session():
    """Zapis audytu jest best-effort: błąd (np. brak tabeli) nie może wywalić
    operacji, którą audytujemy -- wchłania wyjątek i nie rzuca dalej."""
    broken = SimpleNamespace(add=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
                             commit=lambda: None, rollback=lambda: None)
    # Nie powinno rzucić:
    audit.record(broken, "manual-trade", detail="x", request=None)


def test_client_ip_prefers_forwarded_header():
    req = SimpleNamespace(headers={"x-forwarded-for": "203.0.113.7, 10.0.0.1"},
                          client=SimpleNamespace(host="10.0.0.1"))
    assert audit.client_ip(req) == "203.0.113.7"


def test_client_ip_falls_back_to_peer():
    req = SimpleNamespace(headers={}, client=SimpleNamespace(host="198.51.100.4"))
    assert audit.client_ip(req) == "198.51.100.4"


# ---- Alarm po serii nieudanych logowań -------------------------------------

def _auth_client(db_session, settings, secret="test-secret"):
    from app import session_secret

    session_secret._session_secret = secret
    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _reset_login_tracker():
    with routes_auth._fail_lock:
        routes_auth._fail_times.clear()
        routes_auth._last_alarm_at.clear()


def test_failed_logins_trigger_one_alarm_at_threshold(db_session, monkeypatch):
    _reset_login_tracker()
    settings = Settings(dashboard_users="Darek:Dobre-Haslo-123",
                        security_alert_enabled=True, security_alert_failed_logins=3)
    client = _auth_client(db_session, settings)

    alarms = []
    monkeypatch.setattr(routes_auth.push_notifier, "send_alarm",
                        lambda db, s, **kw: alarms.append(kw) or 1)

    # Poniżej progu: żadnego alarmu.
    for _ in range(2):
        assert client.post("/api/auth/login", json={"username": "Darek", "password": "zle"}).status_code == 401
    assert alarms == []

    # Trzecia próba osiąga próg -> DOKŁADNIE jeden alarm.
    assert client.post("/api/auth/login", json={"username": "Darek", "password": "zle"}).status_code == 401
    assert len(alarms) == 1
    assert "Nieudane logowania" in alarms[0]["title"]

    # Kolejna nieudana próba w cooldownie nie sypie drugim alarmem.
    client.post("/api/auth/login", json={"username": "Darek", "password": "zle"})
    assert len(alarms) == 1


def test_failed_logins_disabled_sends_no_alarm(db_session, monkeypatch):
    _reset_login_tracker()
    settings = Settings(dashboard_users="Darek:Dobre-Haslo-123",
                        security_alert_enabled=False, security_alert_failed_logins=2)
    client = _auth_client(db_session, settings)

    alarms = []
    monkeypatch.setattr(routes_auth.push_notifier, "send_alarm",
                        lambda db, s, **kw: alarms.append(kw) or 1)

    for _ in range(5):
        client.post("/api/auth/login", json={"username": "Darek", "password": "zle"})
    assert alarms == []


def test_successful_login_clears_failure_counter(db_session, monkeypatch):
    _reset_login_tracker()
    settings = Settings(dashboard_users="Darek:Dobre-Haslo-123",
                        security_alert_enabled=True, security_alert_failed_logins=3)
    client = _auth_client(db_session, settings)
    monkeypatch.setattr(routes_auth.push_notifier, "send_alarm", lambda db, s, **kw: 1)

    client.post("/api/auth/login", json={"username": "Darek", "password": "zle"})
    client.post("/api/auth/login", json={"username": "Darek", "password": "zle"})
    # Udane logowanie zeruje licznik prób dla tego IP.
    assert client.post("/api/auth/login", json={"username": "Darek", "password": "Dobre-Haslo-123"}).status_code == 200
    with routes_auth._fail_lock:
        assert routes_auth._fail_times.get("testclient", []) == []
