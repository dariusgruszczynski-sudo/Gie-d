import { useEffect, useState } from "react";
import { api, StatusResponse } from "../api/client";

type IconName = "pause" | "play" | "bolt" | "mail" | "restart";

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

  return (
    <div className="toolbar-wrap">
      <div className="toolbar">
        <button className={isStopped ? "btn-primary" : "btn-danger"} disabled={busy} onClick={() => run(isStopped ? api.resume : api.pause)}>
          <Icon name={isStopped ? "play" : "pause"} />
          {isStopped ? "Wznów automat" : "Zatrzymaj automat"}
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
      </div>
      {feedback && <p className={feedback.kind === "error" ? "error-text" : "toolbar-feedback"}>{feedback.text}</p>}
    </div>
  );
}
