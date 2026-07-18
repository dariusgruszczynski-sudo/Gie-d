import { PortfolioSnapshot } from "../api/client";

export function money(v: number | null | undefined, dp = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const neg = v < 0;
  const s = Math.abs(v).toLocaleString("pl-PL", { minimumFractionDigits: dp, maximumFractionDigits: dp });
  return `${neg ? "−" : ""}$${s}`;
}
export function money0(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `$${Math.round(v).toLocaleString("pl-PL")}`;
}
export function pct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}
export function ago(iso: string): string {
  const d = Date.parse(iso);
  if (!Number.isFinite(d)) return "";
  const s = Math.floor((Date.now() - d) / 1000);
  if (s < 60) return "przed chwilą";
  if (s < 3600) return `${Math.floor(s / 60)} min temu`;
  if (s < 86400) return `${Math.floor(s / 3600)} godz temu`;
  return `${Math.floor(s / 86400)} dni temu`;
}

/** Full-width equity band — an SVG area chart with a soft gradient fill and an
 *  end node. Colour follows the trend (mint up / rose down). */
export function EquityBand({ history }: { history: PortfolioSnapshot[] }) {
  const vals = history.map((h) => h.total_value_usdt).filter((v) => v > 0);
  if (vals.length < 2) return <div className="gd-band-empty">Zbieram krzywą konta…</div>;
  const w = 1000;
  const h = 116;
  const pad = 6;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const up = vals[vals.length - 1] >= vals[0];
  const col = up ? "var(--mint)" : "var(--rose)";
  const x = (i: number) => pad + (i / (vals.length - 1)) * (w - 2 * pad);
  const y = (v: number) => h - pad - ((v - min) / range) * (h - 2 * pad);
  const line = vals.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(vals.length - 1).toFixed(1)},${h} L${x(0).toFixed(1)},${h} Z`;
  const lx = x(vals.length - 1);
  const ly = y(vals[vals.length - 1]);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id="gdBandFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={col} stopOpacity="0.28" />
          <stop offset="100%" stopColor={col} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill="url(#gdBandFill)" className="gd-band-area" />
      <path d={line} fill="none" stroke={col} strokeWidth="2.4" vectorEffect="non-scaling-stroke" pathLength={1} className="gd-line" />
      <circle cx={lx} cy={ly} r="9" fill={col} opacity="0.22" className="gd-band-halo" />
      <circle cx={lx} cy={ly} r="3.4" fill={col} />
    </svg>
  );
}

/** Scrolling ticker tape of the tradable universe (both legs), with live last
 *  prices when the latest snapshot has them — a continuous "video" band. */
export function TickerTape({ sesja, poza, prices }: { sesja: string[]; poza: string[]; prices: Record<string, number> }) {
  const items = [...sesja.map((s) => ({ s, leg: "sesja" as const })), ...poza.map((s) => ({ s, leg: "poza" as const }))];
  if (items.length === 0) return null;
  const row = [...items, ...items]; // duplicate for a seamless loop
  return (
    <div className="gd-tape">
      <div className="gd-tape-track">
        {row.map((it, i) => (
          <span className="gd-tape-item" key={i}>
            <span className={`gd-leg-dot ${it.leg}`} />
            <span className="s">{it.s}</span>
            {prices[it.s] !== undefined && <span className="p">{money(prices[it.s])}</span>}
          </span>
        ))}
      </div>
    </div>
  );
}

export function Icon({ name }: { name: "console" | "engines" | "control" | "pulse" }) {
  const p = { fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "console":
      return <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="2" {...p} /><path d="M7 20h10M8 11l3 3 5-6" {...p} /></svg>;
    case "engines":
      return <svg viewBox="0 0 24 24"><path d="M4 15l4-4 3 2 5-6 4 4" {...p} /><path d="M4 20h16" {...p} /></svg>;
    case "control":
      return <svg viewBox="0 0 24 24"><path d="M5 8h14M5 16h14" {...p} /><circle cx="10" cy="8" r="2.4" {...p} /><circle cx="15" cy="16" r="2.4" {...p} /></svg>;
    case "pulse":
      return <svg viewBox="0 0 24 24"><path d="M3 12h4l2-6 3 12 2-7 2 3h5" {...p} /></svg>;
  }
}
