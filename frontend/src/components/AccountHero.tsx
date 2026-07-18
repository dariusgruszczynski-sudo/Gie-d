import { MarketRegime, StatusResponse } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";

function fmt(v: number): string {
  return v.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmt0(v: number): string {
  return v.toLocaleString("pl-PL", { maximumFractionDigits: 0 });
}

/** Allocation donut (Gotówka / SESJA / POZA SESJĄ) with the invested-% in its
 *  hollow centre -- the bold visual anchor of the neo-bank hero, mirroring the
 *  activity-ring look. Pure SVG so it animates and stays crisp at any size. */
function AllocationRing({ cash, sesja, poza, invPct }: { cash: number; sesja: number; poza: number; invPct: number }) {
  const total = Math.max(cash + sesja + poza, 0.0001);
  const r = 52;
  const c = 2 * Math.PI * r;
  const segs = [
    { v: sesja, color: "var(--venue-us)" },
    { v: poza, color: "var(--venue-extended)" },
    { v: cash, color: "rgba(150,152,180,0.42)" },
  ];
  let offset = 0;
  const arcs = segs.map((s, i) => {
    const frac = Math.max(s.v, 0) / total;
    const len = frac * c;
    const el = (
      <circle
        key={i}
        cx="60"
        cy="60"
        r={r}
        fill="none"
        stroke={s.color}
        strokeWidth="14"
        strokeLinecap="butt"
        strokeDasharray={`${len} ${c - len}`}
        strokeDashoffset={-offset}
        className="nb-ring-arc"
      />
    );
    offset += len;
    return el;
  });
  return (
    <div className="nb-ring">
      <svg viewBox="0 0 120 120" width="120" height="120" style={{ transform: "rotate(-90deg)" }}>
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="14" />
        {arcs}
      </svg>
      <div className="nb-ring-center">
        <span className="nb-ring-pct">{invPct}%</span>
        <span className="nb-ring-cap">zainwest.</span>
      </div>
    </div>
  );
}

function PnlPill({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null;
  const up = value >= 0;
  return (
    <span className={`nb-pill ${up ? "up" : "down"}`}>
      <span className="nb-pill-arrow">{up ? "▲" : "▼"}</span>
      {up ? "+" : ""}
      {value.toFixed(2)}%<span className="nb-pill-label">{label}</span>
    </span>
  );
}

function regimeText(r: MarketRegime | null): { label: string; tone: string } {
  if (!r) return { label: "—", tone: "neutral" };
  if (r.regime === "risk_on") return { label: "sprzyja", tone: "on" };
  if (r.regime === "risk_off") return { label: "ostrożnie", tone: "off" };
  return { label: "neutralnie", tone: "neutral" };
}

/** One bold engine tile (SESJA / POZA SESJĄ) -- gradient card with live status,
 *  its slice of the account, and the current market read for that leg. */
function EngineTile({
  kind,
  name,
  sub,
  value,
  live,
  statusText,
  regime,
}: {
  kind: "sesja" | "poza";
  name: string;
  sub: string;
  value: number;
  live: boolean;
  statusText: string;
  regime: MarketRegime | null;
}) {
  const reg = regimeText(regime);
  return (
    <div className={`nb-engine nb-engine-${kind} ${live ? "is-live" : "is-off"}`}>
      <div className="nb-engine-glow" aria-hidden="true" />
      <div className="nb-engine-top">
        <span className="nb-engine-name">{name}</span>
        <span className={`nb-engine-badge ${live ? "live" : "off"}`}>
          <span className="nb-engine-dot" />
          {statusText}
        </span>
      </div>
      <div className="nb-engine-value">${fmt0(value)}</div>
      <div className="nb-engine-foot">
        <span className="nb-engine-sub">{sub}</span>
        <span className={`nb-engine-regime tone-${reg.tone}`}>{reg.label}</span>
      </div>
    </div>
  );
}

function StatTile({ label, value, tone }: { label: string; value: string; tone?: "up" | "down" | "plain" }) {
  return (
    <div className={`nb-stat nb-stat-${tone ?? "plain"}`}>
      <span className="nb-stat-label">{label}</span>
      <span className="nb-stat-value">{value}</span>
    </div>
  );
}

/** The bold neo-bank dashboard header: an allocation-ring hero with the big
 *  animated account value, two vibrant engine tiles, and a row of stat tiles.
 *  Everything else (edge, tokens, tuning) lives on the detail tabs. */
export function AccountHero({ status }: { status: StatusResponse }) {
  const account = status.account;
  const total = useCountUp(account?.total_value ?? 0);
  const cash = account?.cash ?? 0;
  const sesja = account?.equity_positions_value ?? 0;
  const poza = account?.extended_positions_value ?? 0;
  const invested = sesja + poza;
  const invPct = account && account.total_value > 0 ? Math.round((invested / account.total_value) * 100) : 0;

  const usLive = !status.is_halted && !status.is_paused;
  const usText = status.is_halted ? "HALT" : status.is_paused ? "STOP" : "aktywny";
  const extLive = status.extended_enabled && !status.extended_paused;
  const extText = !status.extended_enabled ? "wył." : status.extended_paused ? "STOP" : "aktywny";

  return (
    <>
      <div className="nb-hero">
        <div className="nb-hero-glow" aria-hidden="true" />
        <div className="nb-hero-main">
          <AllocationRing cash={cash} sesja={sesja} poza={poza} invPct={invPct} />
          <div className="nb-hero-figures">
            <span className="nb-hero-label">Wartość konta</span>
            <div className="nb-hero-value">
              {account ? `$${fmt(total)}` : <span className="nb-hero-pending">oczekiwanie na dane…</span>}
            </div>
            <div className="nb-hero-pills">
              <PnlPill label="dziś" value={status.day_pnl_pct} />
              <PnlPill label="tydzień" value={status.week_pnl_pct} />
            </div>
          </div>
        </div>
        {status.is_halted && status.halted_reason && <div className="nb-hero-halt">⛔ {status.halted_reason}</div>}
      </div>

      <div className="nb-engines">
        <EngineTile
          kind="sesja"
          name="SESJA"
          sub="akcje US · pełny swing"
          value={sesja}
          live={usLive}
          statusText={usText}
          regime={status.market_regime}
        />
        <EngineTile
          kind="poza"
          name="POZA SESJĄ"
          sub="tanie ETF · pre/after"
          value={poza}
          live={extLive}
          statusText={extText}
          regime={status.extended_market_regime}
        />
      </div>

      <div className="nb-stats">
        <StatTile label="Wolna gotówka" value={`$${fmt0(cash)}`} />
        <StatTile label="W grze" value={`$${fmt0(invested)}`} />
        <StatTile label="Zaangażowanie" value={`${invPct}%`} />
      </div>
    </>
  );
}
