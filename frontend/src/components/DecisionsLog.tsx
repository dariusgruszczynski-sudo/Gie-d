import { Decision } from "../api/client";

function contextSummary(d: Decision): string | null {
  const parts: string[] = [];
  try {
    const ctx = JSON.parse(d.market_context_snapshot || "{}");
    if (typeof ctx.fear_greed_index === "number") parts.push(`F&G ${ctx.fear_greed_index}`);
    if (typeof ctx.btc_dominance_pct === "number") parts.push(`BTC.D ${ctx.btc_dominance_pct}%`);
  } catch {
    // older rows before this field existed -- ignore
  }
  try {
    if (d.symbol) {
      const marketData = JSON.parse(d.market_data_snapshot || "{}");
      const technical = marketData[d.symbol]?.technical;
      if (technical?.rsi_14 != null) parts.push(`RSI ${technical.rsi_14}`);
      if (technical?.macd_signal && technical.macd_signal !== "insufficient_data") {
        parts.push(`MACD ${technical.macd_signal}`);
      }
    }
  } catch {
    // older rows before this field existed -- ignore
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function DecisionsLog({ decisions }: { decisions: Decision[] }) {
  return (
    <div className="panel">
      <h2>Log decyzji Claude</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Czas</th>
              <th>Wyzwolone przez</th>
              <th>Decyzja</th>
              <th>Symbol</th>
              <th>Rozmiar</th>
              <th>Pewność</th>
              <th>Status</th>
              <th>Kontekst</th>
              <th>Uzasadnienie</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((d) => {
              const context = contextSummary(d);
              return (
                <tr key={d.id}>
                  <td>{new Date(d.timestamp).toLocaleString("pl-PL")}</td>
                  <td>{d.triggered_by}</td>
                  <td>
                    <span className={`badge ${d.action}`}>{d.action}</span>
                  </td>
                  <td>{d.symbol ?? "—"}</td>
                  <td>{d.size_pct ? `${d.size_pct.toFixed(1)}%` : "—"}</td>
                  <td>{(d.confidence * 100).toFixed(0)}%</td>
                  <td>
                    {d.rejection_reason ? (
                      <span className="rejection">odrzucone</span>
                    ) : d.executed ? (
                      "wykonane"
                    ) : (
                      "brak akcji"
                    )}
                  </td>
                  <td className="context-cell">{context ?? "—"}</td>
                  <td className="reasoning">{d.rejection_reason ?? d.reasoning}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {decisions.length === 0 && <p className="subtitle">Brak jeszcze decyzji.</p>}
      </div>
    </div>
  );
}
