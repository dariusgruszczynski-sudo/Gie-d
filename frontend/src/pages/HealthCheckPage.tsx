import { useCallback, useEffect, useState } from "react";
import { api, HealthCheck, HealthReport, HealthStatus } from "../api/client";

const STATUS_META: Record<HealthStatus, { light: string; label: string }> = {
  ok: { light: "green", label: "OK" },
  warn: { light: "amber", label: "Uwaga" },
  down: { light: "red", label: "Awaria" },
  off: { light: "grey", label: "Wył." },
};

// Human labels for the reset buttons a probe can attach.
const ACTION_LABEL: Record<string, string> = {
  reset_budget_meter: "Wyzeruj licznik budżetu",
  resume_alpaca: "Wznów silnik US",
  resume_crypto: "Wznów silnik krypto",
  clear_halt: "Zdejmij halt",
  refresh_snapshots: "Odśwież snapshoty",
  restart_scheduler: "Restart schedulera",
};

const GROUP_ORDER = ["Integracje", "Połączenia", "Funkcjonalności"];

function TrafficLight({ status }: { status: HealthStatus }) {
  return <span className={`hc-light hc-light-${STATUS_META[status].light}`} aria-label={STATUS_META[status].label} />;
}

function CheckRow({ c, onReset, busy }: { c: HealthCheck; onReset: (a: string) => void; busy: string | null }) {
  return (
    <div className={`hc-row hc-row-${STATUS_META[c.status].light}`}>
      <TrafficLight status={c.status} />
      <div className="hc-row-main">
        <div className="hc-row-label">{c.label}</div>
        <div className="hc-row-detail">{c.detail}</div>
      </div>
      {c.action && (
        <button className="hc-reset-btn" disabled={busy !== null} onClick={() => onReset(c.action!)}>
          {busy === c.action ? "…" : (ACTION_LABEL[c.action] ?? "Reset")}
        </button>
      )}
    </div>
  );
}

/** Health check: traffic-light status of every integration, connection and
 *  internal function, with one-click resets for the ones that can jam. */
export function HealthCheckPage() {
  const [report, setReport] = useState<HealthReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setReport(await api.health());
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runReset(action: string) {
    setBusyAction(action);
    setToast(null);
    try {
      const res = await api.healthReset(action);
      setToast(res.message);
      await load(); // re-probe so the lights reflect the new state
    } catch (e) {
      setToast(`Błąd: ${e}`);
    } finally {
      setBusyAction(null);
    }
  }

  const groups = GROUP_ORDER.map((g) => ({
    name: g,
    items: (report?.checks ?? []).filter((c) => c.group === g),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="hc-page">
      <div className="panel hc-header-panel">
        <div className="hc-header">
          <div>
            <h2 style={{ margin: 0 }}>Health check</h2>
            <p className="subtitle" style={{ margin: "4px 0 0" }}>
              Status integracji, połączeń i funkcji na żywo. Zielone = OK, żółte = uwaga, czerwone = awaria. Zacięte
              elementy zresetujesz guzikiem.
            </p>
          </div>
          <button className="btn-primary hc-refresh" onClick={load} disabled={loading}>
            {loading ? "Sprawdzam…" : "Sprawdź teraz"}
          </button>
        </div>
        {report && (
          <div className="hc-summary">
            <span className={`hc-overall hc-overall-${STATUS_META[report.overall].light}`}>
              <TrafficLight status={report.overall} /> {STATUS_META[report.overall].label}
            </span>
            <span className="hc-counts">
              🟢 {report.counts.ok} · 🟡 {report.counts.warn} · 🔴 {report.counts.down} · ⚪ {report.counts.off}
            </span>
            <span className="hc-checked-at">
              {new Date(report.checked_at).toLocaleTimeString("pl-PL")}
            </span>
          </div>
        )}
        {toast && <div className="hc-toast">{toast}</div>}
        {error && <div className="hc-toast hc-toast-err">Błąd: {error}</div>}
      </div>

      {!report && loading && (
        <div className="panel">
          <p className="subtitle" style={{ margin: 0 }}>
            Sprawdzam integracje (Alpaca, Claude, newsy)… to potrwa kilka sekund.
          </p>
        </div>
      )}

      {groups.map((g) => (
        <div className="panel hc-group" key={g.name}>
          <h3 className="hc-group-title">{g.name}</h3>
          <div className="hc-list">
            {g.items.map((c) => (
              <CheckRow key={c.key} c={c} onReset={runReset} busy={busyAction} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
