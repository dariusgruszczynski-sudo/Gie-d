import { useState } from "react";
import { PortfolioSnapshot } from "../api/client";
import { CollapsibleH2 } from "./CollapsibleH2";

interface HoldingRow {
  asset: string;
  quantity: number;
  price: number | null;
  valueUsd: number;
  pctOfPortfolio: number;
  entryPrice: number | null;
  pnlPct: number | null;
  pnlUsd: number | null;
}

function buildHoldings(
  current: PortfolioSnapshot,
  costBasis: Record<string, number>,
  showCash: boolean,
  denominator: number,
): HoldingRow[] {
  const balances: Record<string, number> = JSON.parse(current.balances_json || "{}");
  const prices: Record<string, number> = JSON.parse(current.prices_json || "{}");
  // % is against the WHOLE account (shared cash counted once at the account
  // level), so a position's weight is honest across both engines.
  const total = denominator > 0 ? denominator : current.total_value_usdt || 0;

  const rows: HoldingRow[] = Object.entries(balances)
    .filter(([, qty]) => qty > 0)
    .map(([asset, qty]) => {
      const price = prices[asset] ?? null;
      const valueUsd = price !== null ? qty * price : 0;
      const entryPrice = costBasis[asset] ?? null;
      const pnlPct = price !== null && entryPrice !== null && entryPrice > 0 ? ((price - entryPrice) / entryPrice) * 100 : null;
      const pnlUsd = price !== null && entryPrice !== null ? (price - entryPrice) * qty : null;
      return {
        asset,
        quantity: qty,
        price,
        valueUsd,
        pctOfPortfolio: total > 0 ? (valueUsd / total) * 100 : 0,
        entryPrice,
        pnlPct,
        pnlUsd,
      };
    });

  rows.sort((a, b) => b.valueUsd - a.valueUsd);

  // Cash is a single ACCOUNT-level pool, not an engine's holding -- it's shown
  // once in the account bar, so per-engine tables omit it to avoid the
  // double-count the "two portfolios" view had.
  if (showCash && current.usdt_balance > 0) {
    rows.push({
      asset: "USD",
      quantity: current.usdt_balance,
      price: 1,
      valueUsd: current.usdt_balance,
      pctOfPortfolio: total > 0 ? (current.usdt_balance / total) * 100 : 0,
      entryPrice: null,
      pnlPct: null,
      pnlUsd: null,
    });
  }

  return rows;
}

function fmtUsd(value: number): string {
  return value.toLocaleString("pl-PL", { maximumFractionDigits: 2 });
}

export function PortfolioHoldings({
  current,
  costBasis,
  title = "Twoje pozycje",
  defaultCollapsed = false,
  showCash = true,
  accountTotal = 0,
}: {
  current: PortfolioSnapshot | null;
  costBasis: Record<string, number>;
  title?: string;
  defaultCollapsed?: boolean;
  showCash?: boolean;
  accountTotal?: number;
}) {
  const [open, setOpen] = useState(!defaultCollapsed);
  const rows = current ? buildHoldings(current, costBasis, showCash, accountTotal) : [];
  return (
    <div className="panel">
      <CollapsibleH2 title={title} open={open} onToggle={() => setOpen((o) => !o)} />
      {open && (
      <div className="table-wrap">
        {rows.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Aktywo</th>
                <th>Ilość</th>
                <th>Cena</th>
                <th>Wejście</th>
                <th>Zysk/strata</th>
                <th>Wartość</th>
                <th>% konta</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.asset}>
                  <td>{row.asset}</td>
                  <td>{row.quantity.toLocaleString("pl-PL", { maximumFractionDigits: 6 })}</td>
                  <td>{row.price !== null ? `$${fmtUsd(row.price)}` : "—"}</td>
                  <td>{row.entryPrice !== null ? `$${fmtUsd(row.entryPrice)}` : "—"}</td>
                  <td>
                    {row.pnlPct !== null ? (
                      <span className={row.pnlPct >= 0 ? "up" : "down"}>
                        {row.pnlPct >= 0 ? "+" : ""}
                        {row.pnlPct.toFixed(2)}%
                        {row.pnlUsd !== null ? ` (${row.pnlUsd >= 0 ? "+" : ""}$${fmtUsd(row.pnlUsd)})` : ""}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>${fmtUsd(row.valueUsd)}</td>
                  <td>{row.pctOfPortfolio.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="subtitle">Ten silnik nie trzyma teraz żadnej pozycji — cała wolna gotówka jest wspólna dla konta.</p>
        )}
      </div>
      )}
    </div>
  );
}
