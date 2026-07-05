import { PortfolioSnapshot } from "../api/client";

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

function buildHoldings(current: PortfolioSnapshot, costBasis: Record<string, number>): HoldingRow[] {
  const balances: Record<string, number> = JSON.parse(current.balances_json || "{}");
  const prices: Record<string, number> = JSON.parse(current.prices_json || "{}");
  const total = current.total_value_usdt || 0;

  const rows: HoldingRow[] = Object.entries(balances)
    .filter(([, qty]) => qty > 0)
    .map(([asset, qty]) => {
      const symbol = `${asset}EUR`;
      const price = prices[symbol] ?? null;
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

  if (current.usdt_balance > 0) {
    rows.push({
      asset: "EUR",
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

function fmtEur(value: number): string {
  return value.toLocaleString("pl-PL", { maximumFractionDigits: 2 });
}

export function PortfolioHoldings({
  current,
  costBasis,
}: {
  current: PortfolioSnapshot | null;
  costBasis: Record<string, number>;
}) {
  return (
    <div className="panel">
      <h2>Twoje pozycje</h2>
      <p className="subtitle" style={{ marginTop: -6, marginBottom: 12 }}>
        Rozbicie portfela na monety z ceną wejścia i bieżącym zyskiem/stratą (niezrealizowanym) na każdej pozycji.
      </p>
      <div className="table-wrap">
        {current && current.total_value_usdt > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Aktywo</th>
                <th>Ilość</th>
                <th>Cena</th>
                <th>Wejście</th>
                <th>Zysk/strata</th>
                <th>Wartość</th>
                <th>% portfela</th>
              </tr>
            </thead>
            <tbody>
              {buildHoldings(current, costBasis).map((row) => (
                <tr key={row.asset}>
                  <td>{row.asset}</td>
                  <td>{row.quantity.toLocaleString("pl-PL", { maximumFractionDigits: 6 })}</td>
                  <td>{row.price !== null ? `€${fmtEur(row.price)}` : "—"}</td>
                  <td>{row.entryPrice !== null ? `€${fmtEur(row.entryPrice)}` : "—"}</td>
                  <td>
                    {row.pnlPct !== null ? (
                      <span className={row.pnlPct >= 0 ? "up" : "down"}>
                        {row.pnlPct >= 0 ? "+" : ""}
                        {row.pnlPct.toFixed(2)}%
                        {row.pnlUsd !== null ? ` (${row.pnlUsd >= 0 ? "+" : ""}€${fmtEur(row.pnlUsd)})` : ""}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>€{fmtEur(row.valueUsd)}</td>
                  <td>{row.pctOfPortfolio.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="subtitle">Brak jeszcze danych o portfelu — pierwszy cykl automatu je utworzy.</p>
        )}
      </div>
    </div>
  );
}
