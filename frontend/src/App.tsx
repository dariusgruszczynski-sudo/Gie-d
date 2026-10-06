import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, isReadOnly, PortfolioResponse, StatusResponse, withShare } from "./api/client";
import { Brain, Cockpit, CrView, Flow, StatusBar, Verdict } from "./ui/ControlRoom";
import { SterDrawer } from "./ui/Ster";
import { extract } from "./ui/Console";
import { isSoundMuted, playTradeSound, setSoundMuted } from "./tradeSound";

const REFRESH_MS = 15000;

/* CONTROL ROOM — nowy interfejs nadzoru bota krypto (paper). Zasady:
   KONTROLA (STER zewsząd) · WIDOCZNOŚĆ (stały status bar) · TRANSPARENTNOŚĆ
   (pozycja = teza/stop/cel, decyzja = powód, werdykt = uczciwa ocena vs BTC). */

const NAV: Array<{ key: CrView; label: string }> = [
  { key: "kokpit", label: "Kokpit" },
  { key: "flow", label: "Pozycje & decyzje" },
  { key: "verdict", label: "Werdykt" },
  { key: "brain", label: "Mózg" },
];

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [extendedPortfolio, setExtendedPortfolio] = useState<PortfolioResponse | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [muted, setMuted] = useState<boolean>(isSoundMuted);
  const [view, setView] = useState<CrView>("kokpit");
  const [sterOpen, setSterOpen] = useState(false);
  const [toasts, setToasts] = useState<Array<{ id: string; kind: "buy" | "sell" | "wait"; title: string; body: string }>>([]);
  const failCount = useRef(0);
  const seenTradeIds = useRef<Set<number> | null>(null);
  const seenDecisionIds = useRef<Set<number> | null>(null);
  const toastSeq = useRef(0);

  const pushToast = useCallback((kind: "buy" | "sell" | "wait", title: string, body: string) => {
    const id = `t${toastSeq.current++}`;
    setToasts((cur) => [...cur, { id, kind, title, body }].slice(-3));
    setTimeout(() => setToasts((cur) => cur.filter((t) => t.id !== id)), 7000);
  }, []);
  const dismissToast = useCallback((id: string) => setToasts((cur) => cur.filter((t) => t.id !== id)), []);

  const refresh = useCallback(async () => {
    try {
      const s = await api.status();
      setStatus(s); setError(null); setReconnecting(false);
      if (!s.extended_enabled) { setExtendedPortfolio(null); }

      const primary = s.crypto_enabled ? "crypto" : "alpaca";
      const [p, t, d] = await Promise.all([api.portfolio(primary), api.trades(primary), api.decisions(s.crypto_enabled ? "crypto" : undefined)]);
      setPortfolio(p); setDecisions(d);
      failCount.current = 0;

      if (s.extended_enabled) {
        try { setExtendedPortfolio(await api.portfolio("extended")); } catch { /* best effort */ }
      }

      // Popup + dźwięk przy świeżej transakcji; pierwsze odświeżenie tylko zapamiętuje.
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
              const win = x.pnl_usd >= 0;
              const sign = win ? "+" : "−";
              const pctTxt = x.pnl_pct !== undefined && x.pnl_pct !== null ? ` (${sign}${Math.abs(x.pnl_pct).toFixed(1)}%)` : "";
              pushToast(win ? "buy" : "sell", `${win ? "✅ Zysk" : "🔻 Strata"} ${sign}${usd(Math.abs(x.pnl_usd))} · ${x.symbol}`, `sprzedano za ${value}${pctTxt}`);
            } else {
              pushToast(isSell ? "sell" : "buy", `${isSell ? "🔴 Sprzedano" : "🟢 Kupiono"} ${x.symbol}`, `${x.quantity.toLocaleString("pl-PL", { maximumFractionDigits: 4 })} @ ${usd(x.price)} · ${value}`);
            }
          });
        }
      }

      if (seenDecisionIds.current === null) {
        seenDecisionIds.current = new Set(d.map((x) => x.id));
      } else {
        const freshHolds = d.filter((x) => !seenDecisionIds.current!.has(x.id) && x.action === "HOLD");
        d.forEach((x) => seenDecisionIds.current!.add(x.id));
        if (freshHolds.length > 0) {
          const reason = (freshHolds[0].reasoning || "Brak wyraźnej przewagi w tym cyklu.").slice(0, 140);
          pushToast("wait", "⏳ Czekam", reason);
        }
      }
    } catch (e) {
      failCount.current += 1;
      const msg = e instanceof Error ? e.message : String(e);
      if (failCount.current >= 3) { setError(msg); setReconnecting(false); }
      else setReconnecting(true);
    }
  }, [pushToast]);

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

  const changeView = useCallback((v: CrView) => {
    setView(v);
    window.scrollTo({ top: 0, behavior: "smooth" });
    navigator.vibrate?.(8);
  }, []);
  const toggleMuted = useCallback(() => setMuted((m) => { const n = !m; setSoundMuted(n); return n; }), []);

  const lastCycleIso = decisions[0]?.timestamp ?? null;
  // Licznik pozycji na zakładce „Pozycje & decyzje".
  const posCount = status
    ? [...extract(portfolio, "sesja", status.crypto_enabled ? "crypto" : "alpaca"), ...extract(extendedPortfolio, "poza")].length
    : 0;
  const paused = status ? (status.crypto_enabled ? !!status.crypto_paused : status.is_paused) : false;
  const halted = !!status?.is_halted;

  return (
    <div className="gd cr">
      <div className="cr-root">
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

        {!status ? (
          <div className="cr-screen"><p className="cr-empty">Łączę z automatem…</p></div>
        ) : (
          <>
            <header className="cr-header">
              <StatusBar status={status} lastCycleIso={lastCycleIso} onChanged={refresh} />
              <nav className="cr-nav">
                {NAV.map((n) => (
                  <button key={n.key} className={`cr-tab ${view === n.key ? "on" : ""}`} onClick={() => changeView(n.key)}>
                    {n.label}
                    {n.key === "flow" && posCount > 0 && <span className="badge up">{posCount}</span>}
                  </button>
                ))}
                <span style={{ flex: 1 }} />
                <button className="cr-tab" onClick={toggleMuted} title={muted ? "Dźwięk wyłączony" : "Dźwięk włączony"}>{muted ? "🔇" : "🔊"}</button>
              </nav>
            </header>

            {error && <div className="cr-screen" style={{ paddingBottom: 0 }}><div className="cr-halt-banner">Błąd API: {error}</div></div>}
            {!error && reconnecting && <div className="cr-screen" style={{ paddingBottom: 0 }}><div className="cr-doing" style={{ borderLeftColor: "var(--cr-warn)" }}><span className="ico">⟳</span><div className="txt">Ponawiam połączenie…</div></div></div>}

            <div key={view}>
              {view === "kokpit" ? (
                <Cockpit status={status} portfolio={portfolio} decisions={decisions} onGoFlow={() => changeView("flow")} onGoVerdict={() => changeView("verdict")} />
              ) : view === "flow" ? (
                <Flow status={status} alpaca={portfolio} extended={extendedPortfolio} decisions={decisions} onChanged={refresh} />
              ) : view === "verdict" ? (
                <Verdict status={status} portfolio={portfolio} />
              ) : (
                <Brain status={status} decisions={decisions} />
              )}
            </div>

            {!isReadOnly && (
              <button className={`cr-fab ${halted ? "halt" : paused ? "paused" : ""}`} onClick={() => setSterOpen(true)}>
                <span className="fab-ico">⛭</span>STER
              </button>
            )}
            {sterOpen && !isReadOnly && <SterDrawer status={status} onChanged={refresh} onClose={() => setSterOpen(false)} />}
          </>
        )}
      </div>
    </div>
  );
}
