import { useEffect, useState } from "react";
import { api } from "../api/client";

/** Per-portfolio control panel: START/STOP, refresh, force-analysis for one
 *  venue (Alpaca equities or extended), each independent of the other. */
export function VenueControls({
  venue,
  label,
  paused,
  halted,
  enabled,
  onChanged,
}: {
  venue: "alpaca" | "extended";
  label: string;
  paused: boolean;
  halted?: boolean;
  enabled: boolean;
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ text: string; kind: "ok" | "error" } | null>(null);
  const stopped = paused || !!halted;

  useEffect(() => {
    if (!feedback) return;
    const id = setTimeout(() => setFeedback(null), 4500);
    return () => clearTimeout(id);
  }, [feedback]);

  async function run(action: () => Promise<unknown>, okText?: string) {
    setBusy(true);
    setFeedback(null);
    try {
      const res = (await action()) as { message?: string };
      setFeedback({ text: res?.message || okText || "OK", kind: "ok" });
      onChanged();
    } catch (e) {
      setFeedback({ text: String(e), kind: "error" });
    } finally {
      setBusy(false);
    }
  }

  const accent = venue === "extended" ? "extended" : "alpaca";

  if (!enabled) {
    return (
      <div className={`panel venue-controls venue-controls-${accent}`}>
        <div className="venue-controls-head">
          <span className={`venue-dot venue-dot-${accent}`} /> {label}
        </div>
        <p className="subtitle" style={{ margin: 0 }}>
          Portfel wyłączony — włącz go (EXTENDED_ENABLED=true) i zasil konto, żeby sterować handlem.
        </p>
      </div>
    );
  }

  return (
    <div className={`panel venue-controls venue-controls-${accent}`}>
      <div className="venue-controls-head">
        <span className={`venue-dot venue-dot-${accent}`} /> {label}
        <span className={`toolbar-status-dot ${stopped ? "" : "toolbar-status-dot-live"}`} style={{ marginLeft: "auto" }} />
        <span className="toolbar-status-hint">{halted ? "zatrzymany (limit strat)" : stopped ? "nie handluje" : "aktywny"}</span>
      </div>
      <div className="venue-controls-row">
        <button
          className={`btn-hero ${stopped ? "btn-primary" : "btn-danger"}`}
          disabled={busy}
          onClick={() => run(() => (stopped ? api.resume(venue) : api.pause(venue)))}
        >
          {stopped ? "START" : "STOP"}
        </button>
        <button className="btn-secondary" disabled={busy} onClick={() => run(() => api.refreshPortfolio(venue), "Portfel odświeżony")}>
          Odśwież portfel
        </button>
        <button className="btn-secondary" disabled={busy} onClick={() => run(() => api.runCycleNow(venue), "Analiza wymuszona")}>
          Wymuś analizę
        </button>
      </div>
      {feedback && <p className={feedback.kind === "error" ? "error-text" : "toolbar-feedback"} style={{ marginBottom: 0 }}>{feedback.text}</p>}
    </div>
  );
}
