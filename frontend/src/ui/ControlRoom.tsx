import { useEffect, useMemo, useState } from "react";
import {
  api, Decision, HistoryResponse, HistoryTrade, KnowledgeResponse,
  PortfolioResponse, PositionPlan, StatusResponse,
} from "../api/client";
import { ago, money, money0, pct, PnlBand } from "./kit";
import { DecRow, extract, Leg, PositionCard } from "./Console";

/* =============================================================================
   CONTROL ROOM — ekrany nowego interfejsu nadzoru bota krypto (paper).
   Trzy zasady: KONTROLA · WIDOCZNOŚĆ · TRANSPARENTNOŚĆ.
   - StatusBar: stan systemu zawsze na wierzchu + szybka pauza.
   - Cockpit: „czy wszystko gra?" w 3 sekundy.
   - Flow: pozycje (teza/stop/cel) scalone z feedem decyzji „dlaczego".
   - Verdict: jedna uczciwa ocena — bot vs trzymanie BTC, z licznikiem próbki.
   - Brain: pamięć bota (playbook/lekcje) + puls rynku, który bot widzi.
   ============================================================================= */

export type CrView = "kokpit" | "flow" | "verdict" | "brain";
type PrimaryVenue = "alpaca" | "crypto";

function primaryVenueOf(status: StatusResponse): PrimaryVenue {
  return status.crypto_enabled ? "crypto" : "alpaca";
}
function pausedOf(status: StatusResponse): boolean {
  return status.crypto_enabled ? !!status.crypto_paused : status.is_paused;
}
function investedOf(status: StatusResponse): number {
  const a = status.account;
  return a ? (a.equity_positions_value ?? 0) + (a.extended_positions_value ?? 0) + (a.crypto_positions_value ?? 0) : 0;
}

/* ──────────────────────────── STATUS BAR ───────────────────────────────── */
export function StatusBar({ status, lastCycleIso, onChanged }: {
  status: StatusResponse; lastCycleIso: string | null; onChanged: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const venue = primaryVenueOf(status);
  const paused = pausedOf(status);
  const halted = !!status.is_halted;
  const acc = status.account;
  const invPct = acc && acc.total_value > 0 ? Math.round((investedOf(status) / acc.total_value) * 100) : 0;
  const stateCls = halted ? "halt" : paused ? "paused" : "live";
  const stateTxt = halted ? "HALT" : paused ? "PAUZA" : "ŻYJE";
  async function toggle() {
    setBusy(true);
    try { await (paused ? api.resume(venue) : api.pause(venue)); onChanged(); }
    finally { setBusy(false); }
  }
  const dayUp = (status.day_pnl_pct ?? 0) >= 0;
  const weekUp = (status.week_pnl_pct ?? 0) >= 0;
  const botUp = status.trading_pnl.total_usd >= 0;
  return (
    <div className="cr-top">
      <div className="cr-sys">
        <span className="cr-brand"><span className="cr-brand-dot" />GIEL<b>DAREK</b></span>
        <span className={`cr-state ${stateCls}`}><span className="dot" />{stateTxt}</span>
        <span className={`cr-who ${paused || halted ? "you" : ""}`}>steruje <b>{paused || halted ? "TY" : "BOT"}</b></span>
        {lastCycleIso && <span className="cr-cyc">ostatni skan <b>{ago(lastCycleIso)}</b></span>}
        <span className="cr-cyc">skan co <b>~{status.poll_interval_minutes}m</b></span>
        <span className="cr-sys-sp" />
        <span className={`cr-paper ${status.mode === "live" ? "live" : ""}`}>{status.mode === "live" ? "LIVE" : "PAPER"}</span>
        <button className={`cr-pausebtn ${paused || halted ? "resume" : ""}`} disabled={busy} onClick={toggle}>
          {busy ? "…" : halted ? "▶ Odblokuj" : paused ? "▶ Wznów" : "❚❚ Pauza"}
        </button>
      </div>
      <div className="cr-nums">
        <div className="cr-num"><span className="k">Konto</span><span className="v big">{acc ? money0(acc.total_value) : "…"}</span></div>
        <div className="cr-num"><span className="k">Dziś</span><span className={`v ${dayUp ? "up" : "down"}`}>{status.day_pnl_pct == null ? "—" : pct(status.day_pnl_pct)}</span></div>
        <div className="cr-num"><span className="k">Tydzień</span><span className={`v ${weekUp ? "up" : "down"}`}>{status.week_pnl_pct == null ? "—" : pct(status.week_pnl_pct)}</span></div>
        <div className="cr-num"><span className="k">Zysk bota</span><span className={`v ${botUp ? "up" : "down"}`}>{botUp ? "+" : "−"}{money0(Math.abs(status.trading_pnl.total_usd))}</span></div>
        <div className="cr-num"><span className="k">Ekspozycja</span><span className="v">{invPct}%</span></div>
        <div className="cr-num"><span className="k">Gotówka</span><span className="v">{acc ? money0(acc.cash) : "…"}</span></div>
      </div>
    </div>
  );
}

/* ─────────────── wspólne: zapas do auto-stopu (ryzyko „paliwo") ─────────── */
function riskFuel(status: StatusResponse) {
  const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
  const dayProx = status.daily_loss_limit_pct > 0 && status.day_pnl_pct != null
    ? clamp01(Math.max(0, -status.day_pnl_pct) / status.daily_loss_limit_pct) : 0;
  const weekProx = status.weekly_loss_limit_pct > 0 && status.week_pnl_pct != null
    ? clamp01(Math.max(0, -status.week_pnl_pct) / status.weekly_loss_limit_pct) : 0;
  const acc = status.account;
  const ddPct = acc && status.peak_account_value > 0 && acc.total_value > 0
    ? (status.peak_account_value - acc.total_value) / status.peak_account_value * 100 : 0;
  const ddProx = status.max_drawdown_halt_pct > 0 ? clamp01(ddPct / status.max_drawdown_halt_pct) : 0;
  const used = status.is_halted ? 1 : Math.max(dayProx, weekProx, ddProx);
  const which = ddProx >= dayProx && ddProx >= weekProx ? { name: "obsunięcia od szczytu", limit: status.max_drawdown_halt_pct }
    : dayProx >= weekProx ? { name: "dziennego limitu straty", limit: status.daily_loss_limit_pct }
    : { name: "tygodniowego limitu straty", limit: status.weekly_loss_limit_pct };
  const cls = used >= 0.66 ? "hi" : used >= 0.33 ? "mid" : "ok";
  return { used, which, cls, ddPct };
}

/* ──────────────────────────────── KOKPIT ───────────────────────────────── */
export function Cockpit({ status, portfolio, decisions, onGoFlow, onGoVerdict }: {
  status: StatusResponse; portfolio: PortfolioResponse | null; decisions: Decision[];
  onGoFlow: () => void; onGoVerdict: () => void;
}) {
  const acc = status.account;
  const total = acc?.total_value ?? 0;
  const invPct = acc && acc.total_value > 0 ? Math.round((investedOf(status) / acc.total_value) * 100) : 0;
  const totalUp = (acc?.total_value ?? 0) >= (portfolio?.inception?.total_value_usdt ?? acc?.total_value ?? 0);
  const fuel = riskFuel(status);
  const sc = portfolio?.scorecard ?? null;

  // „Co bot robi teraz" — najświeższa decyzja (często HOLD-heartbeat „czuwam").
  const latest = decisions[0] ?? null;
  const doingTxt = status.is_halted
    ? (status.halted_reason || "Bezpiecznik zatrzymał bota.")
    : (latest?.reasoning || "Czuwam — skanuję rynek, czekam na sygnał wejścia.");
  const doingIco = status.is_halted ? "⛔" : latest?.action === "BUY" ? "🟢" : latest?.action === "SELL" ? "🔴" : "👁";

  // Werdykt-skrót: bot vs trzymanie BTC (benchmark ze scorecard).
  const alphaPct = sc?.alpha_pct ?? null;
  const vShort = sc && sc.closed_trades >= 0
    ? (sc.closed_trades < 50
        ? `Za mało danych na werdykt — ${sc.closed_trades}/50 zamknięć`
        : alphaPct == null ? "Brak benchmarku do porównania"
        : `${alphaPct >= 0 ? "Bije" : "Przegrywa z"} trzymaniem ${sc.benchmark_symbol}: ${alphaPct >= 0 ? "+" : ""}${alphaPct.toFixed(1)}pp`)
    : "Zbieram wynik…";

  return (
    <div className="cr-screen">
      {status.is_halted && status.halted_reason && (
        <div className="cr-halt-banner">⛔ <b>Bezpiecznik zatrzymał bota.</b> {status.halted_reason} — otwórz STER i naciśnij „Odblokuj", żeby wznowić i wyzerować punkty odniesienia.</div>
      )}

      <div className="cr-hero">
        <span className="lbl">Wartość konta</span>
        <div className={`val ${totalUp ? "up" : "down"}`}>{acc ? money0(total) : "…"}</div>
        <div className="deltas">
          <span className="delta">dziś <b className={(status.day_pnl_pct ?? 0) >= 0 ? "up" : "down"}>{status.day_pnl_pct == null ? "—" : pct(status.day_pnl_pct)}</b> <small>(wycena)</small></span>
          <span className="delta">tydzień <b className={(status.week_pnl_pct ?? 0) >= 0 ? "up" : "down"}>{status.week_pnl_pct == null ? "—" : pct(status.week_pnl_pct)}</b></span>
          <span className="delta">zysk bota <b className={status.trading_pnl.total_usd >= 0 ? "up" : "down"}>{status.trading_pnl.total_usd >= 0 ? "+" : "−"}{money(Math.abs(status.trading_pnl.total_usd))}</b></span>
        </div>
      </div>

      <div className="cr-doing">
        <span className="ico">{doingIco}</span>
        <div className="txt">{doingTxt}<span className="when">{latest ? ago(latest.timestamp) : "na żywo"} · bot {pausedOf(status) ? "wstrzymany" : "pilnuje"}</span></div>
      </div>

      <div className="cr-grid c2">
        <div className="cr-panel">
          <div className="cr-ph"><h3>Zapas do auto-stopu</h3><span className="note">kiedy bot sam się wstrzyma</span></div>
          <div className="cr-fuel">
            <div className="cr-fuel-row">
              <span className="lbl">wykorzystane ryzyko <b>{Math.round(fuel.used * 100)}%</b> {fuel.which.name}</span>
            </div>
            <div className="cr-fuel-bar"><i className={fuel.cls} style={{ width: `${Math.max(3, Math.round(fuel.used * 100))}%` }} /></div>
            <div className="cr-fuel-note">
              Limity: dzień −{status.daily_loss_limit_pct}% · tydzień −{status.weekly_loss_limit_pct}% · obsunięcie −{status.max_drawdown_halt_pct}%.
              {status.is_halted ? " Automat ZATRZYMANY." : fuel.used < 0.33 ? " Daleko do stopów — spokojnie." : fuel.used < 0.66 ? " Jest zapas, ale bez luzu." : " Blisko bezpiecznika — ostrożnie."}
            </div>
          </div>
        </div>
        <div className="cr-grid c2">
          <div className="cr-metric"><span className="k">W grze</span><span className="v">{invPct}%</span><span className="s">{money0(investedOf(status))}</span></div>
          <div className="cr-metric"><span className="k">Gotówka</span><span className="v">{acc ? money0(acc.cash) : "…"}</span><span className="s">czeka na wejścia</span></div>
          <div className="cr-metric"><span className="k">Już wzięte</span><span className={`v ${status.trading_pnl.realized_usd >= 0 ? "up" : "down"}`}>{status.trading_pnl.realized_usd >= 0 ? "+" : "−"}{money0(Math.abs(status.trading_pnl.realized_usd))}</span><span className="s">zaksięgowane</span></div>
          <div className="cr-metric"><span className="k">Na otwartych</span><span className={`v ${status.trading_pnl.unrealized_usd >= 0 ? "up" : "down"}`}>{status.trading_pnl.unrealized_usd >= 0 ? "+" : "−"}{money0(Math.abs(status.trading_pnl.unrealized_usd))}</span><span className="s">wycena</span></div>
        </div>
      </div>

      <button className="cr-vshort" onClick={onGoVerdict}>
        <span className="l"><div className="t">Werdykt: aktywny handel vs trzymanie BTC</div><div className="s">{vShort}</div></span>
        <span className="r">pełny werdykt →</span>
      </button>

      <div className="cr-panel" style={{ marginTop: 12 }}>
        <div className="cr-ph"><h3>Ostatnie decyzje</h3><button className="cr-prop-mut" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--cr-accent)" }} onClick={onGoFlow}>wszystkie →</button></div>
        {decisions.length ? (
          <div className="gd-stream">{decisions.slice(0, 3).map((d) => <DecRow key={d.id} d={d} />)}</div>
        ) : <p className="cr-empty">Jeszcze brak decyzji w tym oknie.</p>}
      </div>
    </div>
  );
}

/* ─────────────────── POZYCJE & DECYZJE (Flow) ──────────────────────────── */
export function Flow({ status, alpaca, extended, decisions, onChanged }: {
  status: StatusResponse; alpaca: PortfolioResponse | null; extended: PortfolioResponse | null;
  decisions: Decision[]; onChanged: () => void;
}) {
  const primary = primaryVenueOf(status);
  const positions = [...extract(alpaca, "sesja", primary), ...extract(extended, "poza")].sort((a, b) => b.value - a.value);
  const invested = positions.reduce((s, p) => s + p.value, 0);
  const [plans, setPlans] = useState<Record<string, PositionPlan>>({});
  const [filter, setFilter] = useState<"all" | "acts">("all");
  const hasA = !!alpaca?.current, hasE = !!extended?.current;

  useEffect(() => {
    let dead = false;
    (async () => {
      const map: Record<string, PositionPlan> = {};
      const legs: Array<[Leg, "alpaca" | "extended" | "crypto"]> = [];
      if (hasA) legs.push(["sesja", primary]);
      if (hasE) legs.push(["poza", "extended"]);
      await Promise.all(legs.map(async ([leg, venue]) => {
        try { const r = await api.positionPlans(venue); r.positions.forEach((pp) => (map[`${leg}:${pp.asset}`] = pp)); } catch { /* best effort */ }
      }));
      if (!dead) setPlans(map);
    })();
    return () => { dead = true; };
  }, [hasA, hasE, invested, primary]);

  const states = positions.map((p) => plans[`${p.leg}:${p.asset}`]?.sell_plan?.state);
  const ripe = states.filter((s) => s === "profit_ready" || s === "sell_now").length;
  const climbing = states.filter((s) => s === "climbing").length;
  const nearStop = states.filter((s) => s === "near_stop").length;
  const bypassPct = status.profiles.alpaca.min_hold_profit_bypass_pct;
  const marketOpen = !!status.crypto_enabled || status.market_session === "regular";
  const shown = filter === "acts" ? decisions.filter((d) => d.action !== "HOLD") : decisions;

  return (
    <div className="cr-screen">
      <div className="cr-screen-head"><h2>Pozycje &amp; decyzje</h2><span className="sub">co trzymam i dlaczego — teza, stop, cel oraz każda decyzja silnika</span></div>

      <div className="cr-posbar">
        <div className="i"><b>{money0(invested)}</b><small>w grze</small></div>
        <div className="i"><b className="up">{ripe}</b><small>🟢 do wzięcia</small></div>
        <div className="i"><b>{climbing}</b><small>↗ rośnie</small></div>
        <div className="i"><b className={nearStop ? "down" : ""}>{nearStop}</b><small>⚠ blisko stopu</small></div>
        <div className="i"><b>{positions.length}</b><small>otwartych</small></div>
      </div>

      <div className="cr-flow">
        <div>
          <div className="cr-ph"><h3>Otwarte pozycje</h3><span className="note">teza · stop · cel · „kiedy sprzedam"</span></div>
          {positions.length ? (
            <div className="gd-pcards">
              {positions.map((p) => (
                <PositionCard key={`${p.leg}:${p.asset}`} p={p} plan={plans[`${p.leg}:${p.asset}`]}
                  bypassPct={bypassPct} marketOpen={marketOpen} onChanged={onChanged}
                  editable override={status.exit_overrides?.[p.asset]} />
              ))}
            </div>
          ) : <p className="cr-empty">Brak otwartych pozycji — gotówka czeka na najlepsze wejścia.</p>}
        </div>
        <div>
          <div className="cr-ph"><h3>Dziennik decyzji</h3><span className="note">sygnał → próg → akcja</span></div>
          <div className="cr-decfilter">
            <button className={filter === "all" ? "on" : ""} onClick={() => setFilter("all")}>Wszystko</button>
            <button className={filter === "acts" ? "on" : ""} onClick={() => setFilter("acts")}>Tylko akcje (kup/sprzedaj)</button>
          </div>
          {shown.length ? (
            <div className="gd-stream">{shown.slice(0, 24).map((d) => <DecRow key={d.id} d={d} />)}</div>
          ) : <p className="cr-empty">Brak decyzji pasujących do filtra.</p>}
        </div>
      </div>
    </div>
  );
}

/* ──────────────────────────────── WERDYKT ──────────────────────────────── */
export function Verdict({ status, portfolio }: { status: StatusResponse; portfolio: PortfolioResponse | null }) {
  const [hist, setHist] = useState<HistoryResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const primary = primaryVenueOf(status);

  useEffect(() => {
    let dead = false;
    (async () => { try { const r = await api.history(); if (!dead) setHist(r); } catch (e) { if (!dead) setErr(String(e)); } })();
    return () => { dead = true; };
  }, []);

  const sc = portfolio?.scorecard ?? null;
  const closed = (hist?.trades ?? []).filter((t) => (t.venue ?? "alpaca") === primary);
  const n = closed.length || (sc?.closed_trades ?? 0);
  const TARGET = 50;
  const sumP = (arr: HistoryTrade[]) => arr.reduce((s, t) => s + t.pnl_usd, 0);
  const wins = closed.filter((t) => t.pnl_usd >= 0);
  const losses = closed.filter((t) => t.pnl_usd < 0);
  const avgWin = wins.length ? sumP(wins) / wins.length : null;
  const avgLoss = losses.length ? sumP(losses) / losses.length : null;
  const expectancy = closed.length ? sumP(closed) / closed.length : null;
  const winRate = closed.length ? (wins.length / closed.length) * 100 : (sc?.win_rate_pct ?? null);
  const payoff = avgWin != null && avgLoss != null && avgLoss !== 0 ? avgWin / Math.abs(avgLoss) : null;
  const alphaPct = sc?.alpha_pct ?? null;

  // Werdykt GO / NO / WAIT — uczciwie wg próbki i alfy vs trzymanie BTC.
  let vcls = "wait", vbig = "Jeszcze nie wiadomo", vexpl = "";
  if (n < TARGET) {
    vcls = "wait"; vbig = "Jeszcze nie wiadomo";
    vexpl = `Za mało zamkniętych transakcji na werdykt — ${n} z ${TARGET}. Nie oceniamy strategii na małej próbce (ani nie stroimy pod nią). Zbieramy dalej.`;
  } else if (alphaPct == null) {
    vcls = "wait"; vbig = "Brak porównania";
    vexpl = "Próbka jest, ale brakuje benchmarku do porównania z trzymaniem BTC.";
  } else if (alphaPct >= 0 && (expectancy ?? 0) > 0) {
    vcls = "go"; vbig = "Bije trzymanie BTC";
    vexpl = `Na ${n} zamknięciach aktywny handel wyprzedza zwykłe trzymanie ${sc?.benchmark_symbol} o ${alphaPct.toFixed(1)}pp, przy dodatniej wartości oczekiwanej. Ma sens.`;
  } else {
    vcls = "no"; vbig = "Przegrywa z BTC";
    vexpl = `Na ${n} zamknięciach aktywny handel ${alphaPct < 0 ? `jest ${Math.abs(alphaPct).toFixed(1)}pp za trzymaniem ${sc?.benchmark_symbol}` : "nie ma dodatniej wartości oczekiwanej"}. Na paper to sygnał „nie włączać realnych środków".`;
  }

  return (
    <div className="cr-screen">
      <div className="cr-screen-head"><h2>Werdykt</h2><span className="sub">czy aktywny handel w ogóle bije zwykłe trzymanie BTC?</span></div>
      {err && <div className="cr-halt-banner">{err}</div>}

      <div className={`cr-verdict ${vcls}`}>
        <span className="eyebrow">ocena GO / NO-GO · paper money</span>
        <div className="big">{vbig}</div>
        <div className="expl">{vexpl}</div>
        <div className="cr-sample">
          <div className="cr-sample-row"><span>próbka do wiarygodnego werdyktu</span><b>{n} / {TARGET} zamknięć</b></div>
          <div className="cr-sample-bar"><i style={{ width: `${Math.min(100, Math.round((n / TARGET) * 100))}%` }} /></div>
        </div>
      </div>

      {sc && (
        <div className="cr-vs">
          <div className="side"><div className="k">Bot (konto)</div><div className="v">{money0(sc.portfolio_value)}</div><div className="s">aktywny handel</div></div>
          <div className="vsmid">vs</div>
          <div className="side"><div className="k">Trzymanie {sc.benchmark_symbol}</div><div className="v">{sc.benchmark_value != null ? money0(sc.benchmark_value) : "—"}</div><div className="s">kup i trzymaj</div></div>
        </div>
      )}

      <div className="cr-panel flush">
        <div style={{ padding: "12px 14px" }} className="cr-ph"><h3>Zysk bota w czasie</h3><span className="note">bez Twoich wpłat — czysty wynik handlu</span></div>
        <div className="cr-band" style={{ border: "none", borderRadius: 0 }}><PnlBand series={portfolio?.pnl_history ?? []} /></div>
      </div>

      <div className="cr-grid c4">
        <div className="cr-metric"><span className="k">Wartość oczekiwana</span><span className={`v ${(expectancy ?? 0) >= 0 ? "up" : "down"}`}>{expectancy == null ? "—" : `${expectancy >= 0 ? "+" : "−"}${money(Math.abs(expectancy))}`}</span><span className="s">na 1 transakcję</span></div>
        <div className="cr-metric"><span className="k">Skuteczność</span><span className="v">{winRate == null ? "—" : `${Math.round(winRate)}%`}</span><span className="s">{wins.length}/{closed.length || "—"} na plus</span></div>
        <div className="cr-metric"><span className="k">Payoff</span><span className="v">{payoff == null ? "—" : `${payoff.toFixed(1)}×`}</span><span className="s">wygrana vs strata</span></div>
        <div className="cr-metric"><span className="k">Alfa vs BTC</span><span className={`v ${(alphaPct ?? 0) >= 0 ? "up" : "down"}`}>{alphaPct == null ? "—" : `${alphaPct >= 0 ? "+" : ""}${alphaPct.toFixed(1)}pp`}</span><span className="s">nad trzymaniem</span></div>
      </div>

      {n > 0 && avgWin != null && avgLoss != null && (
        <div className="cr-panel">
          <div className="cr-ph"><h3>Asymetria</h3><span className="note">to robi wynik przy trendach</span></div>
          <div className="cr-vs" style={{ marginBottom: 0 }}>
            <div className="side"><div className="k">śr. wygrana</div><div className="v up">+{money(avgWin)}</div></div>
            <div className="vsmid">vs</div>
            <div className="side"><div className="k">śr. strata</div><div className="v down">−{money(Math.abs(avgLoss))}</div></div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ──────────────────────────────── MÓZG ─────────────────────────────────── */
interface CryptoStructure {
  btc_funding_rate_pct?: number;
  btc_open_interest_change_24h_pct?: number;
  btc_long_short_ratio?: number;
  fear_greed?: number;
  fear_greed_label?: string;
}
function latestStructure(decisions: Decision[]): CryptoStructure | null {
  for (const d of decisions) {
    if (!d.market_context_snapshot || d.market_context_snapshot === "{}") continue;
    try {
      const o = JSON.parse(d.market_context_snapshot) as CryptoStructure;
      if (o && (o.btc_funding_rate_pct != null || o.fear_greed != null || o.btc_long_short_ratio != null || o.btc_open_interest_change_24h_pct != null)) return o;
    } catch { /* ignore */ }
  }
  return null;
}

const DOMAIN_ICON: Record<string, string> = {
  "Ryzyko i rozmiar": "⚖️", "Reżim i trend": "📈", "Funding i pozycjonowanie": "🔁",
  "Mikrostruktura i egzekucja": "🩻", "Sentyment i narracja": "🎭", "Proces i meta": "🧭",
};
function groupByDomain(rules: string[]): Array<{ domain: string; items: string[] }> {
  const order: string[] = [];
  const by = new Map<string, string[]>();
  for (const raw of rules) {
    const idx = raw.indexOf(" · ");
    const domain = idx > 0 ? raw.slice(0, idx) : "Ogólne";
    const text = idx > 0 ? raw.slice(idx + 3) : raw;
    if (!by.has(domain)) { by.set(domain, []); order.push(domain); }
    by.get(domain)!.push(text);
  }
  return order.map((domain) => ({ domain, items: by.get(domain)! }));
}

export function Brain({ status, decisions }: { status: StatusResponse; decisions: Decision[] }) {
  const [k, setK] = useState<KnowledgeResponse | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => {
    let alive = true;
    api.knowledge().then((r) => alive && setK(r)).catch(() => alive && setErr(true));
    return () => { alive = false; };
  }, []);
  const groups = useMemo(() => (k ? groupByDomain(k.playbook) : []), [k]);
  const struct = useMemo(() => latestStructure(decisions), [decisions]);
  const regime = status.market_regime;
  const regimeChip = !regime ? { cls: "neu", t: "brak danych" }
    : regime.regime === "risk_on" ? { cls: "on", t: "sprzyja (risk-on)" }
    : regime.regime === "risk_off" ? { cls: "off", t: "ostrożnie (risk-off)" }
    : { cls: "neu", t: "neutralnie" };
  const fng = struct?.fear_greed;
  const fngCls = fng == null ? "" : fng >= 75 ? "warn" : fng <= 25 ? "up" : "";
  const funding = struct?.btc_funding_rate_pct;
  const fundingCls = funding == null ? "" : funding >= 0.08 ? "warn" : funding < 0 ? "up" : "";

  return (
    <div className="cr-screen">
      <div className="cr-screen-head"><h2>Mózg</h2><span className="sub">co bot wie i co widzi na rynku — pełna transparentność</span></div>

      <div className="cr-panel">
        <div className="cr-ph"><h3>Puls rynku — to samo, co widzi bot</h3><span className={`cr-chip ${regimeChip.cls}`}>reżim: {regimeChip.t}</span></div>
        <div className="cr-pulse-grid">
          <div className="cr-pulse"><span className="k">Fear &amp; Greed</span><span className={`v ${fngCls}`}>{fng == null ? "—" : fng}</span><span className="s">{struct?.fear_greed_label ?? "indeks nastrojów"}</span></div>
          <div className="cr-pulse"><span className="k">Funding BTC</span><span className={`v ${fundingCls}`}>{funding == null ? "—" : `${funding > 0 ? "+" : ""}${funding}%`}</span><span className="s">{funding == null ? "perp" : funding >= 0 ? "longi płacą (tłum long)" : "shorty płacą"}</span></div>
          <div className="cr-pulse"><span className="k">Open Interest 24h</span><span className={`v ${(struct?.btc_open_interest_change_24h_pct ?? 0) >= 0 ? "up" : "down"}`}>{struct?.btc_open_interest_change_24h_pct == null ? "—" : `${struct.btc_open_interest_change_24h_pct > 0 ? "+" : ""}${struct.btc_open_interest_change_24h_pct}%`}</span><span className="s">zmiana pozycji</span></div>
          <div className="cr-pulse"><span className="k">Long/Short</span><span className="v">{struct?.btc_long_short_ratio == null ? "—" : struct.btc_long_short_ratio}</span><span className="s">{struct?.btc_long_short_ratio == null ? "ratio" : struct.btc_long_short_ratio > 1 ? "więcej longów" : "więcej shortów"}</span></div>
        </div>
        {!struct && <p className="cr-fuel-note" style={{ marginTop: 10 }}>Struktura rynku krypto pojawi się przy najbliższym cyklu silnika (funding/OI/long-short/F&amp;G z rynku perpetualów).</p>}
      </div>

      <p className="cr-intro">
        Pamięć decyzyjna silnika: zasady destylowane z praktyki + twarde lekcje, pisane pod dane,
        które model realnie dostaje — cena i wskaźniki, <b>funding</b>, <b>open interest</b>, <b>long/short</b> i <b>Fear&amp;Greed</b>.
        Krypto gra teraz <b>mechanicznie (bez LLM)</b>, więc wiedza się <b>gromadzi</b> i czeka na włączenie Sonneta — który wystartuje <b>z tym wszystkim</b>, nie na zimno.
      </p>

      {err && <p className="cr-empty">Nie udało się pobrać wiedzy — odśwież.</p>}
      {!k && !err && <p className="cr-empty">Ładuję wiedzę…</p>}

      {k && (
        <>
          <div className="cr-panel">
            <div className="cr-ph"><h3>📘 Playbook</h3><span className="note">{k.playbook.length} zasad · {groups.length} domen · {k.llm_active ? "LLM to czyta" : "zbieram (LLM off)"}</span></div>
            {groups.map((g) => (
              <div key={g.domain} className="cr-domain">
                <div className="cr-dh"><span className="ico">{DOMAIN_ICON[g.domain] ?? "•"}</span><span className="nm">{g.domain}</span><span className="ct">{g.items.length}</span></div>
                <ul className="cr-rules">{g.items.map((r, i) => <li key={i}>{r}</li>)}</ul>
              </div>
            ))}
          </div>

          <div className="cr-panel">
            <div className="cr-ph"><h3>🧠 Lekcje z własnego handlu</h3><span className="note">{k.lessons.length}{k.lessons_updated ? ` · ${k.lessons_updated}` : ""}</span></div>
            {k.lessons.length > 0 ? (
              <ul className="cr-rules lessons">{k.lessons.map((l, i) => <li key={i}>{l}</li>)}</ul>
            ) : <p className="cr-empty">Bot dopiero zbiera własne lekcje — wróć za kilka dni handlu.</p>}
          </div>
        </>
      )}
    </div>
  );
}
