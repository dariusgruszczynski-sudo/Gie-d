import { useEffect, useState } from "react";
import { api, Decision, EngineProfile, isReadOnly, MarketRegime, PortfolioResponse, PositionPlan, StatusResponse } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";
import { ago, EquityBand, money, money0, pct, PnlBand, TickerTape } from "./kit";
import { NewsBar } from "./NewsBar";

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

/* Position as a JOURNEY: stop ── entry ── [current] ── target, with a status
   badge that reflects the exit strategy (ripe to take profit / locked by
   min-hold / near stop). Directly shows "there's a profit, take it". */
export function PositionCard({ p, plan, bypassPct, onChanged }: {
  p: Pos; plan?: PositionPlan; bypassPct: number; onChanged?: () => void;
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

  const ripe = bypassPct > 0 && gain >= bypassPct;
  const nearStop = stop !== null && cur <= stop * 1.015;
  const badge = nearStop ? { t: "⚠ blisko stopu", cls: "stop" }
    : ripe ? { t: "🟢 zysk do wzięcia", cls: "ripe" }
    : up ? { t: "↗ na plusie — trzymam", cls: "hold" }
    : { t: "trzymam — czekam na ruch", cls: "flat" };

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
    <div className={`gd-pcard${ripe ? " ripe" : ""}${nearStop ? " danger" : ""}`}>
      <div className="gd-pcard-top">
        <div className="gd-pcard-id">
          <b className="gd-pcard-sym">{p.asset}</b>
          {daysLabel && <span className="gd-pcard-days">{daysLabel}</span>}
          <span className={`gd-pcard-badge ${badge.cls}`}>{badge.t}</span>
        </div>
        <div className="gd-pcard-fig">
          <span className="gd-pcard-val">{money(p.value)}</span>
          <span className={`gd-pcard-pct ${up ? "gd-up" : "gd-down"}`}>{p.pnlPct !== null ? pct(p.pnlPct) : "—"}</span>
        </div>
      </div>

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
          {plan?.thesis && <button className="gd-pcard-why" onClick={() => setOpen((v) => !v)}>{open ? "ukryj ▲" : "po co? ▾"}</button>}
          {!isReadOnly && onChanged && <button className="gd-sell" disabled={busy} onClick={sell}>{busy ? "…" : "Sprzedaj"}</button>}
        </div>
      </div>
      {open && plan?.thesis && <div className="gd-pcard-thesis">„{plan.thesis}"</div>}
    </div>
  );
}

export function Console({ status, alpaca, extended, decisions, onLeg, onChanged }: {
  status: StatusResponse;
  alpaca: PortfolioResponse | null;
  extended: PortfolioResponse | null;
  decisions: Decision[];
  onLeg: (v: "us" | "extended") => void;
  onChanged: () => void;
}) {
  const acc = status.account;
  const total = useCountUp(acc?.total_value ?? 0);
  const cash = acc?.cash ?? 0;
  const sesjaVal = acc?.equity_positions_value ?? 0;
  const invested = sesjaVal + (acc?.extended_positions_value ?? 0);
  const invPct = acc && acc.total_value > 0 ? Math.round((invested / acc.total_value) * 100) : 0;

  const positions = [...extract(alpaca, "sesja"), ...extract(extended, "poza")].sort((a, b) => b.value - a.value);
  const sesjaCount = positions.length;

  const [plans, setPlans] = useState<Record<string, PositionPlan>>({});
  const hasA = !!alpaca?.current, hasE = !!extended?.current;
  useEffect(() => {
    let dead = false;
    (async () => {
      const map: Record<string, PositionPlan> = {};
      const legs: Array<[Leg, "alpaca" | "extended"]> = [];
      if (hasA) legs.push(["sesja", "alpaca"]);
      if (hasE) legs.push(["poza", "extended"]);
      await Promise.all(legs.map(async ([leg, venue]) => {
        try { const r = await api.positionPlans(venue); r.positions.forEach((pp) => (map[`${leg}:${pp.asset}`] = pp)); } catch { /* best effort */ }
      }));
      if (!dead) setPlans(map);
    })();
    return () => { dead = true; };
  }, [hasA, hasE, invested]);

  const usLive = !status.is_halted && !status.is_paused;

  const livePrices: Record<string, number> = {
    ...JSON.parse(alpaca?.current?.prices_json || "{}"),
    ...JSON.parse(extended?.current?.prices_json || "{}"),
  };

  return (
    <div className="gd-view">
      <TickerTape sesja={status.whitelist} poza={status.extended_enabled ? status.extended_whitelist : []} prices={livePrices} />
      <NewsBar />
      <div className="gd-topline">
        <span className="gd-kicker">Konsola · {new Date().toLocaleDateString("pl-PL", { weekday: "long", day: "numeric", month: "long" })}</span>
        <span className={`gd-mode ${status.mode === "live" ? "live" : ""}`}>
          <span className="gd-blip" />{status.mode === "live" ? "LIVE" : "PAPER"}
        </span>
      </div>

      {status.is_halted && status.halted_reason && <div className="gd-halt">⛔ {status.halted_reason}</div>}

      <div className="gd-hero">
        <div className="gd-hero-label">💰 Zysk automatu · ile bot dorobił (bez Twoich wpłat)</div>
        <div className={`gd-hero-val ${status.trading_pnl.total_usd >= 0 ? "gd-up" : "gd-down"}`}>
          {acc ? `${status.trading_pnl.total_usd >= 0 ? "+" : ""}${money(status.trading_pnl.total_usd)}` : "…"}
        </div>
        <div className="gd-hero-deltas">
          <span className="gd-delta">{acc ? money(total) : "…"}<small>wartość konta</small></span>
          <span className="gd-delta" style={{ color: "var(--dim)" }}>{money0(cash)}<small>gotówka</small></span>
          <span className="gd-delta" style={{ color: "var(--dim)" }}>{invPct}%<small>w grze</small></span>
        </div>
      </div>

      <div className="gd-stratrow">
        <ConvictionLadder held={sesjaCount} profile={status.profiles.alpaca} />
        <div className="gd-engine" onClick={() => onLeg("us")}>
          <div className="gd-engine-top">
            <span className="gd-engine-name">Silnik pozycyjny · Akcje US</span>
            <span className={`gd-chip ${usLive ? "gd-chip-on" : "gd-chip-off"}`}><span className="gd-dot pulse" />{status.is_halted ? "HALT" : status.is_paused ? "STOP" : "gra"}</span>
          </div>
          <div className="gd-engine-val">{money0(sesjaVal)}<small>{sesjaCount} {sesjaCount === 1 ? "pozycja" : "pozycji"} · {invPct}% w grze</small></div>
          <MarketWeather r={status.market_regime} />
        </div>
      </div>

      <div className="gd-pnl-head">Na co składa się Zysk automatu: <b>zrealizowany + otwarte (papierowy)</b></div>
      <div className="gd-pnl">
        <div className="gd-pnl-item">
          <span className="gd-pnl-l">Zrealizowany (zamknięte)</span>
          <span className={`gd-pnl-v ${status.trading_pnl.realized_usd >= 0 ? "gd-up" : "gd-down"}`}>
            {status.trading_pnl.realized_usd >= 0 ? "+" : ""}{money(status.trading_pnl.realized_usd)}
          </span>
        </div>
        <div className="gd-pnl-item">
          <span className="gd-pnl-l">Otwarte (papierowy)</span>
          <span className={`gd-pnl-v ${status.trading_pnl.unrealized_usd >= 0 ? "gd-up" : "gd-down"}`}>
            {status.trading_pnl.unrealized_usd >= 0 ? "+" : ""}{money(status.trading_pnl.unrealized_usd)}
          </span>
        </div>
        <div className="gd-pnl-item">
          <span className="gd-pnl-l">Bot vs samo trzymanie SPY</span>
          {status.alpha_vs_spy ? (
            <>
              <span className={`gd-pnl-v ${status.alpha_vs_spy.alpha_usd >= 0 ? "gd-up" : "gd-down"}`}>
                {status.alpha_vs_spy.alpha_usd >= 0 ? "+" : ""}{money(status.alpha_vs_spy.alpha_usd)}
                {status.alpha_vs_spy.alpha_pct !== null && <small> ({status.alpha_vs_spy.alpha_pct >= 0 ? "+" : ""}{status.alpha_vs_spy.alpha_pct.toFixed(1)}%)</small>}
              </span>
              <span className="gd-pnl-sub">
                {status.alpha_vs_spy.alpha_usd >= 0
                  ? "bot zarobił tyle WIĘCEJ, niż gdybyś to samo trzymał w SPY"
                  : "bot jest tyle W TYLE za zwykłym trzymaniem SPY"}
              </span>
            </>
          ) : (
            <>
              <span className="gd-pnl-v" style={{ color: "var(--dim)" }}>—</span>
              <span className="gd-pnl-sub">porównanie ruszy, gdy będzie cena SPY i punkt startowy</span>
            </>
          )}
        </div>
      </div>

      <div className="gd-bandgrp">
        <div className="gd-band-h">Zysk automatu w czasie <small>bez Twoich wpłat — czysty wynik handlu</small></div>
        <div className="gd-band"><PnlBand series={alpaca?.pnl_history ?? []} /></div>
      </div>
      <div className="gd-bandgrp">
        <div className="gd-band-h">Wartość konta w czasie <small>razem z wpłatami</small></div>
        <div className="gd-band"><EquityBand history={alpaca?.history ?? []} /></div>
      </div>

      <NowStrip status={status} />

      <div className="gd-sec"><h3>Otwarte pozycje</h3><span className="gd-sec-note">{money(invested)} w grze · 🟢 = zysk do wzięcia</span></div>
      {positions.length ? (
        <div className="gd-pcards">
          {positions.map((p) => (
            <PositionCard key={`${p.leg}:${p.asset}`} p={p} plan={plans[`${p.leg}:${p.asset}`]}
              bypassPct={status.profiles.alpaca.min_hold_profit_bypass_pct} onChanged={onChanged} />
          ))}
        </div>
      ) : <p className="gd-empty">Brak otwartych pozycji — gotówka czeka na najlepsze wejścia.</p>}

      <div className="gd-sec"><h3>Decyzje Claude</h3><span className="gd-sec-note">na żywo</span></div>
      {decisions.length ? (
        <div className="gd-stream">{decisions.slice(0, 12).map((d) => <DecRow key={d.id} d={d} />)}</div>
      ) : <p className="gd-empty">Jeszcze brak decyzji w tym oknie.</p>}
    </div>
  );
}
