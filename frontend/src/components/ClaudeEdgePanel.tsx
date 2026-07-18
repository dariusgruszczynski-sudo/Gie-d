import { useState } from "react";
import { api, ClaudeEdge } from "../api/client";

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function Side({ title, side, sub }: { title: string; side: ClaudeEdge["mechanical_only"]; sub: string }) {
  return (
    <div className="edge-side">
      <h3 className="edge-side-title">{title}</h3>
      <div className="edge-side-body">
        <div className="profile-row">
          <span>Zamknięte transakcje</span>
          <b>{side.closed_trades}</b>
        </div>
        <div className="profile-row">
          <span>Trafność</span>
          <b>{side.win_rate_pct !== null ? `${side.win_rate_pct}%` : "—"} ({side.wins}W / {side.losses}L)</b>
        </div>
        {side.avg_return_pct !== undefined && (
          <div className="profile-row">
            <span>Śr. zwrot / transakcję</span>
            <b className={(side.avg_return_pct ?? 0) >= 0 ? "up" : "down"}>{fmtPct(side.avg_return_pct)}</b>
          </div>
        )}
      </div>
      <p className="subtitle edge-side-note">{sub}</p>
    </div>
  );
}

/** Answers "czy Claude zarabia na siebie": retrospective, on-demand comparison
 *  of what the mechanical filter alone would have done vs what Claude-directed
 *  trading actually did, recomputed from stored decision history. Never
 *  touches the live trading path. */
export function ClaudeEdgePanel({ venue }: { venue: "alpaca" | "extended" }) {
  const [data, setData] = useState<ClaudeEdge | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      setData(await api.claudeEdge(venue));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>Czy Claude zarabia na siebie?</h2>
        <button className="btn-secondary" disabled={busy} onClick={run}>
          {busy ? "Liczę…" : data ? "Przelicz ponownie" : "Sprawdź"}
        </button>
      </div>
      <p className="subtitle" style={{ marginTop: 0 }}>
        Porównanie retrospektywne: co zrobiłby sam filtr mechaniczny (bez Claude) na tych samych danych, kontra co
        faktycznie zrobił Claude. Liczone na żądanie z historii decyzji — nie dotyka realnego handlu.
      </p>

      {error && <p className="error-text">{error}</p>}

      {data && (
        <>
          <p className="subtitle" style={{ marginBottom: 12 }}>
            Przeanalizowano {data.cycles_analyzed} cykli.
          </p>
          <div className="edge-grid">
            <Side
              title="Sam mechanizm (bez Claude)"
              side={data.mechanical_only}
              sub={`Symulacja na stałej stawce $1000/pozycję — ${data.mechanical_only.notional_realized_usd !== undefined ? `wynik $${data.mechanical_only.notional_realized_usd.toFixed(2)}` : ""} (orientacyjnie, nie 1:1 z realnym kontem).`}
            />
            <Side
              title="Z Claude (jak działo się naprawdę)"
              side={data.with_claude}
              sub={`Realny wynik: $${(data.with_claude.realized_usd ?? 0).toFixed(2)} na tym silniku.`}
            />
          </div>
          <p className="subtitle edge-fineprint">
            Liczby w dolarach nie są 1:1 porównywalne (mechanizm liczy na stałej stawce, realne konto na zmiennej
            wielkości pozycji) — patrz przede wszystkim na <strong>trafność</strong> i <strong>średni zwrot na
            transakcję</strong>: jeśli Claude ma wyraźnie wyższą trafność/zwrot niż sam mechanizm, jego warstwa
            decyzyjna dokłada wartość ponad filtr. Jeśli nie — sam mechanizm wystarczy taniej.
          </p>
        </>
      )}
    </div>
  );
}
