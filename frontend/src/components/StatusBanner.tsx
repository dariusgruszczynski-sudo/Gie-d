import { StatusResponse } from "../api/client";

function pnlClass(value: number | null): string {
  if (value === null) return "";
  return value >= 0 ? "pnl-positive" : "pnl-negative";
}

function fmtPct(value: number | null): string {
  if (value === null) return "—";
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function StatusBanner({ status }: { status: StatusResponse }) {
  const bannerClass = status.is_halted
    ? "banner halted"
    : status.is_paused || status.claude_budget_alert
      ? "banner paused"
      : "banner";

  return (
    <div className={bannerClass}>
      <span className={`pill ${status.mode}`}>
        {status.mode === "testnet" ? "TESTNET (wirtualne środki)" : "PRODUKCJA (realny kapitał)"}
      </span>

      <div className="stat">
        Dzienny P&L
        <strong className={pnlClass(status.day_pnl_pct)}>{fmtPct(status.day_pnl_pct)}</strong>
      </div>
      <div className="stat">
        Tygodniowy P&L
        <strong className={pnlClass(status.week_pnl_pct)}>{fmtPct(status.week_pnl_pct)}</strong>
      </div>
      <div className="stat">
        Limit dzienny / tygodniowy
        <strong>
          -{status.daily_loss_limit_pct}% / -{status.weekly_loss_limit_pct}%
        </strong>
      </div>
      <div className="stat">
        Whitelist
        <strong>{status.whitelist.join(", ")}</strong>
      </div>
      <div className="stat">
        Budżet Claude (miesiąc)
        <strong className={status.claude_budget_alert ? "pnl-negative" : ""}>
          ${status.claude_spend_usd_this_month.toFixed(2)} / ${status.claude_monthly_budget_usd.toFixed(2)} (
          {status.claude_budget_pct_used.toFixed(0)}%)
        </strong>
      </div>

      {status.claude_budget_alert && (
        <div className="stat" style={{ color: "var(--amber)" }}>
          💰 Wykorzystano ponad {status.claude_budget_pct_used.toFixed(0)}% miesięcznego budżetu Claude (szacunek na
          podstawie zużytych tokenów, nie realne saldo) — rozważ doładowanie konta na{" "}
          <strong>console.anthropic.com</strong>.
        </div>
      )}

      {status.is_halted && (
        <div className="stat" style={{ color: "var(--red)" }}>
          ⛔ AUTOMAT ZATRZYMANY: {status.halted_reason}
        </div>
      )}
      {status.is_paused && !status.is_halted && (
        <div className="stat" style={{ color: "var(--amber)" }}>
          ⏸ Automat zapauzowany ręcznie
        </div>
      )}
    </div>
  );
}
