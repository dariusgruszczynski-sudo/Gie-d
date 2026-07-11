import { useCallback, useEffect, useRef, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade } from "./api/client";
import { AccountBar } from "./components/AccountBar";
import { BrandLogo } from "./components/BrandLogo";
import { ControlToolbar } from "./components/ControlToolbar";
import { DecisionSplash } from "./components/DecisionSplash";
import { DecisionsLog } from "./components/DecisionsLog";
import { EmberBackground } from "./components/EmberBackground";
import { InvestmentThesis } from "./components/InvestmentThesis";
import { ManualTradePanel } from "./components/ManualTradePanel";
import { MarketStrip } from "./components/MarketStrip";
import { PortfolioChart } from "./components/PortfolioChart";
import { PositionsBoard } from "./components/PositionsBoard";
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
  const [cryptoPortfolio, setCryptoPortfolio] = useState<PortfolioResponse | null>(null);
  const [cryptoTrades, setCryptoTrades] = useState<Trade[]>([]);
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
          {/* ONE Alpaca account (cash counted once), then the two engines that
              trade it -- not two separate portfolios. */}
          <AccountBar account={status.account} dayPnlPct={status.day_pnl_pct} />
          <div className="ticker-labeled">
            <span className="ticker-venue-label">
              <span className="venue-dot venue-dot-alpaca" /> Silnik · Akcje US (sesja dzienna)
              {status.market_regime && <RegimeBadge regime={status.market_regime} prefix="Rynek" />}
            </span>
            <div className="ticker">
              <PriceTicker history={portfolio?.history ?? []} whitelist={status.whitelist} />
            </div>
          </div>
          <div className="ticker-labeled">
            <span className="ticker-venue-label">
              <span className="venue-dot venue-dot-crypto" /> Silnik · Krypto (24/7)
              {status.crypto_enabled && status.crypto_market_regime && (
                <RegimeBadge regime={status.crypto_market_regime} prefix="Krypto" />
              )}
              {!status.crypto_enabled && <span className="venue-off-tag">wyłączony</span>}
            </span>
            <div className="ticker">
              <PriceTicker history={cryptoPortfolio?.history ?? []} whitelist={status.crypto_whitelist} />
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
              Dwa mózgi Claude (Sonnet→Opus): akcje USA średnio agresywnie · krypto 24/7 agresywnie ·
              wykonanie Alpaca · narzędzie prywatne, nie jest to porada inwestycyjna.
            </p>
          </div>
        </div>

        {error && <p className="error-text">Błąd komunikacji z API: {error}</p>}

        {status && <StatusBanner status={status} />}

        {/* ===== Pozycje: co, w której nodze, ile, za ile, ile zysku ===== */}
        {status && <PositionsBoard alpaca={portfolio} crypto={cryptoPortfolio} />}

        {/* ===== Panele kontrolne (per portfel) ===== */}
        {status && (
          <div className="grid">
            <VenueControls
              venue="alpaca"
              label="Silnik — Akcje US"
              paused={status.is_paused}
              halted={status.is_halted}
              enabled
              onChanged={refresh}
            />
            <VenueControls
              venue="crypto"
              label="Silnik — Krypto 24/7"
              paused={status.crypto_paused}
              enabled={status.crypto_enabled}
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
            <ManualTradePanel whitelist={status.whitelist} onChanged={refresh} venue="alpaca" title="Ręczna transakcja — Silnik Akcje US" />
            {status.crypto_enabled ? (
              <ManualTradePanel whitelist={status.crypto_whitelist} onChanged={refresh} venue="crypto" title="Ręczna transakcja — Silnik Krypto" />
            ) : (
              <div className="panel">
                <h2>Ręczna transakcja — Krypto</h2>
                <p className="subtitle venue-off-note">Portfel krypto wyłączony — włącz go (CRYPTO_ENABLED) i zasil konto, żeby handlować 24/7.</p>
              </div>
            )}
          </div>
        )}

        {/* ===== W co inwestuję (oba silniki, jedna lista) ===== */}
        {status && <InvestmentThesis whitelist={[...status.whitelist, ...status.crypto_whitelist]} />}

        {/* ===== Wykres wartości CAŁEGO konta (jedno konto, nie dwa) ===== */}
        <PortfolioChart history={portfolio?.history ?? []} current={portfolio?.current ?? null} scorecard={portfolio?.scorecard ?? null} />

        {/* ===== Historia transakcji per silnik ===== */}
        <div className="grid">
          <TradesTable trades={trades} title="Transakcje — Silnik Akcje US" />
          <TradesTable trades={cryptoTrades} title="Transakcje — Silnik Krypto" />
        </div>

        {/* ===== Log decyzji Claude — na samym dole (oba silniki) ===== */}
        <div style={{ marginBottom: 16 }}>
          <DecisionsLog decisions={decisions} />
        </div>
      </div>
    </>
  );
}
