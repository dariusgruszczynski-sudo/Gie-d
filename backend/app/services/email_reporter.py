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

GOLD = "#d4af37"
GOLD_BRIGHT = "#f2cf5b"
BG = "#0a0a0a"
PANEL = "#161410"
BORDER = "#4a3c15"
TEXT = "#f3e6c4"
MUTED = "#b3a06a"
GREEN = "#4caf60"
RED = "#e5484d"


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
    ax.set_title("Wartość portfela (USDT)", color=TEXT, fontsize=11, pad=10)
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


def _build_html(
    *,
    settings: Settings,
    current: PortfolioSnapshot | None,
    day_pnl_pct: float | None,
    week_pnl_pct: float | None,
    state,
    budget: dict,
    latest_decision: Decision | None,
    recent_decisions: list[Decision],
    recent_trades: list[Trade],
) -> str:
    mode_label = "TESTNET (wirtualne środki)" if settings.binance_testnet else "PRODUKCJA (realny kapitał)"
    status_line = "zatrzymany (limit strat)" if state.is_halted else "zapauzowany" if state.is_paused else "aktywny"

    decisions_rows = "".join(
        f"""
        <tr>
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};color:{MUTED};font-size:12px;white-space:nowrap;">{d.timestamp.strftime('%d.%m %H:%M')}</td>
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
          <td style="padding:6px 10px;border-bottom:1px solid {BORDER};color:{MUTED};font-size:12px;white-space:nowrap;">{t.timestamp.strftime('%d.%m %H:%M')}</td>
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
        else "Brak jeszcze analizy Opusa — automat czeka na pierwszy cykl."
    )
    outlook_meta = (
        f"({latest_decision.timestamp.strftime('%d.%m %H:%M')}, pewność {latest_decision.confidence * 100:.0f}%)"
        if latest_decision
        else ""
    )

    current_value = f"${current.total_value_usdt:,.2f}" if current else "—"

    return f"""\
<div style="background:{BG};padding:24px 16px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:{TEXT};">
  <div style="max-width:640px;margin:0 auto;">
    <div style="text-align:center;padding:16px;border-bottom:2px solid {GOLD};margin-bottom:20px;">
      <div style="font-size:20px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{GOLD_BRIGHT};">
        KTO GRA GRUBO, WYGRAĆ MUSI
      </div>
      <div style="color:{MUTED};font-size:12px;margin-top:6px;">GielDarek — dzienny raport, {date.today().strftime('%d.%m.%Y')}</div>
    </div>

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <table style="width:100%;border-collapse:collapse;">
        <tr>
          <td style="color:{MUTED};font-size:11px;">TRYB</td>
          <td style="color:{MUTED};font-size:11px;">STATUS AUTOMATU</td>
          <td style="color:{MUTED};font-size:11px;">WARTOŚĆ PORTFELA</td>
        </tr>
        <tr>
          <td style="font-weight:700;padding-top:2px;">{mode_label}</td>
          <td style="font-weight:700;padding-top:2px;">{status_line}</td>
          <td style="font-weight:700;padding-top:2px;">{current_value}</td>
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

    <div style="background:{PANEL};border:1px solid {BORDER};border-radius:10px;padding:16px;margin-bottom:16px;">
      <div style="color:{GOLD};font-size:13px;font-weight:700;margin-bottom:8px;">Perspektywa rynkowa Opusa {outlook_meta}</div>
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


def build_report(db: Session, settings: Settings) -> tuple[str, bytes]:
    current = db.execute(
        select(PortfolioSnapshot).order_by(PortfolioSnapshot.timestamp.desc()).limit(1)
    ).scalar_one_or_none()
    since = datetime.utcnow() - timedelta(days=7)
    history = list(
        db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.timestamp >= since)
            .order_by(PortfolioSnapshot.timestamp.asc())
        ).scalars()
    )

    state = risk_manager.get_state(db)
    day_pnl_pct = (
        (current.total_value_usdt - state.day_start_value) / state.day_start_value * 100
        if current and state.day_start_value > 0
        else None
    )
    week_pnl_pct = (
        (current.total_value_usdt - state.week_start_value) / state.week_start_value * 100
        if current and state.week_start_value > 0
        else None
    )
    budget = budget_tracker.get_budget_status(db, settings)

    recent_decisions = list(
        db.execute(select(Decision).order_by(Decision.timestamp.desc()).limit(10)).scalars()
    )
    latest_decision = recent_decisions[0] if recent_decisions else None
    recent_trades = list(db.execute(select(Trade).order_by(Trade.timestamp.desc()).limit(10)).scalars())

    chart_png = _render_chart_png(history)
    html = _build_html(
        settings=settings,
        current=current,
        day_pnl_pct=day_pnl_pct,
        week_pnl_pct=week_pnl_pct,
        state=state,
        budget=budget,
        latest_decision=latest_decision,
        recent_decisions=recent_decisions,
        recent_trades=recent_trades,
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
