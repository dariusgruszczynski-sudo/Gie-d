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
  extendedHoursEnabled,
  extendedHoursAutoUsd,
  lastCycleAt,
  pollIntervalMinutes,
}: {
  session: MarketSession;
  bounds: SessionBounds | null;
  extendedHoursEnabled: boolean;
  extendedHoursAutoUsd: number;
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
            <span>Pre-market {fmtBoundary(bounds.pre_market_start)}</span>
            <span>Otwarcie {fmtBoundary(bounds.regular_open)}</span>
            <span>Zamknięcie {fmtBoundary(bounds.regular_close)}</span>
            <span>Po sesji do {fmtBoundary(bounds.after_hours_end)}</span>
          </div>
        </div>
      )}
      {extendedHoursEnabled ? (
        <p className="subtitle" style={{ marginTop: 10, marginBottom: 0 }}>
          Rozszerzone godziny handlu (pre-market/after-hours) są aktywne — automat monitoruje rynek ~16h/dobę.
        </p>
      ) : (
        <p className="subtitle" style={{ marginTop: 10, marginBottom: 0 }}>
          Automat handluje tylko w sesji regularnej.
          {extendedHoursAutoUsd > 0
            ? ` Rozszerzone godziny (pre-market/after-hours) włączą się automatycznie po przekroczeniu $${extendedHoursAutoUsd.toFixed(0)} wartości portfela.`
            : ""}
        </p>
      )}
    </div>
  );
}
