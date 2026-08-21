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


def _this_sell_pnl(db: Session, trade) -> dict | None:
    """Zysk/strata TEJ sprzedaży (średni koszt), żeby push mówił wprost 'czy
    zarobiłeś'. Bierzemy najnowszy wpis realized_history dla tego symbolu +
    (najlepiej) z pasującym czasem sprzedaży -- to właśnie ta transakcja."""
    try:
        venue = getattr(trade, "venue", "alpaca")
        hist = scorecard.realized_history(db, venue=venue, limit=60)
        ts = trade.timestamp.isoformat() if getattr(trade, "timestamp", None) is not None else None
        for h in hist:
            if h["symbol"] == trade.symbol and (ts is None or h.get("sold_at") == ts):
                return h
        for h in hist:  # awaryjnie: bez dopasowania czasu, po samym symbolu
            if h["symbol"] == trade.symbol:
                return h
    except Exception:
        logger.warning("sell pnl lookup failed", exc_info=True)
    return None


def _trade_reasoning(trade) -> str:
    """Krótkie uzasadnienie Claude powiązane z tym zleceniem (Decision.reasoning),
    przycięte do jednego zdania na powiadomienie. Best-effort -- brak decyzji /
    lazy-load fail nie może wywalić powiadomienia."""
    try:
        dec = getattr(trade, "decision", None)
        text = (getattr(dec, "reasoning", "") or "").strip() if dec is not None else ""
        if not text:
            return ""
        # Jedno zdanie / max ~120 znaków, żeby baner był zwięzły.
        first = text.split(". ")[0].strip().rstrip(".")
        return (first[:120] + "…") if len(first) > 120 else first
    except Exception:
        return ""


def send_trade_push(db: Session, settings: Settings, trade, account_total: float | None = None) -> None:
    """Powiadomienie o wykonanej transakcji: CO zrobił, ZA ILE, a przy sprzedaży
    CZY ZAROBIŁ czy STRACIŁ (kwota + %), z wizualnym kodowaniem (✅/🔻/🟢) i
    dopasowaną wibracją. Wywoływane zaraz po zapisie Trade (obok maila)."""
    if not push_configured(settings):
        return
    try:
        # Tryb powiadomień: all / big (tylko duże ruchy) / daily / off.
        mode = getattr(risk_manager.get_state(db), "push_mode", "all") or "all"
        if mode in ("off", "daily"):
            return
        if mode == "big":
            big = max(15.0, 0.03 * account_total) if account_total else 15.0
            if abs(getattr(trade, "usdt_value", 0.0) or 0.0) < big:
                return
        side = trade.side.upper()
        venue = _venue_label(getattr(trade, "venue", "alpaca"))
        acct = f" · konto {_fmt_usd(account_total)}" if account_total is not None else ""

        if side == "BUY":
            title = f"🟢 KUPIŁEM {trade.symbol} — za {_fmt_usd(trade.usdt_value)}"
            body = f"{trade.quantity:g} @ {_fmt_usd(trade.price)} · silnik {venue}{acct}"
            # Dołącz KRÓTKIE uzasadnienie Claude (czemu kupił), jeśli jest przy
            # decyzji powiązanej z tym zleceniem -- więcej kontekstu w kieszeni.
            why = _trade_reasoning(trade)
            if why:
                body = f"{body}\n„{why}"
            kind, vibrate = "buy", [20, 40, 20]
        else:
            pnl = _this_sell_pnl(db, trade)
            if pnl is not None:
                win = (pnl["pnl_usd"] or 0) >= 0
                sign = "+" if win else "−"
                amt = _fmt_usd(abs(pnl["pnl_usd"]))
                pct = pnl.get("pnl_pct")
                pcttxt = f" ({sign}{abs(pct):.1f}%)" if pct is not None else ""
                days = pnl.get("days_held")
                daystxt = f" · trzymane {days} {'dzień' if days == 1 else 'dni'}" if days is not None else ""
                head = "✅ ZYSK" if win else "🔻 STRATA"
                title = f"{head} {sign}{amt} — sprzedałem {trade.symbol}"
                body = f"za {_fmt_usd(trade.usdt_value)}{pcttxt}{daystxt} · silnik {venue}{acct}"
                kind = "win" if win else "loss"
                vibrate = [30, 50, 30, 50, 30] if win else [220]
            else:
                title = f"🔴 SPRZEDAŁEM {trade.symbol} — za {_fmt_usd(trade.usdt_value)}"
                body = f"{trade.quantity:g} @ {_fmt_usd(trade.price)} · silnik {venue}{acct}"
                kind, vibrate = "sell", [60]

        send_to_all(
            db,
            settings,
            title=title,
            body=body,
            tag=f"trade-{trade.id}",
            url="/",
            data={"venue": getattr(trade, "venue", "alpaca"), "side": side, "symbol": trade.symbol,
                  "kind": kind, "vibrate": vibrate},
        )
    except Exception as exc:  # pragma: no cover - powiadomienie nie może wywalić handlu
        logger.warning("send_trade_push failed: %s", exc)


def send_alarm(db: Session, settings: Settings, *, title: str, body: str, tag: str = "alarm") -> int:
    """Wysoki-priorytet alarm (np. blackout newsów, wstrzymanie handlu). Cienka
    nakładka na send_to_all, best-effort -- nigdy nie wywraca ścieżki handlu."""
    try:
        return send_to_all(db, settings, title=title, body=body, tag=tag, url="/")
    except Exception as exc:  # pragma: no cover - alarm nie może wywalić handlu
        logger.warning("send_alarm failed: %s", exc)
        return 0


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


def _combined_account_total(db: Session) -> float | None:
    """Łączna wartość konta (gotówka liczona RAZ + pozycje obu nóg) z najświeższych
    snapshotów — ta sama metoda co daily summary. None, gdy brak snapshotów."""
    a = _latest_snapshot(db, "alpaca")
    c = _latest_snapshot(db, "extended")
    if a is None and c is None:
        return None
    freshest = max((s for s in (a, c) if s is not None), key=lambda s: s.timestamp)
    cash = freshest.usdt_balance
    equity_value = (a.total_value_usdt - a.usdt_balance) if a else 0.0
    extended_value = (c.total_value_usdt - c.usdt_balance) if c else 0.0
    return cash + equity_value + extended_value


def check_day_pnl_alert(db: Session, settings: Settings) -> bool:
    """Alert progu dziennego P&L: gdy dzienny wynik konta przekroczy próg (w obie
    strony), leci JEDEN push na dzień na kierunek (dedup po dniu handlowym +
    kierunku w SystemState). Best-effort — wołane z pętli schedulera."""
    if not settings.day_pnl_alert_enabled or not push_configured(settings):
        return False
    total = _combined_account_total(db)
    if total is None:
        return False
    state = risk_manager.get_state(db)
    if state.day_start_value <= 0:
        return False
    pct = (total - state.day_start_value) / state.day_start_value * 100
    if abs(pct) < settings.day_pnl_alert_pct:
        return False
    direction = "up" if pct >= 0 else "down"
    # Klucz dnia = ten sam dzień handlowy, którego używa risk_manager (day_start_date),
    # więc alert auto-resetuje się przy przewinięciu doby, bez własnej logiki daty.
    stamp = f"{state.day_start_date or ''}:{direction}"
    if getattr(state, "day_pnl_alert_stamp", "") == stamp:
        return False
    usd = total - state.day_start_value
    if direction == "up":
        title = f"📈 Mocny dzień: +{pct:.1f}% ({_fmt_usd(usd)})"
        body = f"Konto {_fmt_usd(total)} — bot na plusie dziś."
    else:
        title = f"📉 Duży zjazd dnia: {pct:.1f}% ({_fmt_usd(usd)})"
        body = f"Konto {_fmt_usd(total)} — dziś na minusie. Zerknij, czy wszystko gra."
    sent = send_alarm(db, settings, title=title, body=body, tag="day-pnl")
    if sent > 0:
        state.day_pnl_alert_stamp = stamp
        db.commit()
    return sent > 0


def send_weekly_summary_push(db: Session, settings: Settings) -> bool:
    """Zwięzłe podsumowanie TYGODNIA jako push: zysk zrealizowany z ostatnich 7
    dni, liczba zamknięć, skuteczność, stan konta. Osobny rytm od dziennego."""
    if not push_configured(settings):
        return False
    import datetime as _dt

    closes = scorecard.realized_history(db, venue="alpaca", limit=500)
    now = _dt.datetime.now(_dt.UTC)
    week_pnl = 0.0
    wins = closed = 0
    for c in closes:
        sold = c.get("sold_at")
        if not sold:
            continue
        try:
            when = _dt.datetime.fromisoformat(sold)
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=_dt.UTC)
        if (now - when).days > 7 or now < when:
            continue
        pnl = c.get("pnl_usd") or 0.0
        week_pnl += pnl
        closed += 1
        if pnl >= 0:
            wins += 1
    total = _combined_account_total(db)
    win_txt = f" · skuteczność {round(wins / closed * 100)}%" if closed else ""
    sign = "+" if week_pnl >= 0 else ""
    title = f"🗓️ Tydzień: {sign}{_fmt_usd(week_pnl)}"
    acct = f" · konto {_fmt_usd(total)}" if total is not None else ""
    body = f"{closed} {'transakcja' if closed == 1 else 'transakcji'}{win_txt}{acct}"
    sent = send_to_all(db, settings, title=title, body=body, tag="weekly-summary", url="/")
    return sent > 0
