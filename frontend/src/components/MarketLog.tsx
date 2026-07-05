import { PortfolioSnapshot } from "../api/client";

export function MarketLog({ history, whitelist }: { history: PortfolioSnapshot[]; whitelist: string[] }) {
  const rows = [...history].reverse().slice(0, 40);

  return (
    <div className="panel">
      <h2>Log rynkowy</h2>
      <p className="subtitle" style={{ marginTop: -6, marginBottom: 12 }}>
        Zapis z każdego cyklu automatu — niezależnie od tego, czy padła pełna decyzja Claude.
      </p>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Czas</th>
              <th>Wartość portfela</th>
              {whitelist.map((s) => (
                <th key={s}>{s}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const prices: Record<string, number> = JSON.parse(r.prices_json || "{}");
              return (
                <tr key={r.id}>
                  <td>{new Date(r.timestamp).toLocaleString("pl-PL")}</td>
                  <td>${r.total_value_usdt.toFixed(2)}</td>
                  {whitelist.map((s) => (
                    <td key={s}>{prices[s] !== undefined ? `$${prices[s].toFixed(2)}` : "—"}</td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
        {rows.length === 0 && <p className="subtitle">Brak jeszcze zapisów — pierwszy cykl automatu je utworzy.</p>}
      </div>
    </div>
  );
}
