import { Scorecard as ScorecardData } from "../api/client";

function fmtUsd(v: number): string {
  const sign = v >= 0 ? "+" : "−";
  return `${sign}$${Math.abs(v).toFixed(2)}`;
}

function fmtPct(v: number): string {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

export function Scorecard({ data }: { data: ScorecardData | null }) {
  if (!data) return null;

  const hasAlpha = data.alpha_pct !== null && data.alpha_usd !== null;
  const beating = (data.alpha_pct ?? 0) >= 0;

  return (
    <div className="panel" style={{ marginBottom: 16 }}>
      <div className="panel-header-row">
        <h2>Wynik vs trzymanie {data.benchmark_symbol}</h2>
        {hasAlpha && (
          <span className={`session-badge ${beating ? "session-badge-regular" : "session-badge-closed"}`}>
            {beating ? "BIJESZ RYNEK" : "PONIŻEJ RYNKU"}
          </span>
        )}
      </div>
      <p className="subtitle" style={{ marginTop: -6, marginBottom: 12 }}>
        Czy aktywny handel wygrywa z biernym trzymaniem {data.benchmark_symbol}? Jeśli nie — lepiej po prostu trzymać
        indeks.
      </p>
      <div className="scorecard-grid">
        <div className="scorecard-tile">
          <span className="scorecard-label">Twój portfel</span>
          <strong>${data.portfolio_value.toFixed(2)}</strong>
        </div>
        <div className="scorecard-tile">
          <span className="scorecard-label">Gdybyś trzymał {data.benchmark_symbol}</span>
          <strong>{data.benchmark_value !== null ? `$${data.benchmark_value.toFixed(2)}` : "—"}</strong>
        </div>
        <div className="scorecard-tile">
          <span className="scorecard-label">Przewaga (alpha)</span>
          <strong className={hasAlpha ? (beating ? "up" : "down") : ""}>
            {hasAlpha ? `${fmtUsd(data.alpha_usd!)} (${fmtPct(data.alpha_pct!)})` : "—"}
          </strong>
        </div>
        <div className="scorecard-tile">
          <span className="scorecard-label">Zrealizowany P&L</span>
          <strong className={data.realized_pnl_usd >= 0 ? "up" : "down"}>{fmtUsd(data.realized_pnl_usd)}</strong>
        </div>
        <div className="scorecard-tile">
          <span className="scorecard-label">Trafność</span>
          <strong>
            {data.win_rate_pct !== null ? `${data.win_rate_pct.toFixed(0)}%` : "—"}
            <span className="scorecard-sub">
              {" "}
              ({data.wins}W / {data.losses}L)
            </span>
          </strong>
        </div>
      </div>
    </div>
  );
}
