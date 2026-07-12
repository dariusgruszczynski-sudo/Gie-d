import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, isReadOnly, PortfolioResponse, StatusResponse, Trade, withShare } from "./api/client";
import { BrandLoader } from "./components/BrandLoader";
import { BrandLogo } from "./components/BrandLogo";
import { DecisionSplash } from "./components/DecisionSplash";
import { EmberBackground } from "./components/EmberBackground";
import { MarketTemperature } from "./components/MarketTemperature";
import { StrategyBar } from "./components/StrategyBar";
import { TabNav } from "./components/TabNav";
import { ControlPage } from "./pages/ControlPage";
import { EnginePage } from "./pages/EnginePage";
import { OverviewPage } from "./pages/OverviewPage";
import { PageData, TabKey } from "./pages/types";
import { isSoundMuted, playTradeSound, setSoundMuted } from "./tradeSound";

const REFRESH_MS = 15000;
const TAB_KEY = "gield.tab";

function readInitialTab(): TabKey {
  const fromHash = window.location.hash.replace("#", "");
  const valid: TabKey[] = ["overview", "us", "crypto", "control"];
  if (valid.includes(fromHash as TabKey)) return fromHash as TabKey;
  const stored = localStorage.getItem(TAB_KEY);
  return valid.includes(stored as TabKey) ? (stored as TabKey) : "overview";
}

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [cryptoPortfolio, setCryptoPortfolio] = useState<PortfolioResponse | null>(null);
  const [cryptoTrades, setCryptoTrades] = useState<Trade[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  const [splashDecision, setSplashDecision] = useState<Decision | null>(null);
  const [muted, setMuted] = useState<boolean>(isSoundMuted);
  const [tab, setTab] = useState<TabKey>(readInitialTab);
  const [shuttingDown, setShuttingDown] = useState(false);
  const seenDecisionIds = useRef<Set<number> | null>(null);
  const seenTradeIds = useRef<Set<number> | null>(null);
  // Tolerate transient blips (a RESTART, a dropped poll) -- only surface the
  // error banner after several consecutive failures, so a 2-5s restart window
  // doesn't flash a scary "502" that clears itself on the next poll.
  const failCount = useRef(0);

  const toggleMuted = useCallback(() => {
    setMuted((m) => {
      const next = !m;
      setSoundMuted(next);
      return next;
    });
  }, []);

  const changeTab = useCallback((t: TabKey) => {
    setTab(t);
    localStorage.setItem(TAB_KEY, t);
    window.location.hash = t;
    window.scrollTo({ top: 0, behavior: "smooth" });
    navigator.vibrate?.(8); // subtle haptic tick on phones
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [s, p, t, d] = await Promise.all([
        api.status(),
        api.portfolio("alpaca"),
        api.trades("alpaca"),
        api.decisions(),
      ]);
      setStatus(s);
      setPortfolio(p);
      setTrades(t);
      setDecisions(d);
      failCount.current = 0;
      setError(null);
      setReconnecting(false);

      // The 24-7 crypto portfolio is fetched only when the venue is enabled,
      // so a single-lot setup pays no extra requests.
      if (s.crypto_enabled) {
        const [cp, ct] = await Promise.all([api.portfolio("crypto"), api.trades("crypto")]);
        setCryptoPortfolio(cp);
        setCryptoTrades(ct);
      } else {
        setCryptoPortfolio(null);
        setCryptoTrades([]);
      }

      if (seenDecisionIds.current === null) {
        // First load -- just remember what already exists, don't splash for history.
        seenDecisionIds.current = new Set(d.map((x) => x.id));
      } else {
        const fresh = d.filter((x) => !seenDecisionIds.current!.has(x.id));
        fresh.forEach((x) => seenDecisionIds.current!.add(x.id));
        if (fresh.length > 0) setSplashDecision(fresh[0]);
      }

      // Sound fires ONLY on a real executed trade (an action), not on every
      // routine HOLD -- and plays even when the tab is in the background.
      if (seenTradeIds.current === null) {
        seenTradeIds.current = new Set(t.map((x) => x.id));
      } else {
        const freshTrades = t.filter((x) => !seenTradeIds.current!.has(x.id));
        freshTrades.forEach((x) => seenTradeIds.current!.add(x.id));
        if (freshTrades.length > 0) {
          const side = freshTrades[0].side.toUpperCase() === "SELL" ? "SELL" : "BUY";
          playTradeSound(side); // no-ops itself if muted
          // Haptic burst on a real trade -- BUY double-tap, SELL single long.
          navigator.vibrate?.(side === "SELL" ? [60] : [20, 40, 20]);
        }
      }
    } catch (e) {
      // Restart / momentary drop: first couple of failures are almost always a
      // brief window (the app bouncing), so show a soft "reconnecting" note and
      // only escalate to a hard error once it's clearly persistent.
      failCount.current += 1;
      if (failCount.current >= 3) {
        setError(String(e));
        setReconnecting(false);
      } else {
        setReconnecting(true);
      }
    }
  }, []);

  useEffect(() => {
    refresh();
    // 15s polling stays as the fallback; SSE below makes updates instant.
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    // Live push: backend emits a tick whenever a new decision/trade/snapshot
    // lands or the pause/halt state flips -- refresh immediately instead of
    // waiting out the polling interval. Browser auto-reconnects on errors.
    const es = new EventSource(withShare("/api/events"));
    es.onmessage = () => refresh();
    return () => es.close();
  }, [refresh]);

  const data: PageData | null = status
    ? {
        status,
        portfolio,
        cryptoPortfolio,
        trades,
        cryptoTrades,
        decisions,
        refresh,
        muted,
        toggleMuted,
        shutdown: () => setShuttingDown(true),
      }
    : null;

  if (shuttingDown) {
    // Same splash as the post-login boot animation, but its onComplete does a
    // REAL page reload (fetches the current bundle) instead of an in-memory
    // state flip -- so a later deploy is picked up immediately, not just on
    // next natural refresh.
    return <BrandLoader onComplete={() => window.location.reload()} />;
  }

  return (
    <>
      {splashDecision && <DecisionSplash decision={splashDecision} onDismiss={() => setSplashDecision(null)} />}
      <EmberBackground />

      <div className="app">
        {isReadOnly && (
          <div className="readonly-ribbon">
            <span className="readonly-dot" /> Widok tylko do odczytu — podgląd na żywo, bez sterowania.
          </div>
        )}
        <div className="app-header">
          <BrandLogo size={48} />
          <div>
            <h1>
              Giel<span className="brand-accent">Darek</span>
            </h1>
            <p className="subtitle">
              Dwa mózgi Claude (Sonnet→Opus): akcje USA średnio agresywnie · krypto 24/7 agresywnie · wykonanie Alpaca ·
              narzędzie prywatne, nie jest to porada inwestycyjna.
            </p>
            {status && <MarketTemperature us={status.market_regime} crypto={status.crypto_market_regime} />}
          </div>
        </div>

        {status && <TabNav active={tab} onChange={changeTab} cryptoEnabled={status.crypto_enabled} />}

        {data && <StrategyBar status={data.status} />}

        {error ? (
          <p className="error-text">Błąd komunikacji z API: {error}</p>
        ) : (
          reconnecting && <p className="reconnecting-note">Ponawiam połączenie… (aplikacja może właśnie się restartować)</p>
        )}

        {!status && <StatusPlaceholder />}

        {data && (
          // key={tab} re-mounts on switch so the entrance animation replays --
          // gives each tab a smooth slide/fade in, native-app feel.
          <div className="tab-page" key={tab}>
            {tab === "overview" && <OverviewPage data={data} />}
            {tab === "us" && <EnginePage data={data} venue="alpaca" />}
            {tab === "crypto" && <EnginePage data={data} venue="crypto" />}
            {tab === "control" && <ControlPage data={data} />}
          </div>
        )}
      </div>
    </>
  );
}

function StatusPlaceholder() {
  return (
    <div className="panel" style={{ marginTop: 16 }}>
      <p className="subtitle" style={{ margin: 0 }}>
        Łączenie z automatem — oczekiwanie na dane…
      </p>
    </div>
  );
}
