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
  regular: { label: "SESJA OTWARTA", className: "session-badge-regular" },
};

function fmtTime(date: Date, tz: string): string {
  return date.toLocaleTimeString("pl-PL", { timeZone: tz, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function fmtBoundary(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("pl-PL", { timeZone: WARSAW_TZ, hour: "2-digit", minute: "2-digit" });
}

function fmtAgo(iso: string, now: Date): string {
  const mins = Math.max(0, Math.round((now.getTime() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "przed chwilą";
  if (mins === 1) return "1 min temu";
  if (mins < 60) return `${mins} min temu`;
  const hours = Math.floor(mins / 60);
  return `${hours} h ${mins % 60} min temu`;
}

export function SessionClock({
  session,
  bounds,
  lastCycleAt,
  pollIntervalMinutes,
}: {
  session: MarketSession;
  bounds: SessionBounds | null;
  lastCycleAt: string | null;
  pollIntervalMinutes: number;
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
      {lastCycleAt && (
        <p className="subtitle" style={{ marginTop: 0, marginBottom: 10 }}>
          Ostatni cykl automatu: <strong>{fmtAgo(lastCycleAt, now)}</strong> · sprawdza rynek co{" "}
          {pollIntervalMinutes} min
        </p>
      )}
      {bounds && (
        <div className="session-clock-schedule">
          <span className="subtitle">Harmonogram sesji US (czas Warszawa):</span>
          <div className="session-clock-schedule-row">
            <span>Otwarcie {fmtBoundary(bounds.regular_open)}</span>
            <span>Zamknięcie {fmtBoundary(bounds.regular_close)}</span>
          </div>
        </div>
      )}
      <p className="subtitle" style={{ marginTop: 10, marginBottom: 0 }}>
        Automat na akcjach US handluje tylko w sesji regularnej (~6.5h/dobę). Handel nocny/24-7 obsługuje osobny
        portfel krypto.
      </p>
    </div>
  );
}
