import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade, withShare } from "./api/client";
import { Console } from "./ui/Console";
import { Control } from "./ui/Control";
import { Engines } from "./ui/Engines";
import { Health } from "./ui/Health";
import { Icon } from "./ui/kit";
import { isSoundMuted, playTradeSound, setSoundMuted } from "./tradeSound";

const REFRESH_MS = 15000;
type View = "console" | "engines" | "control" | "health";

const NAV: Array<{ key: View; label: string; icon: "console" | "engines" | "control" | "pulse" }> = [
  { key: "console", label: "Konsola", icon: "console" },
  { key: "engines", label: "Silniki", icon: "engines" },
  { key: "control", label: "Steruj", icon: "control" },
  { key: "health", label: "Puls", icon: "pulse" },
];

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [extendedPortfolio, setExtendedPortfolio] = useState<PortfolioResponse | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [extendedTrades, setExtendedTrades] = useState<Trade[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [muted, setMuted] = useState<boolean>(isSoundMuted);
  const [view, setView] = useState<View>("console");
  const [engineVenue, setEngineVenue] = useState<"alpaca" | "extended">("alpaca");
  const failCount = useRef(0);
  const seenTradeIds = useRef<Set<number> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, p, t, d] = await Promise.all([api.status(), api.portfolio("alpaca"), api.trades("alpaca"), api.decisions()]);
      setStatus(s); setPortfolio(p); setTrades(t); setDecisions(d);
      failCount.current = 0; setError(null); setReconnecting(false);

      if (s.extended_enabled) {
        const [cp, ct] = await Promise.all([api.portfolio("extended"), api.trades("extended")]);
        setExtendedPortfolio(cp); setExtendedTrades(ct);
      } else { setExtendedPortfolio(null); setExtendedTrades([]); }

      if (seenTradeIds.current === null) {
        seenTradeIds.current = new Set(t.map((x) => x.id));
      } else {
        const fresh = t.filter((x) => !seenTradeIds.current!.has(x.id));
        fresh.forEach((x) => seenTradeIds.current!.add(x.id));
        if (fresh.length > 0) {
          const side = fresh[0].side.toUpperCase() === "SELL" ? "SELL" : "BUY";
          playTradeSound(side);
          navigator.vibrate?.(side === "SELL" ? [60] : [20, 40, 20]);
        }
      }
    } catch (e) {
      failCount.current += 1;
      if (failCount.current >= 3) { setError(String(e)); setReconnecting(false); }
      else setReconnecting(true);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    const es = new EventSource(withShare("/api/events"));
    es.onmessage = () => refresh();
    return () => es.close();
  }, [refresh]);

  const goLeg = useCallback((v: "us" | "extended") => {
    setEngineVenue(v === "us" ? "alpaca" : "extended");
    setView("engines");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const changeView = useCallback((v: View) => {
    setView(v);
    window.scrollTo({ top: 0, behavior: "smooth" });
    navigator.vibrate?.(8);
  }, []);

  const toggleMuted = useCallback(() => setMuted((m) => { const n = !m; setSoundMuted(n); return n; }), []);

  return (
    <div className="gd">
      <div className="gd-bg" aria-hidden="true"><span /><span /><span /></div>

      <div className="gd-shell">
        <nav className="gd-rail">
          <div className="gd-brand">
            <span className="gd-brand-mark" />
            <span className="gd-brand-name">GIEL<b>DAREK</b></span>
          </div>
          {NAV.map((n) => (
            <button key={n.key} className={`gd-nav ${view === n.key ? "on" : ""}`} onClick={() => changeView(n.key)}>
              <Icon name={n.icon} />
              <span className="gd-nav-label">{n.label}</span>
            </button>
          ))}
          <div className="gd-nav-sp" />
          <button className="gd-nav" onClick={toggleMuted}>
            <Icon name="pulse" />
            <span className="gd-nav-label">{muted ? "Dźwięk: off" : "Dźwięk: on"}</span>
          </button>
          <div className="gd-rail-foot">{status ? (status.mode === "live" ? "LIVE · realne środki" : "PAPER") : "łączę…"}</div>
        </nav>

        <main className="gd-main">
          {error && <div className="gd-halt">Błąd API: {error}</div>}
          {!error && reconnecting && <div className="gd-ribbon">Ponawiam połączenie…</div>}

          <div className="gd-swap" key={view === "engines" ? `engines:${engineVenue}` : view}>
            {!status ? (
              <div className="gd-view"><p className="gd-empty">Łączę z automatem…</p></div>
            ) : view === "console" ? (
              <Console status={status} alpaca={portfolio} extended={extendedPortfolio} decisions={decisions} onLeg={goLeg} onChanged={refresh} />
            ) : view === "engines" ? (
              <Engines status={status} alpaca={portfolio} extended={extendedPortfolio} trades={trades} extendedTrades={extendedTrades}
                decisions={decisions} venue={engineVenue} setVenue={setEngineVenue} onChanged={refresh} />
            ) : view === "control" ? (
              <Control status={status} onChanged={refresh} />
            ) : (
              <Health />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
