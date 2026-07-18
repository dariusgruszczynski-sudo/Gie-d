import { usePushNotifications } from "../hooks/usePushNotifications";

function BellIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M6 9a6 6 0 1 1 12 0c0 4 1.5 5.5 2 6H4c.5-.5 2-2 2-6Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
      />
      <path d="M10 19a2 2 0 0 0 4 0" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

/** Opt-in do powiadomień push na telefon / Apple Watch, w kolorystyce apki.
 *  Powiadomienie leci przy każdej realnej transakcji: co, ile, po ile, stan $. */
export function NotificationSettings() {
  const { state, busy, message, enable, disable, test } = usePushNotifications();

  return (
    <div className="panel notif-panel">
      <div className="notif-head">
        <span className="notif-icon">
          <BellIcon />
        </span>
        <div>
          <h2 style={{ margin: 0 }}>Powiadomienia na telefon</h2>
          <p className="subtitle" style={{ margin: "2px 0 0" }}>
            Push przy każdym kupnie/sprzedaży: co, ile, po ile i stan konta — prosto na telefon i Apple Watch.
          </p>
        </div>
        <span className={`notif-state notif-state-${state}`}>
          {state === "on"
            ? "włączone"
            : state === "denied"
              ? "zablokowane"
              : state === "unsupported"
                ? "brak wsparcia"
                : state === "server-off"
                  ? "serwer wył."
                  : "wyłączone"}
        </span>
      </div>

      <div className="notif-actions">
        {state === "on" ? (
          <>
            <button className="btn-danger" disabled={busy} onClick={disable}>
              Wyłącz na tym urządzeniu
            </button>
            <button className="btn-secondary" disabled={busy} onClick={test}>
              Wyślij test
            </button>
          </>
        ) : (
          <button
            className="btn-primary"
            disabled={busy || state === "unsupported" || state === "server-off" || state === "denied"}
            onClick={enable}
          >
            Włącz powiadomienia
          </button>
        )}
      </div>

      {message && <p className="toolbar-feedback" style={{ marginBottom: 0 }}>{message}</p>}
    </div>
  );
}
