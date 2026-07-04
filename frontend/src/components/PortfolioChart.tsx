import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PortfolioSnapshot } from "../api/client";

export function PortfolioChart({ history, current }: { history: PortfolioSnapshot[]; current: PortfolioSnapshot | null }) {
  const data = history.map((h) => ({
    time: new Date(h.timestamp).toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }),
    value: h.total_value_usdt,
  }));

  return (
    <div className="panel">
      <h2>Wartość portfela (USDT)</h2>
      {current && (
        <div style={{ marginBottom: 10 }}>
          <span className="stat">
            Aktualna wartość
            <strong>${current.total_value_usdt.toFixed(2)}</strong>
          </span>
        </div>
      )}
      <div style={{ width: "100%", height: 260 }}>
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis dataKey="time" tick={{ fontSize: 10 }} minTickGap={30} />
            <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10 }} width={70} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="var(--accent, #2563eb)" dot={false} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {data.length === 0 && <p className="subtitle">Brak jeszcze danych — pierwszy cykl automatu je utworzy.</p>}
    </div>
  );
}
