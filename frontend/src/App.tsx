import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade, withShare } from "./api/client";
import { Console } from "./ui/Console";
import { Control } from "./ui/Control";
import { Health } from "./ui/Health";
import { History } from "./ui/History";
import { News } from "./ui/News";
import { Positions } from "./ui/Positions";
import { Week } from "./ui/Week";
import { HelpModal, Onboarding, useOnboarding } from "./ui/Help";
import { Icon } from "./ui/kit";
import { isSoundMuted, playTradeSound, setSoundMuted } from "./tradeSound";

const REFRESH_MS = 15000;
// Pięć ekranów: Pulpit (high-level + statystyka) · Pozycje (akcje + miarki
// „kiedy sprzedam") · Newsy · Puls (health) · Steruj (panel sterowania).
type View = "dashboard" | "positions" | "week" | "history" | "news" | "health" | "control";

const NAV: Array<{ key: View; label: string; icon: "console" | "positions" | "control" | "pulse" | "news" | "journal" | "engines" }> = [
  { key: "dashboard", label: "Pulpit", icon: "console" },
  { key: "positions", label: "Pozycje", icon: "positions" },
  { key: "week", label: "Tydzień", icon: "engines" },
  { key: "history", label: "Historia", icon: "journal" },
  { key: "news", label: "Newsy", icon: "news" },
  { key: "health", label: "Puls", icon: "pulse" },
  { key: "control", label: "Steruj", icon: "control" },
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
  // Tryb Prosty vs Zaawansowany — chowa nerdowe metryki dla spokojnego widoku.
  const [simple, setSimple] = useState<boolean>(() => { try { return localStorage.getItem("gd-simple") === "1"; } catch { return false; } });
  const [helpOpen, setHelpOpen] = useState(false);
  const [showOnboard, doneOnboard] = useOnboarding();
  const [view, setView] = useState<View>("dashboard");
  const [toasts, setToasts] = useState<Array<{ id: string; kind: "buy" | "sell" | "wait"; title: string; body: string }>>([]);
  const failCount = useRef(0);
  const seenTradeIds = useRef<Set<number> | null>(null);
  const seenDecisionIds = useRef<Set<number> | null>(null);
  const toastSeq = useRef(0);

  const pushToast = useCallback((kind: "buy" | "sell" | "wait", title: string, body: string) => {
    const id = `t${toastSeq.current++}`;
    // Keep at most 3 on screen; auto-dismiss after a few seconds.
    setToasts((cur) => [...cur, { id, kind, title, body }].slice(-3));
    setTimeout(() => setToasts((cur) => cur.filter((t) => t.id !== id)), 7000);
  }, []);
  const dismissToast = useCallback((id: string) => setToasts((cur) => cur.filter((t) => t.id !== id)), []);

  const refresh = useCallback(async () => {
    try {
      // Status NAJPIERW i osobno -- to on wypełnia dashboard głównymi liczbami.
      // Dzięki temu, gdy cięższe zapytania (portfolio/trades) są wolne albo
      // padną, "bebechy" i tak się pokazują, zamiast pustego panelu.
      const s = await api.status();
      setStatus(s); setError(null); setReconnecting(false);
      if (!s.extended_enabled) { setExtendedPortfolio(null); setExtendedTrades([]); }

      const [p, t, d] = await Promise.all([api.portfolio("alpaca"), api.trades("alpaca"), api.decisions()]);
      setPortfolio(p); setTrades(t); setDecisions(d);
      failCount.current = 0;

      if (s.extended_enabled) {
        const [cp, ct] = await Promise.all([api.portfolio("extended"), api.trades("extended")]);
        setExtendedPortfolio(cp); setExtendedTrades(ct);
      }

      // Popup + dźwięk przy ŚWIEŻEJ transakcji (kupno/sprzedaż). Pierwsze
      // odświeżenie tylko zapamiętuje stan (nie wyskakuje na cały backlog).
      if (seenTradeIds.current === null) {
        seenTradeIds.current = new Set(t.map((x) => x.id));
      } else {
        const fresh = t.filter((x) => !seenTradeIds.current!.has(x.id));
        fresh.forEach((x) => seenTradeIds.current!.add(x.id));
        if (fresh.length > 0) {
          const side = fresh[0].side.toUpperCase() === "SELL" ? "SELL" : "BUY";
          playTradeSound(side);
          navigator.vibrate?.(side === "SELL" ? [60] : [20, 40, 20]);
          const usd = (v: number) => `$${v.toLocaleString("pl-PL", { maximumFractionDigits: 2 })}`;
          fresh.slice(0, 3).forEach((x) => {
            const isSell = x.side.toUpperCase() === "SELL";
            const value = usd(x.usdt_value);
            if (isSell && x.pnl_usd !== undefined && x.pnl_usd !== null) {
              // Sprzedaż: pokaż CZY zarobił i za ile — kolor toastu wg wyniku.
              const win = x.pnl_usd >= 0;
              const sign = win ? "+" : "−";
              const pctTxt = x.pnl_pct !== undefined && x.pnl_pct !== null ? ` (${sign}${Math.abs(x.pnl_pct).toFixed(1)}%)` : "";
              pushToast(
                win ? "buy" : "sell",
                `${win ? "✅ Zysk" : "🔻 Strata"} ${sign}${usd(Math.abs(x.pnl_usd))} · ${x.symbol}`,
                `sprzedano za ${value}${pctTxt}`,
              );
            } else {
              pushToast(
                isSell ? "sell" : "buy",
                `${isSell ? "🔴 Sprzedano" : "🟢 Kupiono"} ${x.symbol}`,
                `${x.quantity.toLocaleString("pl-PL", { maximumFractionDigits: 4 })} @ ${usd(x.price)} · ${value}`,
              );
            }
          });
        }
      }

      // Popup "czeka" przy ŚWIEŻEJ decyzji HOLD (bot przeanalizował i świadomie
      // trzyma). Transakcje mają własny popup wyżej, więc tu tylko HOLD.
      if (seenDecisionIds.current === null) {
        seenDecisionIds.current = new Set(d.map((x) => x.id));
      } else {
        const freshHolds = d.filter((x) => !seenDecisionIds.current!.has(x.id) && x.action === "HOLD");
        d.forEach((x) => seenDecisionIds.current!.add(x.id));
        if (freshHolds.length > 0) {
          const h = freshHolds[0];
          const reason = (h.reasoning || "Brak wyraźnej przewagi w tym cyklu.").slice(0, 140);
          pushToast("wait", "⏳ Czekam", reason);
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

  const changeView = useCallback((v: View) => {
    setView(v);
    window.scrollTo({ top: 0, behavior: "smooth" });
    navigator.vibrate?.(8);
  }, []);

  const toggleMuted = useCallback(() => setMuted((m) => { const n = !m; setSoundMuted(n); return n; }), []);
  const toggleSimple = useCallback(() => setSimple((s) => { const n = !s; try { localStorage.setItem("gd-simple", n ? "1" : "0"); } catch { /* ignore */ } return n; }), []);

  return (
    <div className="gd">
      <div className="gd-bg" aria-hidden="true"><span /><span /><span /></div>

      {showOnboard && <Onboarding onDone={doneOnboard} />}
      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}

      {toasts.length > 0 && (
        <div className="gd-toasts" role="status" aria-live="polite">
          {toasts.map((t) => (
            <button key={t.id} className={`gd-toast gd-toast-${t.kind}`} onClick={() => dismissToast(t.id)}>
              <span className="gd-toast-title">{t.title}</span>
              <span className="gd-toast-body">{t.body}</span>
            </button>
          ))}
        </div>
      )}

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
          <button className="gd-nav" onClick={() => setHelpOpen(true)}>
            <Icon name="news" />
            <span className="gd-nav-label">Pomoc</span>
          </button>
          <button className="gd-nav" onClick={toggleSimple}>
            <Icon name="console" />
            <span className="gd-nav-label">{simple ? "Widok: prosty" : "Widok: pełny"}</span>
          </button>
          <button className="gd-nav" onClick={toggleMuted}>
            <Icon name="pulse" />
            <span className="gd-nav-label">{muted ? "Dźwięk: off" : "Dźwięk: on"}</span>
          </button>
          <div className="gd-rail-foot">
            {status ? (status.mode === "live" ? "LIVE · realne środki" : "PAPER") : "łączę…"}
            {status?.build_sha && (
              <span className="gd-build" title={status.build_time ? `zbudowano ${status.build_time} UTC` : "wersja kodu"}>
                wersja {status.build_sha}
              </span>
            )}
          </div>
        </nav>

        <main className="gd-main">
          {error && <div className="gd-halt">Błąd API: {error}</div>}
          {!error && reconnecting && <div className="gd-ribbon">Ponawiam połączenie…</div>}

          <div className="gd-swap" key={view}>
            {!status ? (
              <div className="gd-view"><p className="gd-empty">Łączę z automatem…</p></div>
            ) : view === "dashboard" ? (
              <Console status={status} alpaca={portfolio} extended={extendedPortfolio} simple={simple} onGoPositions={() => changeView("positions")} />
            ) : view === "positions" ? (
              <Positions status={status} alpaca={portfolio} extended={extendedPortfolio} decisions={decisions} onChanged={refresh} />
            ) : view === "week" ? (
              <Week status={status} />
            ) : view === "history" ? (
              <History status={status} />
            ) : view === "news" ? (
              <News />
            ) : view === "control" ? (
              <Control status={status} onChanged={refresh} />
            ) : (
              <Health status={status} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
