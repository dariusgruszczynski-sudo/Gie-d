"""Web Push (VAPID) powiadomienia na telefon / Apple Watch przez PWA.

Wysyła krótkie powiadomienie przy KAŻDEJ realnej transakcji: co, ile, po ile,
i jaki jest stan konta. Wszystko best-effort -- brak kluczy VAPID, brak
biblioteki pywebpush albo błąd sieci NIGDY nie wywraca ścieżki handlu (to samo
podejście co email_reporter): łapiemy i logujemy, handel leci dalej.

Martwe subskrypcje (push service zwraca 404/410) są automatycznie usuwane, więc
lista nie puchnie o telefony, które odinstalowały apkę."""

import json
import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import PortfolioSnapshot, PushSubscription
from app.services import budget_tracker, risk_manager, scorecard

logger = logging.getLogger(__name__)

try:  # pywebpush jest opcjonalny -- bez niego push po prostu nie działa.
    from pywebpush import WebPushException, webpush

    _HAVE_PYWEBPUSH = True
except Exception:  # pragma: no cover - zależne od środowiska
    webpush = None  # type: ignore
    WebPushException = Exception  # type: ignore
    _HAVE_PYWEBPUSH = False


def push_configured(settings: Settings) -> bool:
    """Czy push jest w ogóle skonfigurowany (klucze + biblioteka + włącznik)."""
    return bool(
        settings.push_enabled
        and settings.vapid_public_key
        and settings.vapid_private_key
        and _HAVE_PYWEBPUSH
    )


def _venue_label(venue: str) -> str:
    return "Poza sesją" if venue == "extended" else "Akcje US"


def _fmt_usd(v: float) -> str:
    return f"${v:,.2f}"


def send_to_all(
    db: Session,
    settings: Settings,
    *,
    title: str,
    body: str,
    tag: str = "gieldarek",
    url: str = "/",
    data: dict | None = None,
) -> int:
    """Rozsyła jedno powiadomienie do wszystkich zapisanych urządzeń. Zwraca
    liczbę udanych wysyłek. Nie rzuca wyjątków -- to funkcja best-effort."""
    if not push_configured(settings):
        return 0

    subs = list(db.execute(select(PushSubscription)).scalars())
    if not subs:
        return 0

    payload = json.dumps(
        {"title": title, "body": body, "tag": tag, "url": url, "data": data or {}}
    )
    vapid_claims = {"sub": settings.vapid_subject}
    dead: list[str] = []
    sent = 0

    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims=dict(vapid_claims),
                ttl=600,
            )
            sent += 1
        except WebPushException as exc:  # type: ignore[misc]
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                dead.append(sub.endpoint)  # subskrypcja martwa -- do wyrzucenia
            else:
                logger.warning("Web push failed (%s): %s", status, exc)
        except Exception as exc:  # pragma: no cover - defensywnie
            logger.warning("Web push error: %s", exc)

    if dead:
        db.execute(delete(PushSubscription).where(PushSubscription.endpoint.in_(dead)))
        db.commit()
        logger.info("Pruned %d dead push subscription(s)", len(dead))

    return sent


def send_trade_push(db: Session, settings: Settings, trade, account_total: float | None = None) -> None:
    """Powiadomienie o wykonanej transakcji: strona, symbol, ilość, cena,
    wartość i stan konta. Wywoływane zaraz po zapisie Trade (obok maila)."""
    if not push_configured(settings):
        return
    try:
        side = trade.side.upper()
        emoji = "🟢" if side == "BUY" else "🔴"
        verb = "KUPIONO" if side == "BUY" else "SPRZEDANO"
        venue = _venue_label(getattr(trade, "venue", "alpaca"))
        title = f"{emoji} {verb} {trade.symbol}"
        parts = [
            f"{trade.quantity:g} @ {_fmt_usd(trade.price)}",
            f"wartość {_fmt_usd(trade.usdt_value)}",
            f"silnik {venue}",
        ]
        if account_total is not None:
            parts.append(f"konto {_fmt_usd(account_total)}")
        body = " · ".join(parts)
        send_to_all(
            db,
            settings,
            title=title,
            body=body,
            tag=f"trade-{trade.id}",
            url="/",
            data={"venue": getattr(trade, "venue", "alpaca"), "side": side, "symbol": trade.symbol},
        )
    except Exception as exc:  # pragma: no cover - powiadomienie nie może wywalić handlu
        logger.warning("send_trade_push failed: %s", exc)


def _latest_snapshot(db: Session, venue: str) -> PortfolioSnapshot | None:
    return db.execute(
        select(PortfolioSnapshot).where(PortfolioSnapshot.venue == venue).order_by(PortfolioSnapshot.timestamp.desc()).limit(1)
    ).scalar_one_or_none()


def _held_position_count(snapshot: PortfolioSnapshot | None) -> int:
    if snapshot is None:
        return 0
    try:
        balances: dict = json.loads(snapshot.balances_json or "{}")
    except (TypeError, ValueError):
        return 0
    return sum(1 for qty in balances.values() if qty and qty > 0)


def send_daily_summary_push(db: Session, settings: Settings) -> bool:
    """Baner podsumowujący stan konta jako powiadomienie push -- zastępuje
    mailowy raport dzienny. Wywoływane automatycznie raz o report_hour (domyślnie
    8:00) i na żądanie (przycisk 'Wyślij podsumowanie' w Centrum sterowania).
    Best-effort: cicho pomija się, gdy push nie jest skonfigurowany albo nie ma
    jeszcze żadnego snapshotu. Zwraca True, jeśli coś realnie wysłano."""
    if not push_configured(settings):
        return False

    a = _latest_snapshot(db, "alpaca")
    c = _latest_snapshot(db, "extended")
    if a is None and c is None:
        return False

    freshest = max((s for s in (a, c) if s is not None), key=lambda s: s.timestamp)
    cash = freshest.usdt_balance
    equity_value = (a.total_value_usdt - a.usdt_balance) if a else 0.0
    extended_value = (c.total_value_usdt - c.usdt_balance) if c else 0.0
    total = cash + equity_value + extended_value

    state = risk_manager.get_state(db)
    day_pnl_pct = (
        (total - state.day_start_value) / state.day_start_value * 100 if state.day_start_value > 0 else None
    )
    day_txt = f"{'+' if day_pnl_pct >= 0 else ''}{day_pnl_pct:.2f}% dziś" if day_pnl_pct is not None else "brak danych dziś"

    positions_us = _held_position_count(a)
    positions_extended = _held_position_count(c)

    realized = scorecard.total_realized_pnl(db)
    budget = budget_tracker.get_budget_status(db, settings)
    # Lifetime spend, not this month's -- realized P&L is cumulative since
    # inception, so the cost side of "net wynik" must be too (see routes_
    # dashboard._net_result_view for the same fix and rationale).
    net = round(realized - state.claude_spend_usd_lifetime, 2)

    title = f"📊 GielDarek — konto: {_fmt_usd(total)}"
    body = (
        f"{day_txt} · Akcje US: {positions_us} poz. · Poza sesją: {positions_extended} poz. · "
        f"netto (po koszcie Claude): {_fmt_usd(net)} · budżet Claude: {budget['claude_budget_pct_used']:.0f}%"
    )
    sent = send_to_all(db, settings, title=title, body=body, tag="daily-summary", url="/")
    return sent > 0
