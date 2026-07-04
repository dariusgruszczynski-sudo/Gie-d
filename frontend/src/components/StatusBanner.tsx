import { StatusResponse } from "../api/client";
import { BudgetGauge } from "./BudgetGauge";

function pnlClass(value: number | null): string {
  if (value === null) return "";
  return value >= 0 ? "pnl-positive" : "pnl-negative";
}

function fmtPct(value: number | null): string {
  if (value === null) return "—";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

function TrendArrow({ value }: { value: number | null }) {
  if (value === null) return null;
  const up = value >= 0;
  return (
    <svg width="11" height="11" viewBox="0 0 10 10" style={{ marginRight: 4 }} aria-hidden="true">
      {up ? <path d="M5 1 L9 8 L1 8 Z" fill="currentColor" /> : <path d="M5 9 L1 2 L9 2 Z" fill="currentColor" />}
    </svg>
  );
}

export function StatusBanner({ status }: { status: StatusResponse }) {
  const bannerClass = status.is_halted
    ? "banner halted"
    : status.is_paused || status.claude_budget_alert
      ? "banner paused"
      : "banner";

  return (
    <div className={bannerClass}>
      <div className="stat-tiles">
        <div className="stat-tile">
          <span className={`pill ${status.mode}`}>
            {status.mode === "testnet" ? "TESTNET" : "PRODUKCJA"}
          </span>
          <span className="stat-tile-label">
            {status.mode === "testnet" ? "wirtualne środki" : "realny kapitał"}
          </span>
        </div>

        <div className="stat-tile">
          <span className="stat-tile-label">Dzienny P&L</span>
          <strong className={pnlClass(status.day_pnl_pct)}>
            <TrendArrow value={status.day_pnl_pct} />
            {fmtPct(status.day_pnl_pct)}
          </strong>
        </div>

        <div className="stat-tile">
          <span className="stat-tile-label">Tygodniowy P&L</span>
          <strong className={pnlClass(status.week_pnl_pct)}>
            <TrendArrow value={status.week_pnl_pct} />
            {fmtPct(status.week_pnl_pct)}
          </strong>
        </div>

        <div className="stat-tile">
          <span className="stat-tile-label">Limit dzienny / tygodniowy</span>
          <strong>
            -{status.daily_loss_limit_pct}% / -{status.weekly_loss_limit_pct}%
          </strong>
        </div>

        <div className="stat-tile">
          <span className="stat-tile-label">Whitelist</span>
          <strong className="stat-tile-whitelist">{status.whitelist.join(" · ")}</strong>
        </div>

        <div className="stat-tile stat-tile-budget">
          <BudgetGauge pctUsed={status.claude_budget_pct_used} alert={status.claude_budget_alert} />
          <div>
            <span className="stat-tile-label">Budżet Claude (miesiąc)</span>
            <strong className={status.claude_budget_alert ? "pnl-negative" : ""}>
              ${status.claude_spend_usd_this_month.toFixed(2)} / ${status.claude_monthly_budget_usd.toFixed(2)}
            </strong>
          </div>
        </div>
      </div>

      {status.claude_budget_alert && (
        <div className="banner-callout amber">
          💰 Wykorzystano ponad {status.claude_budget_pct_used.toFixed(0)}% miesięcznego budżetu Claude (szacunek na
          podstawie zużytych tokenów, nie realne saldo) — rozważ doładowanie konta na{" "}
          <strong>console.anthropic.com</strong>.
        </div>
      )}

      {status.is_halted && (
        <div className="banner-callout red">⛔ AUTOMAT ZATRZYMANY: {status.halted_reason}</div>
      )}
      {status.is_paused && !status.is_halted && (
        <div className="banner-callout amber">⏸ Automat zapauzowany ręcznie</div>
      )}
    </div>
  );
}
