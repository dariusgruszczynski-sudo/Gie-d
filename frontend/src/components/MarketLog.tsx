import { useState } from "react";
import { PortfolioSnapshot } from "../api/client";
import { CollapsibleH2 } from "./CollapsibleH2";

export function MarketLog({ history, whitelist }: { history: PortfolioSnapshot[]; whitelist: string[] }) {
  const rows = [...history].reverse().slice(0, 40);
  const [open, setOpen] = useState(false); // long table -- collapsed by default

  return (
    <div className="panel">
      <CollapsibleH2 title="Log rynkowy" open={open} onToggle={() => setOpen((o) => !o)} summary={`${rows.length} cykli`} />
      {open && (
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
      )}
    </div>
  );
}
