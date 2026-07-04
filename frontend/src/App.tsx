import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade } from "./api/client";
import { ControlToolbar } from "./components/ControlToolbar";
import { DecisionSplash } from "./components/DecisionSplash";
import { DecisionsLog } from "./components/DecisionsLog";
import { EmberBackground } from "./components/EmberBackground";
import { ManualTradePanel } from "./components/ManualTradePanel";
import { MarketLog } from "./components/MarketLog";
import { PortfolioChart } from "./components/PortfolioChart";
import { PriceTicker } from "./components/PriceTicker";
import { StatusBanner } from "./components/StatusBanner";
import { TradesTable } from "./components/TradesTable";

function Logo() {
  return (
    <svg width="40" height="40" viewBox="0 0 40 40" className="logo-mark" aria-hidden="true">
      <circle cx="20" cy="20" r="19" fill="url(#logoGradient)" stroke="var(--gold)" strokeWidth="1" />
      <defs>
        <linearGradient id="logoGradient" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#1a1608" />
          <stop offset="100%" stopColor="#0a0a0a" />
        </linearGradient>
      </defs>
      <path d="M12 24 L16 16 L20 20 L24 11 L28 15" stroke="var(--gold-bright)" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 11 L28 11 L28 15" stroke="var(--gold-bright)" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const REFRESH_MS = 15000;

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [splashDecision, setSplashDecision] = useState<Decision | null>(null);
  const seenDecisionIds = useRef<Set<number> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, p, t, d] = await Promise.all([
        api.status(),
        api.portfolio(),
        api.trades(),
        api.decisions(),
      ]);
      setStatus(s);
      setPortfolio(p);
      setTrades(t);
      setDecisions(d);
      setError(null);

      if (seenDecisionIds.current === null) {
        // First load -- just remember what already exists, don't splash for history.
        seenDecisionIds.current = new Set(d.map((x) => x.id));
      } else {
        const fresh = d.filter((x) => !seenDecisionIds.current!.has(x.id));
        fresh.forEach((x) => seenDecisionIds.current!.add(x.id));
        if (fresh.length > 0) setSplashDecision(fresh[0]);
      }
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <>
      {splashDecision && <DecisionSplash decision={splashDecision} onDismiss={() => setSplashDecision(null)} />}
      <EmberBackground />
      <PriceTicker history={portfolio?.history ?? []} whitelist={status?.whitelist ?? []} />
      <div className="app">
        <div className="brand-banner">
          <p className="slogan">Kto gra grubo, wygrać musi</p>
        </div>

        <div className="app-header">
          <Logo />
          <div>
            <h1>Gie-d — automatyczny bot inwestycyjny</h1>
            <p className="subtitle">
              Decyzje: Claude Opus · Wykonanie: Binance · To narzędzie prywatne, nie jest to porada inwestycyjna.
            </p>
          </div>
        </div>

        {error && <p className="error-text">Błąd komunikacji z API: {error}</p>}

        {status && <StatusBanner status={status} />}

        {status && <ControlToolbar status={status} onChanged={refresh} />}

        <div className="grid">
          {portfolio && <PortfolioChart history={portfolio.history} current={portfolio.current} />}
          {status && <ManualTradePanel status={status} onChanged={refresh} />}
        </div>

        <div style={{ marginBottom: 16 }}>
          <DecisionsLog decisions={decisions} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <MarketLog history={portfolio?.history ?? []} whitelist={status?.whitelist ?? []} />
        </div>

        <TradesTable trades={trades} />
      </div>
    </>
  );
}
