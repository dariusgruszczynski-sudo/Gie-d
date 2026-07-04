import { useEffect, useState } from "react";
import { api, StatusResponse } from "../api/client";

type IconName = "pause" | "play" | "bolt" | "mail" | "restart" | "logout" | "refresh";

function Icon({ name }: { name: IconName }) {
  switch (name) {
    case "pause":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
          <rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" />
          <rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" />
        </svg>
      );
    case "play":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 4 L20 12 L6 20 Z" fill="currentColor" />
        </svg>
      );
    case "bolt":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M13 2 L4 14 H11 L9 22 L20 8 H13 Z" fill="currentColor" />
        </svg>
      );
    case "mail":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M4 6 L12 13 L20 6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      );
    case "restart":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M4 12a8 8 0 1 1 2.6 5.9M4 12V6m0 6h6"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "logout":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M9 4 H5 a1 1 0 0 0 -1 1 v14 a1 1 0 0 0 1 1 h4 M16 8 L21 12 L16 16 M21 12 H9"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "refresh":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M20 12a8 8 0 1 1-2.3-5.6M20 4v4h-4"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
  }
}

export function ControlToolbar({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ text: string; kind: "ok" | "error" } | null>(null);
  const isStopped = status.is_paused || status.is_halted;

  useEffect(() => {
    if (!feedback) return;
    const id = setTimeout(() => setFeedback(null), 4500);
    return () => clearTimeout(id);
  }, [feedback]);

  async function run(action: () => Promise<{ message?: string } | unknown>, refreshAfter = true) {
    setBusy(true);
    setFeedback(null);
    try {
      const res = await action();
      const message = (res as { message?: string })?.message;
      if (message) setFeedback({ text: message, kind: "ok" });
      if (refreshAfter) onChanged();
    } catch (e) {
      setFeedback({ text: String(e), kind: "error" });
    } finally {
      setBusy(false);
    }
  }

  async function refreshPortfolio() {
    setBusy(true);
    setFeedback(null);
    try {
      const p = await api.refreshPortfolio();
      const cur = p.quote_currency === "EUR" ? "€" : p.quote_currency + " ";
      const failed = p.failed_symbols.length > 0 ? ` · brak ceny dla: ${p.failed_symbols.join(", ")}` : "";
      setFeedback({
        text: `Kraken OK — saldo ${cur}${p.total_value.toFixed(2)} (wolne ${cur}${p.quote_balance.toFixed(2)})${failed}`,
        kind: "ok",
      });
      onChanged();
    } catch (e) {
      setFeedback({ text: `Kraken niedostępny: ${String(e)}`, kind: "error" });
    } finally {
      setBusy(false);
    }
  }

  async function logOff() {
    setBusy(true);
    try {
      await api.logout();
    } catch {
      // Cookie may already be gone/expired -- either way, force back to the
      // login screen below rather than leaving the user stuck.
    } finally {
      // Full reload (not just local state) so AuthGate re-runs its /api/status
      // check against the now-cleared cookie and renders the login screen.
      window.location.reload();
    }
  }

  return (
    <div className="toolbar-wrap">
      <div className="toolbar">
        <button className={isStopped ? "btn-primary" : "btn-danger"} disabled={busy} onClick={() => run(isStopped ? api.resume : api.pause)}>
          <Icon name={isStopped ? "play" : "pause"} />
          {isStopped ? "START — automatyczny zakup/sprzedaż" : "STOP automat"}
        </button>
        <button className="btn-secondary" disabled={busy} onClick={refreshPortfolio}>
          <Icon name="refresh" />
          Odśwież portfel
        </button>
        <button className="btn-primary" disabled={busy} onClick={() => run(api.runCycleNow)}>
          <Icon name="bolt" />
          Wymuś analizę
        </button>
        <button className="btn-primary" disabled={busy} onClick={() => run(api.sendReportNow, false)}>
          <Icon name="mail" />
          Wyślij raport
        </button>
        <button className="btn-danger" disabled={busy} onClick={() => run(api.restart, false)}>
          <Icon name="restart" />
          Restart
        </button>
        <button className="btn-secondary" disabled={busy} onClick={logOff}>
          <Icon name="logout" />
          Wyloguj
        </button>
      </div>
      {feedback && <p className={feedback.kind === "error" ? "error-text" : "toolbar-feedback"}>{feedback.text}</p>}
    </div>
  );
}
