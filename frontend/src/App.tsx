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
import { MarketStrip } from "./components/MarketStrip";
import { PortfolioChart } from "./components/PortfolioChart";
import { PortfolioHoldings } from "./components/PortfolioHoldings";
import { PriceTicker } from "./components/PriceTicker";
import { RegimeBadge } from "./components/RegimeBadge";
import { StatusBanner } from "./components/StatusBanner";
import { TradesTable } from "./components/TradesTable";
import { VenueControls } from "./components/VenueControls";
import { isSoundMuted, playTradeSound, setSoundMuted } from "./tradeSound";

const REFRESH_MS = 15000;

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [etoroPortfolio, setEtoroPortfolio] = useState<PortfolioResponse | null>(null);
  const [etoroTrades, setEtoroTrades] = useState<Trade[]>([]);
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
        api.portfolio("alpaca"),
        api.trades("alpaca"),
        api.decisions(),
      ]);
      setStatus(s);
      setPortfolio(p);
      setTrades(t);
      setDecisions(d);
      setError(null);

      // The 24-7 crypto/forex portfolio is fetched only when the venue is
      // enabled, so a single-broker setup pays no extra requests.
      if (s.etoro_enabled) {
        const [ep, et] = await Promise.all([api.portfolio("etoro"), api.trades("etoro")]);
        setEtoroPortfolio(ep);
        setEtoroTrades(et);
      } else {
        setEtoroPortfolio(null);
        setEtoroTrades([]);
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
        }
      }
    } catch (e) {
      setError(String(e));
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
    const es = new EventSource("/api/events");
    es.onmessage = () => refresh();
    return () => es.close();
  }, [refresh]);

  return (
    <>
      {splashDecision && <DecisionSplash decision={splashDecision} onDismiss={() => setSplashDecision(null)} />}
      <EmberBackground />
      {status && (
        <div className="tickers-stack">
          <div className="ticker-labeled">
            <span className="ticker-venue-label">
              <span className="venue-dot venue-dot-alpaca" /> Portfel dzienny · Alpaca (akcje US)
            </span>
            <div className="ticker">
              <AccountSummary current={portfolio?.current ?? null} inception={portfolio?.inception ?? null} />
              <PriceTicker history={portfolio?.history ?? []} whitelist={status.whitelist} />
            </div>
          </div>
          <div className="ticker-labeled">
            <span className="ticker-venue-label">
              <span className="venue-dot venue-dot-etoro" /> Portfel nocny · eToro (krypto/forex 24-7)
              {status.etoro_mode && (
                <span className="venue-mode-tag">{status.etoro_mode === "paper" ? "DEMO" : "LIVE"}</span>
              )}
              {status.etoro_enabled && status.etoro_market_regime && (
                <RegimeBadge regime={status.etoro_market_regime} prefix="Krypto/Forex" />
              )}
              {!status.etoro_enabled && <span className="venue-off-tag">wyłączony</span>}
            </span>
            <div className="ticker">
              <AccountSummary current={etoroPortfolio?.current ?? null} inception={etoroPortfolio?.inception ?? null} />
              <PriceTicker history={etoroPortfolio?.history ?? []} whitelist={status.etoro_whitelist} />
            </div>
          </div>
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

        {/* ===== Panele kontrolne (per portfel) ===== */}
        {status && (
          <div className="grid">
            <VenueControls
              venue="alpaca"
              label="Sterowanie — Alpaca (akcje)"
              paused={status.is_paused}
              halted={status.is_halted}
              enabled
              onChanged={refresh}
            />
            <VenueControls
              venue="etoro"
              label="Sterowanie — eToro (krypto/forex)"
              paused={status.etoro_paused}
              enabled={status.etoro_enabled}
              onChanged={refresh}
            />
          </div>
        )}

        {status && <ControlToolbar status={status} onChanged={refresh} muted={muted} onToggleMuted={toggleMuted} />}

        {status && (
          <MarketStrip
            session={status.market_session}
            bounds={status.session_bounds}
            lastCycleAt={portfolio?.current?.timestamp ?? null}
            pollIntervalMinutes={status.poll_interval_minutes}
            scorecard={portfolio?.scorecard ?? null}
            regime={status.market_regime}
          />
        )}

        {status && (
          <div className="grid">
            <ManualTradePanel whitelist={status.whitelist} onChanged={refresh} venue="alpaca" title="Ręczna transakcja — Alpaca (akcje)" />
            {status.etoro_enabled ? (
              <ManualTradePanel whitelist={status.etoro_whitelist} onChanged={refresh} venue="etoro" title="Ręczna transakcja — eToro (krypto/forex)" />
            ) : (
              <div className="panel">
                <h2>Ręczna transakcja — eToro</h2>
                <p className="subtitle venue-off-note">Portfel eToro wyłączony — włącz go (ETORO_ENABLED) i zasil konto, żeby handlować krypto/forex.</p>
              </div>
            )}
          </div>
        )}

        {/* ===== W co inwestuję (oba portfele) ===== */}
        <div className="grid">
          {status && <InvestmentThesis whitelist={status.whitelist} />}
          {status && <InvestmentThesis whitelist={status.etoro_whitelist} />}
        </div>

        {/* ===== Wykresy wartości (oba portfele) ===== */}
        <div className="grid">
          <PortfolioChart history={portfolio?.history ?? []} current={portfolio?.current ?? null} scorecard={portfolio?.scorecard ?? null} />
          <PortfolioChart history={etoroPortfolio?.history ?? []} current={etoroPortfolio?.current ?? null} scorecard={null} />
        </div>

        {/* ===== Pozycje (oba portfele, obok siebie) ===== */}
        <div className="grid">
          <PortfolioHoldings current={portfolio?.current ?? null} costBasis={portfolio?.cost_basis ?? {}} title="Pozycje — Alpaca" />
          <PortfolioHoldings current={etoroPortfolio?.current ?? null} costBasis={etoroPortfolio?.cost_basis ?? {}} title="Pozycje — eToro" />
        </div>

        {/* ===== Historia transakcji (oba portfele, obok siebie) ===== */}
        <div className="grid">
          <TradesTable trades={trades} title="Transakcje — Alpaca" />
          <TradesTable trades={etoroTrades} title="Transakcje — eToro" />
        </div>

        {/* ===== Log decyzji Claude — na samym dole (oba portfele) ===== */}
        <div style={{ marginBottom: 16 }}>
          <DecisionsLog decisions={decisions} />
        </div>

        <MarketLog history={portfolio?.history ?? []} whitelist={status?.whitelist ?? []} />
      </div>
    </>
  );
}
