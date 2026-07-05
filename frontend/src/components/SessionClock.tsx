import { useEffect, useState } from "react";
import { MarketSession, SessionBounds } from "../api/client";

const TIMEZONES: { label: string; tz: string }[] = [
  { label: "Warszawa", tz: "Europe/Warsaw" },
  { label: "Nowy Jork", tz: "America/New_York" },
  { label: "Los Angeles", tz: "America/Los_Angeles" },
];

const WARSAW_TZ = "Europe/Warsaw";

const SESSION_LABELS: Record<string, { label: string; className: string }> = {
  closed: { label: "GIEŁDA ZAMKNIĘTA", className: "session-badge-closed" },
  pre_market: { label: "PRE-MARKET", className: "session-badge-pre" },
  regular: { label: "SESJA OTWARTA", className: "session-badge-regular" },
  after_hours: { label: "AFTER-HOURS", className: "session-badge-after" },
};

function fmtTime(date: Date, tz: string): string {
  return date.toLocaleTimeString("pl-PL", { timeZone: tz, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function fmtBoundary(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("pl-PL", { timeZone: WARSAW_TZ, hour: "2-digit", minute: "2-digit" });
}

export function SessionClock({
  session,
  bounds,
  extendedHoursEnabled,
}: {
  session: MarketSession;
  bounds: SessionBounds | null;
  extendedHoursEnabled: boolean;
}) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const sessionInfo = session ? SESSION_LABELS[session] : null;

  return (
    <div className="panel">
      <div className="panel-header-row">
        <h2>Zegar sesji</h2>
        {sessionInfo && <span className={`session-badge ${sessionInfo.className}`}>{sessionInfo.label}</span>}
      </div>
      <div className="session-clock-times">
        {TIMEZONES.map((z) => (
          <div className="session-clock-tz" key={z.tz}>
            <span className="session-clock-tz-label">{z.label}</span>
            <span className="session-clock-tz-time">{fmtTime(now, z.tz)}</span>
          </div>
        ))}
      </div>
      {bounds && (
        <div className="session-clock-schedule">
          <span className="subtitle">Harmonogram sesji US (czas Warszawa):</span>
          <div className="session-clock-schedule-row">
            <span>Pre-market {fmtBoundary(bounds.pre_market_start)}</span>
            <span>Otwarcie {fmtBoundary(bounds.regular_open)}</span>
            <span>Zamknięcie {fmtBoundary(bounds.regular_close)}</span>
            <span>Po sesji do {fmtBoundary(bounds.after_hours_end)}</span>
          </div>
        </div>
      )}
      {!extendedHoursEnabled && (
        <p className="subtitle" style={{ marginTop: 10, marginBottom: 0 }}>
          Rozszerzone godziny handlu (pre-market/after-hours) są wyłączone — automat handluje tylko w sesji
          regularnej.
        </p>
      )}
    </div>
  );
}
