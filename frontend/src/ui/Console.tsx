import { useEffect, useState } from "react";
import { api, Decision, EngineProfile, isReadOnly, MarketRegime, PortfolioResponse, PositionPlan, SellPlan, SellState, StatusResponse } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";
import { ago, EquityBand, money, money0, pct, PnlBand, TickerTape } from "./kit";
import { NewsBar } from "./NewsBar";
import { Info } from "./Help";

export type Leg = "sesja" | "poza";
export interface Pos {
  asset: string; leg: Leg; venue: "alpaca" | "extended";
  qty: number; entry: number | null; price: number; value: number;
  pnlPct: number | null; pnlUsd: number | null;
}

export function extract(portfolio: PortfolioResponse | null, leg: Leg): Pos[] {
  const cur = portfolio?.current;
  if (!cur) return [];
  const balances: Record<string, number> = JSON.parse(cur.balances_json || "{}");
  const prices: Record<string, number> = JSON.parse(cur.prices_json || "{}");
  const cost = portfolio?.cost_basis ?? {};
  const out: Pos[] = [];
  for (const [asset, qtyRaw] of Object.entries(balances)) {
    const qty = Number(qtyRaw);
    const price = prices[asset];
    if (!(qty > 0) || price === undefined) continue;
    const value = qty * price;
    if (value < 1) continue;
    const entry = cost[asset] ?? null;
    out.push({
      asset, leg, venue: leg === "poza" ? "extended" : "alpaca", qty, entry, price, value,
      pnlPct: entry && entry > 0 ? ((price - entry) / entry) * 100 : null,
      pnlUsd: entry ? (price - entry) * qty : null,
    });
  }
  return out;
}

export function RegimeChip({ r }: { r: MarketRegime | null }) {
  if (!r) return <span className="gd-chip gd-chip-neu">brak danych</span>;
  if (r.regime === "risk_on") return <span className="gd-chip gd-chip-on">sprzyja</span>;
  if (r.regime === "risk_off") return <span className="gd-chip gd-chip-off">ostrożnie</span>;
  return <span className="gd-chip gd-chip-neu">neutralnie</span>;
}

function NowStrip({ status }: { status: StatusResponse }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const open = status.market_session === "regular";
  const b = status.session_bounds;
  const target = open ? b?.regular_close : b?.regular_open;
  const t = target ? Date.parse(target) : NaN;
  const left = Number.isFinite(t) ? t - now : NaN;
  const fmtLeft = (ms: number) => {
    if (ms <= 0) return "wkrótce";
    const s = Math.floor(ms / 1000), h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
    return h > 0 ? `${h}g ${m}m` : `${m}m ${s % 60}s`;
  };
  return (
    <div className="gd-now">
      <div className="gd-now-item">
        <span className="k">Rynek US</span>
        <span className="v" style={{ color: open ? "var(--mint)" : "var(--dim)" }}>
          {open ? "otwarty" : "zamknięty"}
        </span>
      </div>
      <div className="gd-now-sep" />
      <div className="gd-now-item">
        <span className="k">{open ? "Do zamknięcia" : "Do otwarcia"}</span>
        <span className="v">{Number.isFinite(left) ? fmtLeft(left) : "—"}</span>
      </div>
      <div className="gd-now-sep" />
      <div className="gd-now-item">
        <span className="k">Podgląd rynku</span>
        <span className="v">co ~{status.poll_interval_minutes} min</span>
      </div>
      <div className="gd-now-sep" />
      <div className="gd-now-item">
        <span className="k">Zegar</span>
        <span className="v" style={{ fontFamily: "var(--font-mono)" }}>
          {new Date(now).toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}

export function PosRow({ p, plan, note, onChanged }: { p: Pos; plan?: PositionPlan; note?: string; onChanged?: () => void }) {
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const up = (p.pnlPct ?? 0) >= 0;
  const mag = Math.min(100, Math.abs(p.pnlPct ?? 0) * 8);
  const noteText = plan?.note ?? note;
  const entry = plan?.basis ?? p.entry;
  const days = plan?.days_held;
  const daysLabel = days === null || days === undefined ? null : days === 0 ? "dziś" : days === 1 ? "1 dzień" : `${days} dni`;
  const hasCard = !!(plan && (daysLabel || entry || plan.stop_price || plan.target_price || plan.thesis));
  async function sell() {
    if (!window.confirm(`Sprzedać CAŁĄ pozycję ${p.asset} (~${money(p.value)})? Realne zlecenie.`)) return;
    setBusy(true);
    try { await api.sellAll(p.asset, p.venue); onChanged?.(); } finally { setBusy(false); }
  }
  return (
    <div className="gd-pos-row">
      <div className="gd-pos-tk">
        <span className={`gd-leg-dot ${p.leg}`} />
        <div>
          <b>{p.asset}</b>{daysLabel && <span className="gd-pos-days">· trzymana {daysLabel}</span>}
          {noteText && <div className="gd-pos-plan">{noteText}</div>}
          {hasCard && (
            <button className="gd-pos-more" onClick={() => setOpen((v) => !v)}>{open ? "ukryj plan ▲" : "plan pozycji ▾"}</button>
          )}
        </div>
      </div>
      <div className="gd-pos-fig">
        <div className="val">{money(p.value)}</div>
        <div className={`pct ${up ? "gd-up" : "gd-down"}`}>{p.pnlPct !== null ? pct(p.pnlPct) : "—"}</div>
      </div>
      {!isReadOnly && onChanged ? (
        <button className="gd-sell" disabled={busy} onClick={sell}>{busy ? "…" : "Sprzedaj"}</button>
      ) : <span />}
      <div className="gd-pos-bar">
        <span style={{ width: `${mag}%`, background: up ? "var(--mint)" : "var(--rose)", marginLeft: up ? "50%" : `${50 - mag}%` }} />
      </div>
      {hasCard && open && (
        <div className="gd-pos-card">
          <div className="gd-pos-levels">
            {entry ? <span><i>wejście</i><b>{money(entry)}</b></span> : null}
            {plan?.stop_price ? <span><i>stop</i><b className="gd-down">{money(plan.stop_price)}</b></span> : null}
            {plan?.target_price ? <span><i>cel</i><b className="gd-up">{money(plan.target_price)}</b></span> : null}
            {daysLabel ? <span><i>trzymana</i><b>{daysLabel}</b></span> : null}
          </div>
          {plan?.thesis && <div className="gd-pos-thesis">„{plan.thesis}"</div>}
        </div>
      )}
    </div>
  );
}

export function DecRow({ d }: { d: Decision }) {
  const tag = d.action.toLowerCase();
  return (
    <div className="gd-dec">
      <div className="gd-dec-rail">
        <span className={`gd-dec-tag ${tag}`}>{d.action}</span>
        <span className="gd-dec-line" />
      </div>
      <div>
        <div className="gd-dec-top">
          {d.symbol && <span className="gd-dec-sym">{d.symbol}</span>}
          <span className="gd-dec-leg">{(d.venue ?? "alpaca") === "extended" ? "poza sesją" : "sesja"}</span>
          <span className="gd-dec-conf">pewność {(d.confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="gd-dec-time">{ago(d.timestamp)}{d.executed ? " · wykonano" : ""}</div>
        {d.reasoning && <div className="gd-dec-reason">{d.reasoning}</div>}
        {d.rejection_reason && <div className="gd-dec-rej">⚠ {d.rejection_reason}</div>}
      </div>
    </div>
  );
}

/* Conviction Ladder — the signature widget for the PROGRESSIVE entry strategy:
   filled rungs = held positions; the meter shows the confidence the NEXT entry
   must clear (base + step × held). More positions => a taller bar to clear. */
export function ConvictionLadder({ held, profile }: { held: number; profile: EngineProfile }) {
  const max = profile.max_concurrent_positions || 0;
  const base = profile.min_buy_confidence || 0;
  const step = profile.progressive_confidence_step || 0;
  const cap = profile.progressive_confidence_cap || 0.9;
  const next = Math.min(cap, base + step * held);
  const full = max > 0 && held >= max;
  const slots = max > 0 ? Array.from({ length: max }, (_, i) => i < held) : [];
  return (
    <div className="gd-ladder">
      <div className="gd-ladder-top">
        <span className="gd-ladder-title">◇ Selektywność rośnie z pozycjami</span>
        <span className="gd-ladder-count">{held}<i>/{max || "∞"}</i></span>
      </div>
      {slots.length > 0 && (
        <div className="gd-rungs">
          {slots.map((on, i) => <span key={i} className={`gd-rung${on ? " on" : ""}`} style={{ transitionDelay: `${i * 35}ms` }} />)}
        </div>
      )}
      <div className="gd-ladder-next">
        {full ? (
          <span className="gd-ladder-full">Komplet pozycji — nowe wejście dopiero po wyjściu z którejś</span>
        ) : (
          <>
            <span className="gd-ladder-lbl">następne wejście wymaga pewności</span>
            <div className="gd-ladder-meter"><span style={{ width: `${Math.round(next * 100)}%` }} /></div>
            <b className="gd-ladder-pct">{Math.round(next * 100)}%</b>
          </>
        )}
      </div>
      {profile.conviction_sizing_enabled && (
        <div className="gd-ladder-conv">⚡ Duże zakłady na mocnych sygnałach — do {profile.conviction_size_max_mult ?? 2}× (sufit ryzyka {profile.conviction_max_risk_per_trade_pct ?? 6}%/trade)</div>
      )}
    </div>
  );
}

const REGIME_WX: Record<string, { icon: string; label: string; cls: string }> = {
  risk_on: { icon: "☀", label: "rynek sprzyja", cls: "on" },
  neutral: { icon: "⛅", label: "rynek neutralny", cls: "neu" },
  risk_off: { icon: "⛈", label: "ostrożnie — risk-off", cls: "off" },
};
function MarketWeather({ r }: { r: MarketRegime | null }) {
  const wx = (r && REGIME_WX[r.regime]) || { icon: "•", label: "brak danych", cls: "neu" };
  return (
    <div className={`gd-wx gd-wx-${wx.cls}`}>
      <span className="gd-wx-ico">{wx.icon}</span>
      <span className="gd-wx-lbl">{wx.label}</span>
    </div>
  );
}

/* Wygląd kafla „KIEDY SPRZEDAM" per stan planu wyjścia. */
const SELL_UI: Record<SellState, { cls: string; icon: string; label: string }> = {
  sell_now: { cls: "sellnow", icon: "🟢", label: "sprzedaję" },
  profit_ready: { cls: "ripe", icon: "🟢", label: "zysk do wzięcia" },
  climbing: { cls: "climb", icon: "↗", label: "rośnie" },
  locked: { cls: "locked", icon: "🔒", label: "anty-churn" },
  waiting: { cls: "wait", icon: "⏳", label: "czekam" },
  near_stop: { cls: "stop", icon: "⚠", label: "blisko stopu" },
};

/* "KIEDY SPRZEDAM" — miarka + jednozdaniowy plan wyjścia dla jednej pozycji.
   Wypełnienie miarki = jak blisko wyzwalacza sprzedaży (zysk→cel / strata→stop).
   Gdy rynek jest ZAMKNIĘTY, a plan chce działać „teraz" — mówimy uczciwie „na
   otwarciu", bo bot i tak nie wykona zlecenia przed otwarciem sesji. */
function SellGauge({ sp, marketClosed }: { sp: SellPlan; marketClosed?: boolean }) {
  const ui = SELL_UI[sp.state];
  const w = Math.max(3, Math.min(100, sp.progress_pct));
  const wantsNow = sp.state === "sell_now" || sp.state === "profit_ready" || sp.state === "near_stop";
  const blocked = !!marketClosed && wantsNow;
  return (
    <div className={`gd-sell-plan ${ui.cls}`}>
      <div className="gd-sp-head">
        <span className="gd-sp-eyebrow">Kiedy sprzedam</span>
        <span className="gd-sp-when">{blocked ? "na otwarciu" : sp.when}</span>
      </div>
      <div className="gd-sp-headline"><span className="gd-sp-ico">{ui.icon}</span>{sp.headline}</div>
      <div className="gd-sp-gauge"><span style={{ width: `${w}%` }} /></div>
      {blocked && <div className="gd-sp-closed">⏳ Rynek zamknięty — zlecenie wykona się na otwarciu sesji (albo sprzedaj ręcznie).</div>}
    </div>
  );
}

/* Position as a JOURNEY: stop ── entry ── [current] ── target, plus the
   "kiedy sprzedam" gauge that says WHEN and WHY the bot will close it. Directly
   answers the owner's worry: "there's a profit — why are you still holding?" */
export function PositionCard({ p, plan, bypassPct, marketOpen = true, onChanged }: {
  p: Pos; plan?: PositionPlan; bypassPct: number; marketOpen?: boolean; onChanged?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);
  const gain = p.pnlPct ?? 0;
  const up = gain >= 0;
  const entry = plan?.basis ?? p.entry ?? null;
  const stop = plan?.stop_price ?? null;
  const target = plan?.target_price ?? null;
  const cur = p.price;
  const days = plan?.days_held;
  const daysLabel = days === null || days === undefined ? null : days === 0 ? "dziś" : days === 1 ? "1 dzień" : `${days} dni`;

  const sp = plan?.sell_plan;
  // Highlight the card by its exit state (falls back to raw gain if no plan yet).
  const stateCls = sp ? SELL_UI[sp.state].cls : up ? "climb" : "wait";
  const ripe = sp ? (sp.state === "profit_ready" || sp.state === "sell_now") : (bypassPct > 0 && gain >= bypassPct);
  const nearStop = sp ? sp.state === "near_stop" : (stop !== null && cur <= stop * 1.015);

  // Track scale: stop → target (fall back to a band around entry/current).
  const lo = stop ?? (entry ? entry * 0.94 : cur * 0.94);
  const hi = target ?? (entry ? entry * 1.12 : cur * 1.12);
  const span = hi - lo || 1;
  const xOf = (v: number | null) => v === null ? null : Math.max(2, Math.min(98, ((v - lo) / span) * 100));
  const xEntry = xOf(entry), xCur = xOf(cur);
  const fillFrom = Math.min(xEntry ?? 50, xCur ?? 50), fillTo = Math.max(xEntry ?? 50, xCur ?? 50);

  async function sell() {
    if (!window.confirm(`Sprzedać CAŁĄ pozycję ${p.asset} (~${money(p.value)})? Realne zlecenie.`)) return;
    setBusy(true);
    try { await api.sellAll(p.asset, p.venue); onChanged?.(); } finally { setBusy(false); }
  }

  return (
    <div className={`gd-pcard st-${stateCls}${ripe ? " ripe" : ""}${nearStop ? " danger" : ""}`}>
      <div className="gd-pcard-top">
        <div className="gd-pcard-id">
          <b className="gd-pcard-sym">{p.asset}</b>
          {daysLabel && <span className="gd-pcard-days">{daysLabel}</span>}
          {sp && <span className={`gd-pcard-badge ${SELL_UI[sp.state].cls}`}>{SELL_UI[sp.state].icon} {SELL_UI[sp.state].label}</span>}
        </div>
        <div className="gd-pcard-fig">
          <span className="gd-pcard-val">{money(p.value)}</span>
          <span className={`gd-pcard-pct ${up ? "gd-up" : "gd-down"}`}>{p.pnlPct !== null ? pct(p.pnlPct) : "—"}</span>
        </div>
      </div>

      {sp && <SellGauge sp={sp} marketClosed={!marketOpen} />}

      <div className="gd-track">
        <div className="gd-track-line" />
        <div className={`gd-track-fill ${up ? "up" : "down"}`} style={{ left: `${fillFrom}%`, width: `${Math.max(0, fillTo - fillFrom)}%` }} />
        {stop !== null && <div className="gd-track-mark stop" style={{ left: `${xOf(stop)}%` }}><i /><em>stop</em></div>}
        {xEntry !== null && <div className="gd-track-mark entry" style={{ left: `${xEntry}%` }}><i /><em>wejście</em></div>}
        {target !== null && <div className="gd-track-mark target" style={{ left: `${xOf(target)}%` }}><i /><em>cel</em></div>}
        {xCur !== null && <div className={`gd-track-cur ${up ? "up" : "down"}`} style={{ left: `${xCur}%` }} title={`teraz ${money(cur)}`} />}
      </div>

      <div className="gd-pcard-foot">
        <span className="gd-pcard-lv">wejście <b>{entry ? money(entry) : "—"}</b> · teraz <b>{money(cur)}</b>{target ? <> · cel <b>{money(target)}</b></> : null}</span>
        <div className="gd-pcard-actions">
          {(sp?.detail || plan?.thesis) && <button className="gd-pcard-why" onClick={() => setOpen((v) => !v)}>{open ? "ukryj ▲" : "szczegóły ▾"}</button>}
          {!isReadOnly && onChanged && <button className="gd-sell" disabled={busy} onClick={sell}>{busy ? "…" : "Sprzedaj"}</button>}
        </div>
      </div>
      {open && (
        <div className="gd-pcard-detail">
          {sp?.detail && <div className="gd-pcard-plan">{sp.detail}</div>}
          {plan?.thesis && <div className="gd-pcard-thesis">„{plan.thesis}"</div>}
        </div>
      )}
    </div>
  );
}

/* Duży animowany kafel statystyki (deska rozdzielcza — screen 1). */
function StatCard({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "up" | "down" | "neu" }) {
  return (
    <div className={`gd-stat ${tone ?? "neu"}`}>
      <span className="gd-stat-l">{label}</span>
      <b className="gd-stat-v">{value}</b>
      {sub && <span className="gd-stat-sub">{sub}</span>}
    </div>
  );
}

/* Skuteczność po ludzku — pasek „ile transakcji na plus vs na minus" z konkretnymi
   liczbami i zdaniem wyjaśniającym, zamiast abstrakcyjnego pierścienia %. */
function WinBar({ pct: p, wins, losses }: { pct: number | null; wins: number; losses: number }) {
  const closed = wins + losses;
  if (closed === 0) {
    return (
      <div className="gd-skill">
        <div className="gd-skill-head"><span className="gd-skill-label">Skuteczność</span><b className="gd-skill-pct" style={{ color: "var(--dim)" }}>—</b></div>
        <div className="gd-skill-empty">Za mało zamkniętych transakcji, żeby liczyć — bot dopiero zbiera wynik.</div>
      </div>
    );
  }
  const v = p ?? (wins / closed) * 100;
  const col = v >= 50 ? "var(--mint)" : v >= 35 ? "var(--gold)" : "var(--rose)";
  const per10 = Math.round(v / 10);
  return (
    <div className="gd-skill">
      <div className="gd-skill-head">
        <span className="gd-skill-label">Skuteczność</span>
        <b className="gd-skill-pct" style={{ color: col }}>{Math.round(v)}%</b>
      </div>
      <div className="gd-skill-gloss">tyle transakcji kończy się na plus</div>
      <div className="gd-skill-bar">
        {wins > 0 && <span className="win" style={{ flexGrow: wins }}>{wins}</span>}
        {losses > 0 && <span className="loss" style={{ flexGrow: losses }}>{losses}</span>}
      </div>
      <div className="gd-skill-legend">
        <span className="gd-up">● {wins} na plus</span>
        <span className="gd-down">● {losses} na minus</span>
        <span className="gd-skill-per10">≈ {per10} na 10 udanych</span>
      </div>
    </div>
  );
}

/* SKALA RYZYKA — jeden czytelny wskaźnik „jak ryzykownie jest TERAZ", liczony
   przejrzyście z realnych czynników: ekspozycja (ile w grze), jak blisko
   automatycznych stopów (dzienny/tygodniowy limit straty, obsunięcie od szczytu)
   i nastawienie rynku. Marker na skali Niskie→Umiarkowane→Wysokie + konkretne
   powody pod spodem. */
function RiskScale({ status }: { status: StatusResponse }) {
  const acc = status.account;
  const invPct = acc && acc.total_value > 0
    ? Math.round(((acc.equity_positions_value ?? 0) + (acc.extended_positions_value ?? 0)) / acc.total_value * 100)
    : 0;
  const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

  const exposure = clamp01(invPct / 100);
  const dayLoss = status.daily_loss_limit_pct > 0 && status.day_pnl_pct != null
    ? clamp01(Math.max(0, -status.day_pnl_pct) / status.daily_loss_limit_pct) : 0;
  const weekLoss = status.weekly_loss_limit_pct > 0 && status.week_pnl_pct != null
    ? clamp01(Math.max(0, -status.week_pnl_pct) / status.weekly_loss_limit_pct) : 0;
  const dd = acc && status.peak_account_value > 0 && acc.total_value > 0
    ? (status.peak_account_value - acc.total_value) / status.peak_account_value * 100 : 0;
  const drawdown = status.max_drawdown_halt_pct > 0 ? clamp01(dd / status.max_drawdown_halt_pct) : 0;
  const regime = status.market_regime?.regime;
  const regimeRisk = regime === "risk_off" ? 1 : regime === "risk_on" ? 0.15 : 0.5;

  const lossProximity = Math.max(dayLoss, weekLoss, drawdown);
  let risk = 100 * (0.45 * lossProximity + 0.30 * exposure + 0.25 * regimeRisk);
  if (status.is_halted) risk = 100;
  risk = Math.round(Math.max(0, Math.min(100, risk)));

  const level = status.is_halted ? { t: "ZATRZYMANY", cls: "high" }
    : risk >= 66 ? { t: "Wysokie", cls: "high" }
    : risk >= 33 ? { t: "Umiarkowane", cls: "mid" }
    : { t: "Niskie", cls: "low" };

  // Konkretne powody (max 3), posortowane wg wagi ryzyka.
  const drivers: Array<{ label: string; tone: "hi" | "mid" | "lo" }> = [];
  drivers.push({ label: `w grze ${invPct}%`, tone: exposure >= 0.66 ? "hi" : exposure >= 0.33 ? "mid" : "lo" });
  drivers.push({
    label: regime === "risk_off" ? "rynek: ostrożnie" : regime === "risk_on" ? "rynek: sprzyja" : "rynek: neutralny",
    tone: regime === "risk_off" ? "hi" : regime === "risk_on" ? "lo" : "mid",
  });
  if (lossProximity >= 0.15) {
    const near = drawdown >= dayLoss && drawdown >= weekLoss ? `obsunięcie ${dd.toFixed(1)}%`
      : dayLoss >= weekLoss ? "blisko dziennego stopu" : "blisko tygodniowego stopu";
    drivers.push({ label: near, tone: lossProximity >= 0.6 ? "hi" : "mid" });
  } else {
    drivers.push({ label: "z dala od limitów strat", tone: "lo" });
  }

  const gloss = status.is_halted ? "Automat wstrzymany — limit ryzyka przekroczony."
    : level.cls === "high" ? "Wysoka ekspozycja lub blisko stopów — bot będzie ostrożny z nowymi wejściami."
    : level.cls === "mid" ? "Umiarkowanie — część kapitału pracuje, zapas do limitów jest."
    : "Bezpiecznie — dużo gotówki i daleko do limitów strat.";

  return (
    <div className={`gd-risk ${level.cls}`}>
      <div className="gd-risk-head">
        <span className="gd-risk-label">Skala ryzyka</span>
        <b className={`gd-risk-level ${level.cls}`}>{level.t}</b>
      </div>
      <div className="gd-risk-scale">
        <div className="gd-risk-track" />
        <div className="gd-risk-needle" style={{ left: `${risk}%` }}><i /></div>
      </div>
      <div className="gd-risk-ticks"><span>Niskie</span><span>Umiarkowane</span><span>Wysokie</span></div>
      <div className="gd-risk-gloss">{gloss}</div>
      <div className="gd-risk-drivers">
        {drivers.map((d, i) => <span key={i} className={`gd-risk-chip ${d.tone}`}>{d.label}</span>)}
      </div>
    </div>
  );
}

export function Console({ status, alpaca, extended, simple = false, onGoPositions }: {
  status: StatusResponse;
  alpaca: PortfolioResponse | null;
  extended: PortfolioResponse | null;
  simple?: boolean;
  onGoPositions: () => void;
}) {
  const acc = status.account;
  const total = useCountUp(acc?.total_value ?? 0);
  const cash = acc?.cash ?? 0;
  const sesjaVal = acc?.equity_positions_value ?? 0;
  const invested = sesjaVal + (acc?.extended_positions_value ?? 0);
  const invPct = acc && acc.total_value > 0 ? Math.round((invested / acc.total_value) * 100) : 0;

  const positions = [...extract(alpaca, "sesja"), ...extract(extended, "poza")];
  const sesjaCount = positions.length;
  const sc = alpaca?.scorecard ?? null;

  const usLive = !status.is_halted && !status.is_paused;

  const livePrices: Record<string, number> = {
    ...JSON.parse(alpaca?.current?.prices_json || "{}"),
    ...JSON.parse(extended?.current?.prices_json || "{}"),
  };

  const pnlUp = status.trading_pnl.total_usd >= 0;

  return (
    <div className="gd-view">
      <TickerTape sesja={status.whitelist} poza={status.extended_enabled ? status.extended_whitelist : []} prices={livePrices} />
      <div className="gd-topline">
        <span className="gd-kicker">Pulpit · {new Date().toLocaleDateString("pl-PL", { weekday: "long", day: "numeric", month: "long" })}</span>
        <span className={`gd-mode ${status.mode === "live" ? "live" : ""}`}>
          <span className="gd-blip" />{status.mode === "live" ? "LIVE" : "PAPER"}
        </span>
      </div>

      {status.is_halted && status.halted_reason && <div className="gd-halt">⛔ {status.halted_reason}</div>}

      {/* HERO — jedna, wielka liczba: ile bot dorobił. Reszta niżej, w sekcjach. */}
      <div className="gd-hero">
        <div className="gd-hero-label">💰 Zysk automatu · ile bot dorobił (bez Twoich wpłat)<Info term="zysk_automatu" /></div>
        <div className={`gd-hero-val ${pnlUp ? "gd-up" : "gd-down"}`}>
          {acc ? `${pnlUp ? "+" : ""}${money(status.trading_pnl.total_usd)}` : "…"}
        </div>
        <div className="gd-hero-sub">
          Konto <b>{acc ? money(total) : "…"}</b> · {invPct}% w grze ·
          <span className={`gd-hero-eng ${usLive ? "on" : "off"}`}>
            <span className="gd-dot pulse" />silnik {status.is_halted ? "HALT" : status.is_paused ? "STOP" : "gra"}
          </span>
        </div>
      </div>

      {/* KASA — trzy proste liczby: gdzie są pieniądze */}
      <div className="gd-sec"><h3>Twoja kasa</h3><span className="gd-sec-note">gdzie są pieniądze</span></div>
      <div className="gd-statgrid gd-statgrid-3">
        <StatCard label="Na koncie" value={acc ? money0(acc.total_value) : "…"} sub="wszystkie środki razem" />
        <StatCard label="W akcjach" value={money0(invested)} sub={`${sesjaCount} ${sesjaCount === 1 ? "pozycja" : "pozycji"} · ${invPct}% konta`} />
        <StatCard label="Wolna gotówka" value={money0(cash)} sub="czeka na wejścia" />
      </div>

      {/* RYZYKO — pełny widok: wskaźnik „jak ryzykownie jest teraz" (ukryty w trybie prostym) */}
      {!simple && (
        <>
          <div className="gd-sec"><h3>Ryzyko teraz<Info term="ryzyko" /></h3><span className="gd-sec-note">jak ostrożnie gra automat</span></div>
          <RiskScale status={status} />
        </>
      )}

      {/* ZYSK — po ludzku: skuteczność (pasek) + (pełny) wzięty vs na otwartych */}
      <div className="gd-sec"><h3>Zysk bota<Info term="skutecznosc" /></h3><span className="gd-sec-note">czysty wynik handlu</span></div>
      <WinBar pct={sc?.win_rate_pct ?? null} wins={sc?.wins ?? 0} losses={sc?.losses ?? 0} />
      {!simple && (
        <div className="gd-statgrid" style={{ marginTop: 10 }}>
          <StatCard label="Już wzięty" value={`${status.trading_pnl.realized_usd >= 0 ? "+" : ""}${money(status.trading_pnl.realized_usd)}`}
            tone={status.trading_pnl.realized_usd >= 0 ? "up" : "down"} sub="ze sprzedanych — masz na koncie" />
          <StatCard label="Na otwartych" value={`${status.trading_pnl.unrealized_usd >= 0 ? "+" : ""}${money(status.trading_pnl.unrealized_usd)}`}
            tone={status.trading_pnl.unrealized_usd >= 0 ? "up" : "down"} sub="jeszcze trzymane" />
        </div>
      )}

      {/* WYKRES — jeden, najważniejszy: zysk w czasie (odporny na wpłaty) */}
      <div className="gd-bandgrp">
        <div className="gd-band-h">Zysk automatu w czasie <small>bez Twoich wpłat — czysty wynik handlu</small></div>
        <div className="gd-band"><PnlBand series={alpaca?.pnl_history ?? []} /></div>
      </div>

      <NowStrip status={status} />

      <button className="gd-gopos" onClick={onGoPositions}>
        <span className="gd-gopos-l"><b>{sesjaCount}</b> {sesjaCount === 1 ? "pozycja" : "pozycji"} · {money(invested)} w grze</span>
        <span className="gd-gopos-r">Pozycje i „kiedy sprzedam" →</span>
      </button>
    </div>
  );
}
