import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade } from "./api/client";
import { AccountSummary } from "./components/AccountSummary";
import { BrandLogo } from "./components/BrandLogo";
import { ControlToolbar } from "./components/ControlToolbar";
import { DecisionSplash } from "./components/DecisionSplash";
import { DecisionsLog } from "./components/DecisionsLog";
import { EmberBackground } from "./components/EmberBackground";
import { InvestmentThesis } from "./components/InvestmentThesis";
import { ManualTradePanel } from "./components/ManualTradePanel";
import { MarketLog } from "./components/MarketLog";
import { PortfolioChart } from "./components/PortfolioChart";
import { PortfolioHoldings } from "./components/PortfolioHoldings";
import { PriceTicker } from "./components/PriceTicker";
import { Scorecard } from "./components/Scorecard";
import { SessionClock } from "./components/SessionClock";
import { StatusBanner } from "./components/StatusBanner";
import { TradesTable } from "./components/TradesTable";
import { isSoundMuted, playTradeSound, setSoundMuted } from "./tradeSound";

const REFRESH_MS = 15000;

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [splashDecision, setSplashDecision] = useState<Decision | null>(null);
  const [muted, setMuted] = useState<boolean>(isSoundMuted);
  const seenDecisionIds = useRef<Set<number> | null>(null);
  const seenTradeIds = useRef<Set<number> | null>(null);

  const toggleMuted = useCallback(() => {
    setMuted((m) => {
      const next = !m;
      setSoundMuted(next);
      return next;
    });
  }, []);

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
        }
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
      {status && (
        <div className="ticker">
          <AccountSummary current={portfolio?.current ?? null} inception={portfolio?.inception ?? null} />
          <PriceTicker history={portfolio?.history ?? []} whitelist={status.whitelist} />
        </div>
      )}
      <div className="app">
        <div className="app-header">
          <BrandLogo size={48} />
          <div>
            <h1>Giel<span className="brand-accent">Darek</span></h1>
            <p className="subtitle">
              Decyzje: Claude (Sonnet + Opus) · Wykonanie: Alpaca · Narzędzie prywatne, nie jest to porada inwestycyjna.
            </p>
          </div>
        </div>

        {error && <p className="error-text">Błąd komunikacji z API: {error}</p>}

        {status && <StatusBanner status={status} />}

        {status && <ControlToolbar status={status} onChanged={refresh} muted={muted} onToggleMuted={toggleMuted} />}

        {status && (
          <div style={{ marginBottom: 16 }}>
            <SessionClock
              session={status.market_session}
              bounds={status.session_bounds}
              extendedHoursEnabled={status.extended_hours_active}
              extendedHoursAutoUsd={status.extended_hours_auto_enable_usd}
            />
          </div>
        )}

        {portfolio && <Scorecard data={portfolio.scorecard} />}

        {status && <InvestmentThesis whitelist={status.whitelist} />}

        <div className="grid">
          {portfolio && <PortfolioChart history={portfolio.history} current={portfolio.current} />}
          {status && <ManualTradePanel status={status} onChanged={refresh} />}
        </div>

        <div style={{ marginBottom: 16 }}>
          <PortfolioHoldings current={portfolio?.current ?? null} costBasis={portfolio?.cost_basis ?? {}} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <TradesTable trades={trades} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <DecisionsLog decisions={decisions} />
        </div>

        <MarketLog history={portfolio?.history ?? []} whitelist={status?.whitelist ?? []} />
      </div>
    </>
  );
}
