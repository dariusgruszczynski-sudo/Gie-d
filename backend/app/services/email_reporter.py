"""Builds and sends the daily HTML email report: portfolio chart, current
status, budget, latest Opus market view, and recent decisions/trades."""

import io
import logging
import smtplib
from datetime import date, datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Decision, PortfolioSnapshot, Trade
from app.services import budget_tracker, risk_manager

logger = logging.getLogger(__name__)

# Palette matched to the dashboard's "fintech terminal" theme (indigo accent).
# Names GOLD/GOLD_BRIGHT kept and repointed at the accent so the rest of the
# template re-themes without edits.
GOLD = "#6d7cff"
GOLD_BRIGHT = "#9d7bff"
BG = "#0a0c14"
PANEL = "#111524"
BORDER = "#212842"
TEXT = "#e8ebf5"
MUTED = "#8b93ac"
GREEN = "#26d07c"
RED = "#ff5468"


def _render_chart_png(history: list[PortfolioSnapshot]) -> bytes:
    fig, ax = plt.subplots(figsize=(7, 3), dpi=140)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    if history:
        xs = [h.timestamp for h in history]
        ys = [h.total_value_usdt for h in history]
        ax.plot(xs, ys, color=GOLD_BRIGHT, linewidth=2)
        ax.fill_between(xs, ys, min(ys) * 0.999 if ys else 0, color=GOLD, alpha=0.12)
    else:
        ax.text(0.5, 0.5, "Brak jeszcze danych", ha="center", va="center", color=MUTED, transform=ax.transAxes)

    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.set_title("Wartość portfela (USD)", color=TEXT, fontsize=11, pad=10)
    if history:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m %H:%M"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=6))
    fig.autofmt_xdate()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
    plt.close(fig)
    return buf.getvalue()


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"


def _pct_color(value: float | None) -> str:
    if value is None:
        return MUTED
    return GREEN if value >= 0 else RED


def _scorecard_html(card: dict | None) -> str:
    if not card:
        return ""
    alpha_pct = card.get("alpha_pct")
    alpha_usd = card.get("alpha_usd")
    win_rate = card.get("win_rate_pct")
    verdict = (
        f'<span style="color:{GREEN};font-weight:700;">bijesz rynek</span>'
        if (alpha_pct or 0) >= 0
        else f'<span style="color:{RED};font-weight:700;">poniżej rynku</span>'
    ) if alpha_pct is not None else '<span style="color:' + MUTED + ';">baseline w trakcie kalibracji</span>'
    alpha_txt = (
        f"{'+' if alpha_usd >= 0 else '−'}${abs(alpha_usd):.2f} ({'+' if alpha_pct >= 0 else ''}{alpha_pct:.2f}%)"
        if alpha_pct is not None and alpha_usd is not None
        else "—"
    )
    return f"""
    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <div style="color:{GOLD};font-size:13px;font-weight:700;margin-bottom:8px;">Wynik vs trzymanie {card.get('benchmark_symbol', 'SPY')} — {verdict}</div>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="color:{MUTED};font-size:11px;">TWÓJ PORTFEL</td>
          <td style="color:{MUTED};font-size:11px;">GDYBYŚ TRZYMAŁ {card.get('benchmark_symbol', 'SPY')}</td>
          <td style="color:{MUTED};font-size:11px;">PRZEWAGA (ALPHA)</td>
          <td style="color:{MUTED};font-size:11px;">TRAFNOŚĆ</td>
        </tr>
        <tr>
          <td style="font-weight:700;padding-top:2px;">${card.get('portfolio_value', 0):.2f}</td>
          <td style="font-weight:700;padding-top:2px;">{('$' + format(card['benchmark_value'], '.2f')) if card.get('benchmark_value') is not None else '—'}</td>
          <td style="font-weight:700;padding-top:2px;color:{_pct_color(alpha_pct)};">{alpha_txt}</td>
          <td style="font-weight:700;padding-top:2px;">{(format(win_rate, '.0f') + '% (' + str(card.get('wins', 0)) + 'W/' + str(card.get('losses', 0)) + 'L)') if win_rate is not None else '—'}</td>
        </tr>
      </table>
    </div>"""


def _venue_tag(venue: str) -> str:
    is_crypto = venue == "crypto"
    color = "#f5b544" if is_crypto else GOLD
    label = "Krypto" if is_crypto else "Alpaca"
    return (
        f'<span style="font-size:10px;font-weight:700;color:{color};border:1px solid {color};'
        f'border-radius:4px;padding:1px 5px;">{label}</span>'
    )


def _build_html(
    *,
    alpaca_current: PortfolioSnapshot | None,
    crypto_current: PortfolioSnapshot | None,
    crypto_enabled: bool,
    day_pnl_pct: float | None,
    week_pnl_pct: float | None,
    state,
    budget: dict,
    latest_decision: Decision | None,
    recent_decisions: list[Decision],
    recent_trades: list[Trade],
    scorecard_card: dict | None = None,
) -> str:
    mode_label = "PRODUKCJA (realny kapitał)"
    alpaca_status = "zatrzymany (limit strat)" if state.is_halted else "zapauzowany" if state.is_paused else "aktywny"
    crypto_status = "wyłączony" if not crypto_enabled else ("zatrzymany" if state.crypto_paused else "aktywny")

    alpaca_val = alpaca_current.total_value_usdt if alpaca_current else 0.0
    crypto_val = crypto_current.total_value_usdt if (crypto_enabled and crypto_current) else 0.0
    total_val = alpaca_val + crypto_val

    decisions_rows = "".join(
        f"""
        <tr>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};color:{MUTED};font-size:12px;white-space:nowrap;">{d.timestamp.strftime('%d.%m %H:%M')} {_venue_tag(d.venue)}</td>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};font-size:12px;">
            <span style="color:{GREEN if d.action.value=='BUY' else RED if d.action.value=='SELL' else MUTED};font-weight:600;">{d.action.value}</span>
            {(' ' + d.symbol) if d.symbol else ''}
          </td>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};font-size:12px;color:{MUTED};">
            {'odrzucone: ' + d.rejection_reason if d.rejection_reason else ('wykonane' if d.executed else 'brak akcji')}
          </td>
        </tr>"""
        for d in recent_decisions
    )

    trades_rows = "".join(
        f"""
        <tr>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};color:{MUTED};font-size:12px;white-space:nowrap;">{t.timestamp.strftime('%d.%m %H:%M')} {_venue_tag(t.venue)}</td>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};font-size:12px;">
            <span style="color:{GREEN if t.side=='BUY' else RED};font-weight:600;">{t.side}</span> {t.symbol}
          </td>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};font-size:12px;">${t.usdt_value:.2f}</td>
        </tr>"""
        for t in recent_trades
    ) or f'<tr><td style="padding:6px 10px;color:{MUTED};font-size:12px;">Brak transakcji w tym okresie.</td></tr>'

    outlook = (
        latest_decision.reasoning
        if latest_decision
        else "Brak jeszcze analizy Claude — automat czeka na pierwszy cykl."
    )
    outlook_meta = (
        f"({latest_decision.timestamp.strftime('%d.%m %H:%M')}, {_venue_tag(latest_decision.venue)}, pewność {latest_decision.confidence * 100:.0f}%)"
        if latest_decision
        else ""
    )

    crypto_cell = (
        f'${crypto_val:,.2f} <span style="color:{MUTED};font-size:11px;">({crypto_status})</span>'
        if crypto_enabled
        else f'<span style="color:{MUTED};">wyłączony</span>'
    )

    return f"""\
<div style="background:{BG};padding:24px 16px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:{TEXT};">
  <div style="max-width:640px;margin:0 auto;">
    <div style="display:flex;align-items:center;gap:12px;padding:4px 4px 18px;border-bottom:1px solid {BORDER};margin-bottom:22px;">
      <div style="width:40px;height:40px;border-radius:11px;background:linear-gradient(135deg,{GOLD},{GOLD_BRIGHT});display:inline-block;text-align:center;line-height:40px;font-size:20px;">📈</div>
      <div style="text-align:left;">
        <div style="font-size:20px;font-weight:800;letter-spacing:-0.5px;color:{TEXT};">Giel<span style="color:{GOLD};">Darek</span></div>
        <div style="color:{MUTED};font-size:12px;margin-top:2px;">Dzienny raport · {date.today().strftime('%d.%m.%Y')} · {mode_label}</div>
      </div>
    </div>

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <div style="color:{GOLD};font-size:13px;font-weight:700;margin-bottom:10px;">Portfele — widok zbiorczy</div>
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="color:{MUTED};font-size:11px;">PORTFEL DZIENNY (AKCJE US)</td>
          <td style="color:{MUTED};font-size:11px;">PORTFEL KRYPTO (24/7)</td>
          <td style="color:{MUTED};font-size:11px;">RAZEM</td>
        </tr>
        <tr>
          <td style="font-weight:700;padding-top:2px;">${alpaca_val:,.2f} <span style="color:{MUTED};font-size:11px;">({alpaca_status})</span></td>
          <td style="font-weight:700;padding-top:2px;">{crypto_cell}</td>
          <td style="font-weight:800;padding-top:2px;color:{GOLD_BRIGHT};">${total_val:,.2f}</td>
        </tr>
      </table>
    </div>

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="color:{MUTED};font-size:11px;">DZIENNY P&amp;L</td>
          <td style="color:{MUTED};font-size:11px;">TYGODNIOWY P&amp;L</td>
          <td style="color:{MUTED};font-size:11px;">BUDŻET CLAUDE (MIESIĄC)</td>
        </tr>
        <tr>
          <td style="font-weight:700;color:{_pct_color(day_pnl_pct)};padding-top:2px;">{_fmt_pct(day_pnl_pct)}</td>
          <td style="font-weight:700;color:{_pct_color(week_pnl_pct)};padding-top:2px;">{_fmt_pct(week_pnl_pct)}</td>
          <td style="font-weight:700;padding-top:2px;{'color:' + RED + ';' if budget['claude_budget_alert'] else ''}">
            ${budget['claude_spend_usd_this_month']:.2f} / ${budget['claude_monthly_budget_usd']:.2f} ({budget['claude_budget_pct_used']:.0f}%)
          </td>
        </tr>
      </table>
    </div>

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:12px;margin-bottom:16px;text-align:center;">
      <img src="cid:portfolio_chart" alt="Wykres wartości portfela" style="max-width:100%;border-radius:6px;" />
    </div>
{_scorecard_html(scorecard_card)}

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <div style="color:{GOLD};font-size:13px;font-weight:700;margin-bottom:8px;">Perspektywa rynkowa Claude {outlook_meta}</div>
      <div style="font-size:13px;line-height:1.5;color:{TEXT};">{outlook}</div>
    </div>

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <div style="color:{GOLD};font-size:13px;font-weight:700;margin-bottom:8px;">Ostatnie decyzje</div>
      <table style="width:100%;border-collapse:collapse;">{decisions_rows or f'<tr><td style="padding:6px 10px;color:{MUTED};font-size:12px;">Brak decyzji.</td></tr>'}</table>
    </div>

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;">
      <div style="color:{GOLD};font-size:13px;font-weight:700;margin-bottom:8px;">Ostatnie transakcje</div>
      <table style="width:100%;border-collapse:collapse;">{trades_rows}</table>
    </div>

    <div style="text-align:center;color:{MUTED};font-size:11px;margin-top:20px;">
      To narzędzie prywatne — nie jest to porada inwestycyjna. Wygenerowano automatycznie o {datetime.now().strftime('%H:%M')}.
    </div>
  </div>
</div>
"""


def _latest_snapshot(db: Session, venue: str) -> PortfolioSnapshot | None:
    return db.execute(
        select(PortfolioSnapshot)
        .where(PortfolioSnapshot.venue == venue)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()


def build_report(db: Session, settings: Settings) -> tuple[str, bytes]:
    alpaca_current = _latest_snapshot(db, "alpaca")
    crypto_current = _latest_snapshot(db, "crypto")
    since = datetime.utcnow() - timedelta(days=7)
    # Chart tracks the Alpaca (day) portfolio -- the account-wide day/week
    # loss baselines are Alpaca-driven.
    history = list(
        db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.timestamp >= since, PortfolioSnapshot.venue == "alpaca")
            .order_by(PortfolioSnapshot.timestamp.asc())
        ).scalars()
    )

    state = risk_manager.get_state(db)
    day_pnl_pct = (
        (alpaca_current.total_value_usdt - state.day_start_value) / state.day_start_value * 100
        if alpaca_current and state.day_start_value > 0
        else None
    )
    week_pnl_pct = (
        (alpaca_current.total_value_usdt - state.week_start_value) / state.week_start_value * 100
        if alpaca_current and state.week_start_value > 0
        else None
    )
    budget = budget_tracker.get_budget_status(db, settings)

    # Recent activity across BOTH portfolios so the report is a single
    # collective view (each row is tagged with its venue).
    recent_decisions = list(
        db.execute(select(Decision).order_by(Decision.timestamp.desc()).limit(12)).scalars()
    )
    latest_decision = recent_decisions[0] if recent_decisions else None
    recent_trades = list(db.execute(select(Trade).order_by(Trade.timestamp.desc()).limit(12)).scalars())

    # Scorecard vs buy-and-hold (Alpaca only -- SPY benchmark).
    card = None
    if alpaca_current is not None:
        import json as _json

        from app.services import scorecard as scorecard_svc

        card = scorecard_svc.compute_scorecard(
            db,
            settings,
            {"total_value_usdt": alpaca_current.total_value_usdt, "prices": _json.loads(alpaca_current.prices_json or "{}")},
        )

    chart_png = _render_chart_png(history)
    html = _build_html(
        alpaca_current=alpaca_current,
        crypto_current=crypto_current,
        crypto_enabled=settings.crypto_enabled,
        day_pnl_pct=day_pnl_pct,
        week_pnl_pct=week_pnl_pct,
        state=state,
        budget=budget,
        latest_decision=latest_decision,
        recent_decisions=recent_decisions,
        recent_trades=recent_trades,
        scorecard_card=card,
    )
    return html, chart_png


def send_daily_report(db: Session, settings: Settings) -> None:
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning("SMTP not configured (SMTP_USERNAME/SMTP_PASSWORD empty) -- skipping report email")
        return

    html, chart_png = build_report(db, settings)

    msg = MIMEMultipart("related")
    msg["Subject"] = f"GielDarek — raport dzienny {date.today().strftime('%d.%m.%Y')}"
    msg["From"] = settings.smtp_from_email or settings.smtp_username
    msg["To"] = settings.report_recipient_email
    msg.attach(MIMEText(html, "html", "utf-8"))

    image = MIMEImage(chart_png)
    image.add_header("Content-ID", "<portfolio_chart>")
    image.add_header("Content-Disposition", "inline", filename="portfolio.png")
    msg.attach(image)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)

    logger.info("Daily report email sent to %s", settings.report_recipient_email)


def send_trade_alert(settings: Settings, trade, reason: str = "") -> None:
    """Best-effort instant email the moment a trade executes (BUY/SELL, incl.
    TP/SL/trailing exits). Never raises -- a mail hiccup must not break trading.
    Silently skipped if alerts are off or SMTP isn't configured."""
    if not settings.trade_alerts_enabled:
        return
    if not settings.smtp_username or not settings.smtp_password:
        return

    try:
        side_pl = "KUPIŁEŚ" if trade.side.upper() == "BUY" else "SPRZEDAŁEŚ"
        color = GREEN if trade.side.upper() == "BUY" else RED
        cur = settings.quote_currency
        subject = f"GielDarek: {side_pl} {trade.symbol} za {trade.usdt_value:.2f} {cur}"
        html = f"""\
<div style="background:{BG};padding:20px 16px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:{TEXT};">
  <div style="max-width:520px;margin:0 auto;">
    <div style="font-size:22px;font-weight:800;color:{color};margin-bottom:12px;">{side_pl} {trade.symbol}</div>
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <tr><td style="color:{MUTED};padding:4px 0;">Ilość</td><td style="text-align:right;font-weight:700;">{trade.quantity:.8f}</td></tr>
      <tr><td style="color:{MUTED};padding:4px 0;">Cena</td><td style="text-align:right;font-weight:700;">{trade.price:.2f} {cur}</td></tr>
      <tr><td style="color:{MUTED};padding:4px 0;">Wartość</td><td style="text-align:right;font-weight:700;">{trade.usdt_value:.2f} {cur}</td></tr>
      <tr><td style="color:{MUTED};padding:4px 0;">Tryb</td><td style="text-align:right;">{trade.mode.value if hasattr(trade.mode, 'value') else trade.mode}{' · ręczna' if trade.is_manual else ' · automat'}</td></tr>
    </table>
    {f'<div style="margin-top:12px;padding:10px;background:{PANEL};border:1px solid {BORDER};border-radius:8px;font-size:13px;line-height:1.5;">{reason}</div>' if reason else ''}
    <div style="color:{MUTED};font-size:11px;margin-top:16px;">GielDarek — powiadomienie automatyczne, {datetime.now().strftime('%d.%m.%Y %H:%M')}. To narzędzie prywatne, nie porada inwestycyjna.</div>
  </div>
</div>"""

        msg = MIMEText(html, "html", "utf-8")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from_email or settings.smtp_username
        msg["To"] = settings.report_recipient_email

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        logger.info("Trade alert email sent: %s %s", trade.side, trade.symbol)
    except Exception:
        logger.warning("Failed to send trade alert email (continuing)", exc_info=True)
