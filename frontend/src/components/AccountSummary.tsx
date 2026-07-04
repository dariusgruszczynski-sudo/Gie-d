import { PortfolioSnapshot } from "../api/client";

export function AccountSummary({
  current,
  inception,
}: {
  current: PortfolioSnapshot | null;
  inception: PortfolioSnapshot | null;
}) {
  if (!current) {
    return (
      <div className="account-summary">
        <span className="account-summary-pending">oczekiwanie na dane…</span>
      </div>
    );
  }

  const hasBaseline = inception !== null && inception.total_value_usdt > 0;
  const pnlUsd = hasBaseline ? current.total_value_usdt - inception!.total_value_usdt : null;
  const pnlPct = hasBaseline ? (pnlUsd! / inception!.total_value_usdt) * 100 : null;
  const up = (pnlUsd ?? 0) >= 0;

  return (
    <div className="account-summary">
      <div className="account-summary-item">
        <span className="account-summary-label">Ile masz</span>
        <strong className="account-summary-value">€{current.total_value_usdt.toFixed(2)}</strong>
      </div>
      <div className="account-summary-divider" />
      <div className="account-summary-item">
        <span className="account-summary-label">Od początku</span>
        {pnlUsd !== null ? (
          <strong className={`account-summary-value ${up ? "up" : "down"}`}>
            {up ? "+" : ""}
            {pnlUsd.toFixed(2)}€ ({up ? "+" : ""}
            {pnlPct!.toFixed(2)}%)
          </strong>
        ) : (
          <strong className="account-summary-value">—</strong>
        )}
      </div>
    </div>
  );
}
