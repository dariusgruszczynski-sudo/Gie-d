import { useEffect, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade } from "../api/client";
import { DecRow, extract, PosRow, RegimeChip } from "./Console";
import { ago, EquityBand, money, money0 } from "./kit";

export function Engines({ status, alpaca, extended, trades, extendedTrades, decisions, venue, setVenue, onChanged }: {
  status: StatusResponse;
  alpaca: PortfolioResponse | null;
  extended: PortfolioResponse | null;
  trades: Trade[];
  extendedTrades: Trade[];
  decisions: Decision[];
  venue: "alpaca" | "extended";
  setVenue: (v: "alpaca" | "extended") => void;
  onChanged: () => void;
}) {
  const isExt = venue === "extended";
  const leg = isExt ? "poza" : "sesja";
  const portfolio = isExt ? extended : alpaca;
  const legTrades = isExt ? extendedTrades : trades;
  const regime = isExt ? status.extended_market_regime : status.market_regime;
  const value = isExt ? status.account?.extended_positions_value ?? 0 : status.account?.equity_positions_value ?? 0;
  const live = isExt ? status.extended_enabled && !status.extended_paused : !status.is_halted && !status.is_paused;
  const prof = isExt ? status.profiles.extended : status.profiles.alpaca;
  const positions = extract(portfolio, leg);
  const legDecisions = decisions.filter((d) => (d.venue ?? "alpaca") === venue);

  const [notes, setNotes] = useState<Record<string, string>>({});
  useEffect(() => {
    let dead = false;
    (async () => {
      try { const r = await api.positionPlans(venue); const m: Record<string, string> = {}; r.positions.forEach((pp) => (m[pp.asset] = pp.note)); if (!dead) setNotes(m); }
      catch { if (!dead) setNotes({}); }
    })();
    return () => { dead = true; };
  }, [venue, positions.length]);

  if (isExt && !status.extended_enabled) {
    return (
      <div className="gd-view">
        <LegToggle venue={venue} setVenue={setVenue} />
        <p className="gd-empty">Silnik POZA SESJĄ jest wyłączony. Włącz EXTENDED_ENABLED i zasil konto, żeby handlować pre/after-market.</p>
      </div>
    );
  }

  return (
    <div className="gd-view">
      <LegToggle venue={venue} setVenue={setVenue} extendedEnabled={status.extended_enabled} />
      <div className={`gd-lane gd-lane-${leg}`} style={{ cursor: "default", marginBottom: 4 }}>
        <div className="gd-lane-head">
          <span className="gd-lane-name">{isExt ? "POZA SESJĄ · pre & after-market" : "SESJA · sesja dzienna"}</span>
          <span className={`gd-chip ${live ? "gd-chip-on" : "gd-chip-off"}`}><span className="gd-dot pulse" />{live ? "handluje" : "stop"}</span>
        </div>
        <div className="gd-lane-val">{money0(value)}</div>
        <div className="gd-lane-meta"><span>{positions.length} pozycji</span><RegimeChip r={regime} /></div>
      </div>

      <div className={`gd-brain gd-brain-${leg}`}>
        <div className="gd-brain-head">
          <span className="gd-brain-dot" />
          {isExt
            ? "Mózg POZA SESJĄ — osobny, agresywny profil na pre/after-market: tanie ETF, całe akcje, zlecenia LIMIT."
            : "Mózg SESJA — pełny swing sesji dziennej: akcje US, ułamki, zlecenia MARKET."}
        </div>
        <div className="gd-brain-knobs">
          <span className="gd-knob"><i>Ryzyko / transakcję</i><b>{prof.risk_per_trade_pct}%</b></span>
          <span className="gd-knob"><i>Min. pewność wejścia</i><b>{Math.round(prof.min_buy_confidence * 100)}%</b></span>
          <span className="gd-knob"><i>Max pozycja</i><b>{prof.max_position_pct}%</b></span>
          <span className="gd-knob"><i>Stop-loss</i><b>{prof.stop_loss_min_pct}–{prof.stop_loss_max_pct}%</b></span>
          <span className="gd-knob"><i>Wyzwalacz ruchu</i><b>{prof.price_move_trigger_pct}%</b></span>
          <span className="gd-knob"><i>R:R</i><b>{prof.reward_risk_ratio}:1</b></span>
          <span className="gd-knob"><i>Alokacja nogi</i><b>{prof.allocation_pct}%</b></span>
          <span className="gd-knob"><i>Podgląd</i><b>{prof.poll_interval_minutes}m · {prof.signal_timeframe}</b></span>
        </div>
      </div>

      <div className="gd-band"><EquityBand history={portfolio?.history ?? []} /></div>

      <div className="gd-sec"><h3>Pozycje</h3></div>
      {positions.length ? (
        <div className="gd-pos">{positions.map((p) => <PosRow key={p.asset} p={p} note={notes[p.asset]} onChanged={onChanged} />)}</div>
      ) : <p className="gd-empty">Brak pozycji na tej nodze.</p>}

      <div className="gd-sec"><h3>Ostatnie transakcje</h3></div>
      {legTrades.length ? (
        <div className="gd-pos">
          {legTrades.slice(0, 12).map((t) => (
            <div className="gd-pos-row" key={t.id} style={{ gridTemplateColumns: "auto 1fr auto" }}>
              <span className={`gd-chip ${t.side.toUpperCase() === "SELL" ? "gd-chip-off" : "gd-chip-on"}`}>{t.side.toUpperCase() === "SELL" ? "SPRZEDAŻ" : "KUPNO"}</span>
              <div className="gd-pos-tk"><b>{t.symbol}</b><span className="gd-pos-plan">{t.quantity.toLocaleString("pl-PL", { maximumFractionDigits: 4 })} @ {money(t.price)}</span></div>
              <span className="gd-dec-time">{ago(t.timestamp)}</span>
            </div>
          ))}
        </div>
      ) : <p className="gd-empty">Brak transakcji na tej nodze.</p>}

      <div className="gd-sec"><h3>Decyzje Claude — {isExt ? "POZA SESJĄ" : "SESJA"}</h3></div>
      {legDecisions.length ? (
        <div className="gd-stream">{legDecisions.slice(0, 15).map((d) => <DecRow key={d.id} d={d} />)}</div>
      ) : <p className="gd-empty">Brak decyzji na tej nodze.</p>}
    </div>
  );
}

function LegToggle({ venue, setVenue, extendedEnabled }: { venue: "alpaca" | "extended"; setVenue: (v: "alpaca" | "extended") => void; extendedEnabled?: boolean }) {
  // Jeden silnik: gdy POZA SESJĄ wyłączona, nie pokazujemy przełącznika nóg --
  // jest tylko silnik pozycyjny (sesja regularna).
  if (!extendedEnabled) {
    return (
      <div className="gd-topline">
        <span className="gd-kicker">Silnik pozycyjny · Akcje US</span>
      </div>
    );
  }
  return (
    <div className="gd-topline">
      <span className="gd-kicker">Silniki</span>
      <div className="gd-btnrow">
        <button className={`gd-btn ${venue === "alpaca" ? "primary" : ""}`} onClick={() => setVenue("alpaca")}>SESJA</button>
        <button className={`gd-btn ${venue === "extended" ? "primary" : ""}`} onClick={() => setVenue("extended")} style={venue === "extended" ? { background: "var(--amber)", color: "var(--ink)", borderColor: "transparent" } : undefined}>POZA SESJĄ</button>
      </div>
    </div>
  );
}
