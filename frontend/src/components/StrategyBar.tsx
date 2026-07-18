import { MarketRegime, StatusResponse } from "../api/client";

type State = { label: string; cls: string };

function equityState(s: StatusResponse): State {
  if (s.is_halted) return { label: "Zatrzymany — limit strat", cls: "halt" };
  if (s.is_paused) return { label: "Wstrzymany", cls: "paused" };
  return { label: "Aktywny", cls: "live" };
}

function extendedState(s: StatusResponse): State {
  if (!s.extended_enabled) return { label: "Wyłączony", cls: "off" };
  if (s.is_halted) return { label: "Zatrzymany — limit strat", cls: "halt" };
  if (s.extended_paused) return { label: "Wstrzymany", cls: "paused" };
  return { label: "Aktywny", cls: "live" };
}

function marketRead(regime: MarketRegime | null): string {
  if (!regime) return "rynek: brak danych";
  if (regime.regime === "risk_on") return "rynek sprzyja";
  if (regime.regime === "risk_off") return "rynek słaby";
  return "rynek neutralny";
}

/** One clear line per engine: what the brain is actually doing right now, in
 *  plain words -- stance (self-tuned aggression), market read, and the signal
 *  it trades on -- instead of a cryptic "KRYPTO RISK-OFF" chip. */
function Leg({
  venue,
  name,
  state,
  regime,
  signal,
}: {
  venue: "alpaca" | "extended";
  name: string;
  state: State;
  regime: MarketRegime | null;
  signal: string;
}) {
  const stance = regime?.aggression_label ? `nastawienie ${regime.aggression_label}` : "nastawienie bazowe";
  const dimmed = state.cls === "off";
  return (
    <div className={`strat-leg strat-leg-${venue} ${dimmed ? "strat-leg-dim" : ""}`}>
      <div className="strat-leg-top">
        <span className={`venue-dot venue-dot-${venue}`} />
        <span className="strat-leg-name">{name}</span>
        <span className={`strat-state strat-state-${state.cls}`}>{state.label}</span>
      </div>
      <div className="strat-leg-desc">
        {dimmed ? (
          <span className="strat-muted">silnik wyłączony — nie handluje</span>
        ) : (
          <>
            <span className="strat-stance">{stance}</span>
            <span className="strat-sep">·</span>
            <span>{marketRead(regime)}</span>
            <span className="strat-sep">·</span>
            <span className="strat-signal">{signal}</span>
          </>
        )}
      </div>
    </div>
  );
}

/** Persistent top strip: at-a-glance strategy for BOTH brains. */
export function StrategyBar({ status }: { status: StatusResponse }) {
  return (
    <div className="strat-bar">
      <Leg
        venue="alpaca"
        name="Akcje US"
        state={equityState(status)}
        regime={status.market_regime}
        signal="sygnał dzienny · sesja"
      />
      <Leg
        venue="extended"
        name="Poza sesją"
        state={extendedState(status)}
        regime={status.extended_market_regime}
        signal="swingi 15-min · całodobowo"
      />
    </div>
  );
}
