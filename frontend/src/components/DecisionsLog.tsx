import { Decision } from "../api/client";

export function DecisionsLog({ decisions }: { decisions: Decision[] }) {
  return (
    <div className="panel">
      <h2>Log decyzji Claude Opus</h2>
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
              <th>Uzasadnienie</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((d) => (
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
                <td className="reasoning">{d.rejection_reason ?? d.reasoning}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {decisions.length === 0 && <p className="subtitle">Brak jeszcze decyzji.</p>}
      </div>
    </div>
  );
}
