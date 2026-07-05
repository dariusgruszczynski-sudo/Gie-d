import { Trade } from "../api/client";

export function TradesTable({ trades }: { trades: Trade[] }) {
  return (
    <div className="panel">
      <h2>Historia transakcji</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Czas</th>
              <th>Symbol</th>
              <th>Strona</th>
              <th>Ilość</th>
              <th>Cena</th>
              <th>Wartość USD</th>
              <th>Tryb</th>
              <th>Źródło</th>
            </tr>
          </thead>
          <tbody>
            {trades.map((t) => (
              <tr key={t.id}>
                <td>{new Date(t.timestamp).toLocaleString("pl-PL")}</td>
                <td>{t.symbol}</td>
                <td>
                  <span className={`badge ${t.side}`}>{t.side}</span>
                </td>
                <td>{t.quantity}</td>
                <td>${t.price.toFixed(2)}</td>
                <td>${t.usdt_value.toFixed(2)}</td>
                <td>{t.mode}</td>
                <td>{t.is_manual ? "ręczna" : "automat"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {trades.length === 0 && <p className="subtitle">Brak transakcji.</p>}
      </div>
    </div>
  );
}
