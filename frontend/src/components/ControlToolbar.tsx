import { useEffect, useState } from "react";
import { api, StatusResponse } from "../api/client";

type IconName = "pause" | "play" | "bolt" | "bell" | "restart" | "logout" | "refresh" | "sound" | "muted" | "power";

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
    case "power":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 3v8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          <path
            d="M6.5 6.5a8 8 0 1 0 11 0"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "bell":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M6 9a6 6 0 1 1 12 0c0 4 1.5 5.5 2 6H4c.5-.5 2-2 2-6Z"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinejoin="round"
          />
          <path d="M10 19a2 2 0 0 0 4 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
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
    case "sound":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 9v6h4l5 4V5L8 9H4Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
          <path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8 8 0 0 1 0 12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
    case "muted":
      return (
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M4 9v6h4l5 4V5L8 9H4Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
          <path d="M17 9.5l4 5M21 9.5l-4 5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        </svg>
      );
  }
}

export function ControlToolbar({
  status,
  onChanged,
  muted,
  onToggleMuted,
  onShutdown,
}: {
  status: StatusResponse;
  onChanged: () => void;
  muted: boolean;
  onToggleMuted: () => void;
  onShutdown?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ text: string; kind: "ok" | "error" } | null>(null);

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
        <div className="toolbar-section">
          <span className="toolbar-section-label">Globalne</span>
          <div className="toolbar-row">
            <button className="btn-secondary" disabled={busy} onClick={() => run(api.sendReportNow, false)}>
              <Icon name="bell" />
              Wyślij podsumowanie
            </button>
            <button
              className="btn-secondary"
              disabled={busy}
              title="Po dolaniu/wypłacie kasy (np. eToro): przelicza baseline P&L na obecną wartość konta, żeby 'zysk dziś' nie liczył wpłaty jako zysku."
              onClick={() => {
                if (window.confirm("Przeliczyć P&L od nowa? Baseline dnia i tygodnia ustawi się na obecną wartość konta (użyj po dolaniu/wypłacie kasy).")) {
                  run(() => api.healthReset("rebaseline_pnl"));
                }
              }}
            >
              <Icon name="refresh" />
              Przelicz P&L
            </button>
          </div>
        </div>

        <div className="toolbar-divider" />

        <div className="toolbar-section toolbar-section-end">
          <span className="toolbar-section-label">Ustawienia</span>
          <div className="toolbar-row">
            <button className="btn-ghost" onClick={onToggleMuted} title={muted ? "Włącz dźwięk transakcji" : "Wycisz dźwięk transakcji"}>
              <Icon name={muted ? "muted" : "sound"} />
              {muted ? "Dźwięk: wył." : "Dźwięk: wł."}
            </button>
            <button className="btn-ghost" disabled={busy} onClick={logOff}>
              <Icon name="logout" />
              Wyloguj
            </button>
            <button className="btn-outline-danger" disabled={busy} onClick={() => run(api.restart, false)} title="Restartuje proces automatu">
              <Icon name="restart" />
              Restart
            </button>
            {onShutdown && (
              <button
                className="btn-ghost"
                onClick={onShutdown}
                title="Tylko widok: pokazuje ekran ładowania i przeładowuje apkę od zera (pobiera najnowszą wersję). Handel automatyczny NIE zatrzymuje się — to nie jest STOP."
              >
                <Icon name="power" />
                Wyłącz (odśwież widok)
              </button>
            )}
          </div>
        </div>
      </div>
      {feedback && <p className={feedback.kind === "error" ? "error-text" : "toolbar-feedback"}>{feedback.text}</p>}
    </div>
  );
}
