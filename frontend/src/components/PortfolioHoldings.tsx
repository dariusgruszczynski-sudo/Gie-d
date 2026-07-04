import { PortfolioSnapshot } from "../api/client";

interface HoldingRow {
  asset: string;
  quantity: number;
  price: number | null;
  valueUsd: number;
  pctOfPortfolio: number;
}

function buildHoldings(current: PortfolioSnapshot): HoldingRow[] {
  const balances: Record<string, number> = JSON.parse(current.balances_json || "{}");
  const prices: Record<string, number> = JSON.parse(current.prices_json || "{}");
  const total = current.total_value_usdt || 0;

  const rows: HoldingRow[] = Object.entries(balances)
    .filter(([, qty]) => qty > 0)
    .map(([asset, qty]) => {
      const symbol = `${asset}USDT`;
      const price = prices[symbol] ?? null;
      const valueUsd = price !== null ? qty * price : 0;
      return {
        asset,
        quantity: qty,
        price,
        valueUsd,
        pctOfPortfolio: total > 0 ? (valueUsd / total) * 100 : 0,
      };
    });

  rows.sort((a, b) => b.valueUsd - a.valueUsd);

  if (current.usdt_balance > 0) {
    rows.push({
      asset: "USDT",
      quantity: current.usdt_balance,
      price: 1,
      valueUsd: current.usdt_balance,
      pctOfPortfolio: total > 0 ? (current.usdt_balance / total) * 100 : 0,
    });
  }

  return rows;
}

export function PortfolioHoldings({ current }: { current: PortfolioSnapshot | null }) {
  return (
    <div className="panel">
      <h2>Twoje pozycje</h2>
      <p className="subtitle" style={{ marginTop: -6, marginBottom: 12 }}>
        Rozbicie aktualnej wartości portfela na poszczególne monety (nie tylko sama suma w dolarach).
      </p>
      <div className="table-wrap">
        {current && current.total_value_usdt > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Aktywo</th>
                <th>Ilość</th>
                <th>Cena</th>
                <th>Wartość</th>
                <th>% portfela</th>
              </tr>
            </thead>
            <tbody>
              {buildHoldings(current).map((row) => (
                <tr key={row.asset}>
                  <td>{row.asset}</td>
                  <td>{row.quantity.toLocaleString("pl-PL", { maximumFractionDigits: 6 })}</td>
                  <td>{row.price !== null ? `$${row.price.toLocaleString("pl-PL", { maximumFractionDigits: 2 })}` : "—"}</td>
                  <td>${row.valueUsd.toLocaleString("pl-PL", { maximumFractionDigits: 2 })}</td>
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
