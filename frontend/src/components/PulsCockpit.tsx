import { useEffect, useState } from "react";
import { MarketRegime, StatusResponse } from "../api/client";

/** Countdown helper -> "2g 14m" / "9m 30s". */
function fmtLeft(ms: number): string {
  if (ms <= 0) return "wkrótce";
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}g ${m}m`;
  if (m > 0) return `${m}m ${sec}s`;
  return `${sec}s`;
}

function regimeMeter(r: MarketRegime | null): { label: string; tone: string; fill: number } {
  if (!r) return { label: "brak danych", tone: "neutral", fill: 0.5 };
  if (r.regime === "risk_on") return { label: "sprzyja wejściom", tone: "on", fill: 0.82 };
  if (r.regime === "risk_off") return { label: "ostrożnie", tone: "off", fill: 0.22 };
  return { label: "neutralnie", tone: "neutral", fill: 0.5 };
}

function RegimeRow({ name, regime }: { name: string; regime: MarketRegime | null }) {
  const m = regimeMeter(regime);
  return (
    <div className="puls-regime">
      <div className="puls-regime-head">
        <span className="puls-regime-name">{name}</span>
        <span className={`puls-regime-label tone-${m.tone}`}>{m.label}</span>
      </div>
      <div className="puls-meter">
        <span className={`puls-meter-fill tone-${m.tone}`} style={{ width: `${m.fill * 100}%` }} />
      </div>
    </div>
  );
}

/** Live "pulse" of the machine: the US session state with a ticking countdown to
 *  the next open/close, both engines' market read as animated meters, and the
 *  engines' live run state. Everything is backend-grounded (status), the only
 *  motion is the 1s clock — a real cockpit, not decoration. */
export function PulsCockpit({ status }: { status: StatusResponse }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const open = status.market_session === "regular";
  const b = status.session_bounds;
  const targetIso = open ? b?.regular_close : b?.regular_open;
  const target = targetIso ? Date.parse(targetIso) : NaN;
  const left = Number.isFinite(target) ? target - now : NaN;
  const clock = new Date(now).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  const usLive = !status.is_halted && !status.is_paused;
  const extLive = status.extended_enabled && !status.extended_paused;

  return (
    <div className="puls">
      {/* Rynek US — stan sesji + żywy licznik */}
      <div className={`puls-tile puls-market ${open ? "is-open" : "is-closed"}`}>
        <div className="puls-tile-top">
          <span className="puls-eyebrow">Rynek US</span>
          <span className="puls-clock">{clock}</span>
        </div>
        <div className="puls-market-state">
          <span className={`puls-live-dot ${open ? "on" : ""}`} />
          {open ? "SESJA OTWARTA" : "ZAMKNIĘTE"}
        </div>
        <div className="puls-countdown">
          {Number.isFinite(left) ? (
            <>
              <b>{fmtLeft(left)}</b> {open ? "do zamknięcia" : "do otwarcia"}
            </>
          ) : (
            <span className="puls-muted">poza godzinami handlu</span>
          )}
        </div>
      </div>

      {/* Nastawienie — mierniki reżimu obu nóg */}
      <div className="puls-tile">
        <span className="puls-eyebrow">Nastawienie rynku</span>
        <div className="puls-regimes">
          <RegimeRow name="SESJA" regime={status.market_regime} />
          <RegimeRow name="POZA SESJĄ" regime={status.extended_market_regime} />
        </div>
      </div>

      {/* Automat — stan silników */}
      <div className="puls-tile">
        <span className="puls-eyebrow">Automat</span>
        <div className="puls-engines">
          <div className="puls-engine">
            <span className={`puls-engine-dot ${usLive ? "live" : "off"}`} />
            <span className="puls-engine-name">SESJA</span>
            <span className="puls-engine-state">
              {status.is_halted ? "HALT" : status.is_paused ? "STOP" : "handluje"}
            </span>
          </div>
          <div className="puls-engine">
            <span className={`puls-engine-dot ${extLive ? "live" : "off"}`} />
            <span className="puls-engine-name">POZA</span>
            <span className="puls-engine-state">
              {!status.extended_enabled ? "wył." : status.extended_paused ? "STOP" : "handluje"}
            </span>
          </div>
        </div>
        <div className="puls-cadence">podgląd rynku co ~{status.poll_interval_minutes} min</div>
      </div>
    </div>
  );
}
