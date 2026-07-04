import { StatusResponse } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";
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

function TileIcon({ name }: { name: "shield" | "lock" | "coins" }) {
  const common = { width: 15, height: 15, viewBox: "0 0 24 24", fill: "none" as const, "aria-hidden": true as const };
  switch (name) {
    case "shield":
      return (
        <svg {...common}>
          <path d="M12 2 L20 5 V11 C20 16 16.5 20 12 22 C7.5 20 4 16 4 11 V5 Z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
        </svg>
      );
    case "lock":
      return (
        <svg {...common}>
          <rect x="5" y="10" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M8 10 V7 a4 4 0 0 1 8 0 v3" stroke="currentColor" strokeWidth="1.6" />
        </svg>
      );
    case "coins":
      return (
        <svg {...common}>
          <ellipse cx="9" cy="7" rx="6" ry="3" stroke="currentColor" strokeWidth="1.6" />
          <path d="M3 7 v4 c0 1.7 2.7 3 6 3 s6 -1.3 6 -3 V7" stroke="currentColor" strokeWidth="1.6" />
          <path d="M3 15 c0 1.7 2.7 3 6 3 s6 -1.3 6 -3" stroke="currentColor" strokeWidth="1.6" />
          <ellipse cx="17" cy="13" rx="4" ry="2.2" stroke="currentColor" strokeWidth="1.4" />
          <path d="M13 13 v3.5 c0 1.2 1.8 2.2 4 2.2 s4 -1 4 -2.2 V13" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      );
  }
}

function LiveDot() {
  return (
    <span className="live-dot">
      NA ŻYWO
    </span>
  );
}

export function StatusBanner({ status }: { status: StatusResponse }) {
  const bannerClass = status.is_halted
    ? "banner halted"
    : status.is_paused || status.claude_budget_alert
      ? "banner paused"
      : "banner";

  const spentAnimated = useCountUp(status.claude_spend_usd_this_month);

  return (
    <div className={bannerClass}>
      <div className="stat-tiles">
        <div className="stat-tile">
          <div className="stat-tile-top">
            <TileIcon name="shield" />
            <span className={`pill ${status.mode}`}>{status.mode === "testnet" ? "TESTNET" : "PRODUKCJA"}</span>
          </div>
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
          <div className="stat-tile-top">
            <TileIcon name="lock" />
            <span className="stat-tile-label">Limit dzienny / tygodniowy</span>
          </div>
          <strong>
            -{status.daily_loss_limit_pct}% / -{status.weekly_loss_limit_pct}%
          </strong>
        </div>

        <div className="stat-tile">
          <div className="stat-tile-top">
            <TileIcon name="coins" />
            <span className="stat-tile-label">Whitelist</span>
          </div>
          <strong className="stat-tile-whitelist">{status.whitelist.join(" · ")}</strong>
        </div>

        <div className="stat-tile stat-tile-budget">
          <BudgetGauge pctUsed={status.claude_budget_pct_used} alert={status.claude_budget_alert} />
          <div>
            <span className="stat-tile-label">Budżet Claude (miesiąc)</span>
            <strong className={status.claude_budget_alert ? "pnl-negative" : ""}>
              ${spentAnimated.toFixed(2)} / ${status.claude_monthly_budget_usd.toFixed(2)}
            </strong>
          </div>
        </div>

        <div className="stat-tile stat-tile-live">
          <LiveDot />
          <span className="stat-tile-label">automat monitoruje rynek</span>
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
