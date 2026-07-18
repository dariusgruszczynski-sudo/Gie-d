import { AccountView } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";

function fmt(v: number): string {
  return v.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/** The ONE Alpaca account, shown once — not two portfolios. Cash is a single
 *  shared pool; the two engines each contribute only their positions' value. */
export function AccountBar({
  account,
  dayPnlPct,
}: {
  account: AccountView | null;
  dayPnlPct: number | null;
}) {
  const total = useCountUp(account?.total_value ?? 0);
  if (!account) {
    return (
      <div className="account-bar">
        <span className="account-bar-pending">Konto Alpaca — oczekiwanie na dane…</span>
      </div>
    );
  }
  const dayUp = (dayPnlPct ?? 0) >= 0;
  return (
    <div className="account-bar">
      <div className="account-bar-main">
        <span className="account-bar-label">Konto Alpaca — ile masz</span>
        <strong className="account-bar-total">${fmt(total)}</strong>
        {dayPnlPct !== null && (
          <span className={`account-bar-day ${dayUp ? "up" : "down"}`}>
            {dayUp ? "+" : ""}
            {dayPnlPct.toFixed(2)}% dziś
          </span>
        )}
      </div>
      <div className="account-bar-split">
        <span className="account-bar-chip">
          <span className="account-bar-chip-label">Wolna gotówka</span>
          <span className="account-bar-chip-val">${fmt(account.cash)}</span>
        </span>
        <span className="account-bar-chip">
          <span className="venue-dot venue-dot-alpaca" />
          <span className="account-bar-chip-label">Akcje US</span>
          <span className="account-bar-chip-val">${fmt(account.equity_positions_value)}</span>
        </span>
        <span className="account-bar-chip">
          <span className="venue-dot venue-dot-extended" />
          <span className="account-bar-chip-label">Poza sesją</span>
          <span className="account-bar-chip-val">${fmt(account.extended_positions_value)}</span>
        </span>
      </div>
    </div>
  );
}
