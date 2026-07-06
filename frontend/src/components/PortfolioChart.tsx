import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { PortfolioSnapshot, Scorecard } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";

function ChartTooltip({ active, payload, label, benchmarkSymbol }: any) {
  if (!active || !payload || !payload.length) return null;
  const byKey: Record<string, number> = {};
  for (const p of payload) byKey[p.dataKey] = Number(p.value);
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-time">{label}</div>
      <div className="chart-tooltip-value">${(byKey.value ?? 0).toFixed(2)}</div>
      {byKey.benchmark !== undefined && (
        <div className="chart-tooltip-benchmark">
          {benchmarkSymbol} (kup i trzymaj): ${byKey.benchmark.toFixed(2)}
        </div>
      )}
    </div>
  );
}

const RANGES = [
  { key: "1D", hours: 24 },
  { key: "1W", hours: 24 * 7 },
  { key: "1M", hours: 24 * 30 },
  { key: "ALL", hours: Infinity },
] as const;

type RangeKey = (typeof RANGES)[number]["key"];

export function PortfolioChart({
  history,
  current,
  scorecard,
}: {
  history: PortfolioSnapshot[];
  current: PortfolioSnapshot | null;
  scorecard: Scorecard | null;
}) {
  const [range, setRange] = useState<RangeKey>("1D");

  const cutoffHours = RANGES.find((r) => r.key === range)?.hours ?? Infinity;
  const cutoff = Number.isFinite(cutoffHours) ? Date.now() - cutoffHours * 3600 * 1000 : 0;
  const filtered = history.filter((h) => new Date(h.timestamp).getTime() >= cutoff);

  // Buy-and-hold benchmark overlay: what the portfolio would be worth if the
  // starting value had just been parked in the benchmark ticker. Each
  // snapshot stores that ticker's price, so the whole series is reconstructed
  // client-side from the baseline the backend anchors at inception.
  const baselinePrice = scorecard?.benchmark_start_price ?? null;
  const baselineValue = scorecard?.benchmark_start_value ?? null;
  const benchmarkSymbol = scorecard?.benchmark_symbol ?? "SPY";
  const hasBenchmark = baselinePrice !== null && baselineValue !== null && baselinePrice > 0;

  const data = filtered.map((h) => {
    let benchmark: number | null = null;
    if (hasBenchmark) {
      try {
        const prices = JSON.parse(h.prices_json || "{}");
        const p = prices[benchmarkSymbol];
        if (typeof p === "number" && p > 0) benchmark = baselineValue! * (p / baselinePrice!);
      } catch {
        // malformed snapshot -- skip the benchmark point, keep the value line
      }
    }
    return {
      time: new Date(h.timestamp).toLocaleString("pl-PL", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }),
      value: h.total_value_usdt,
      benchmark,
    };
  });

  const first = data[0]?.value ?? 0;
  const last = data[data.length - 1]?.value ?? 0;
  const isUp = last >= first;
  const periodChangePct = first > 0 ? ((last - first) / first) * 100 : null;
  const animatedValue = useCountUp(current?.total_value_usdt ?? 0);
  const benchmarkVisible = hasBenchmark && data.some((d) => d.benchmark !== null);

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>Wartość portfela (USD)</h2>
        <div className="chart-range-tabs">
          {RANGES.map((r) => (
            <button
              key={r.key}
              className={`chart-range-tab ${range === r.key ? "active" : ""}`}
              onClick={() => setRange(r.key)}
              type="button"
            >
              {r.key}
            </button>
          ))}
        </div>
      </div>
      {current && (
        <div className="chart-value-row">
          <strong className="chart-current-value">${animatedValue.toFixed(2)}</strong>
          {periodChangePct !== null && (
            <span className={`chart-period-change ${isUp ? "up" : "down"}`}>
              {isUp ? "+" : ""}
              {periodChangePct.toFixed(2)}% ({range})
            </span>
          )}
          {benchmarkVisible && (
            <span className="chart-benchmark-legend">
              <span className="chart-benchmark-swatch" /> {benchmarkSymbol} kup i trzymaj
            </span>
          )}
        </div>
      )}
      <div style={{ width: "100%", height: 280 }}>
        <ResponsiveContainer>
          <AreaChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={isUp ? "var(--green)" : "var(--red)"} stopOpacity={0.35} />
                <stop offset="100%" stopColor={isUp ? "var(--green)" : "var(--red)"} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 6" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="time" tick={{ fontSize: 10, fill: "var(--muted)" }} minTickGap={30} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
            <YAxis domain={["auto", "auto"]} tick={{ fontSize: 10, fill: "var(--muted)" }} width={70} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip benchmarkSymbol={benchmarkSymbol} />} />
            {benchmarkVisible && (
              <Area
                type="monotone"
                dataKey="benchmark"
                stroke="var(--muted)"
                strokeWidth={1.5}
                strokeDasharray="5 4"
                fill="none"
                dot={false}
                activeDot={{ r: 3 }}
                connectNulls
              />
            )}
            <Area
              type="monotone"
              dataKey="value"
              stroke={isUp ? "var(--green)" : "var(--red)"}
              strokeWidth={2}
              fill="url(#portfolioFill)"
              dot={false}
              activeDot={{ r: 4 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      {data.length === 0 && <p className="subtitle">Brak jeszcze danych w tym zakresie.</p>}
    </div>
  );
}
