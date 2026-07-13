import { DecisionsLog } from "../components/DecisionsLog";
import { InvestmentThesis } from "../components/InvestmentThesis";
import { ManualTradePanel } from "../components/ManualTradePanel";
import { MarketStrip } from "../components/MarketStrip";
import { PositionsBoard } from "../components/PositionsBoard";
import { PriceTicker } from "../components/PriceTicker";
import { RegimeBadge } from "../components/RegimeBadge";
import { TradesTable } from "../components/TradesTable";
import { VenueControls } from "../components/VenueControls";
import { isReadOnly } from "../api/client";
import { PageData } from "./types";

/** One engine's full dashboard: ticker, regime, START/STOP, its own positions,
 *  manual trade, trade history, thesis and Claude decisions — filtered to just
 *  that venue (Alpaca US equities OR crypto). */
export function EnginePage({ data, venue }: { data: PageData; venue: "alpaca" | "crypto" }) {
  const { status, refresh } = data;
  const isCrypto = venue === "crypto";
  const portfolio = isCrypto ? data.cryptoPortfolio : data.portfolio;
  const trades = isCrypto ? data.cryptoTrades : data.trades;
  const whitelist = isCrypto ? status.crypto_whitelist : status.whitelist;
  const regime = isCrypto ? status.crypto_market_regime : status.market_regime;
  const dot = isCrypto ? "crypto" : "alpaca";
  const label = isCrypto ? "Silnik — Krypto (24/7)" : "Silnik — Akcje US (sesja dzienna)";
  const decisions = data.decisions.filter((d) => (d.venue ?? "alpaca") === venue);

  if (isCrypto && !status.crypto_enabled) {
    return (
      <div className="panel">
        <div className="venue-controls-head">
          <span className="venue-dot venue-dot-crypto" /> {label}
        </div>
        <p className="subtitle" style={{ margin: 0 }}>
          Silnik krypto jest wyłączony (CRYPTO_ENABLED=false). Włącz go w konfiguracji i zasil konto, żeby handlować
          24/7.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="ticker-labeled engine-ticker">
        <span className="ticker-venue-label">
          <span className={`venue-dot venue-dot-${dot}`} /> {label}
          {regime && <RegimeBadge regime={regime} prefix={isCrypto ? "Krypto" : "Rynek"} />}
        </span>
        <div className="ticker">
          <PriceTicker history={portfolio?.history ?? []} whitelist={whitelist} />
        </div>
      </div>

      {!isReadOnly && (
        <VenueControls
          venue={venue}
          label={label}
          paused={isCrypto ? status.crypto_paused : status.is_paused}
          halted={isCrypto ? undefined : status.is_halted}
          enabled={isCrypto ? status.crypto_enabled : true}
          onChanged={refresh}
        />
      )}

      <PositionsBoard alpaca={isCrypto ? null : portfolio} crypto={isCrypto ? portfolio : null} onChanged={refresh} />

      {!isCrypto && (
        <MarketStrip
          session={status.market_session}
          bounds={status.session_bounds}
          lastCycleAt={portfolio?.current?.timestamp ?? null}
          pollIntervalMinutes={status.poll_interval_minutes}
          scorecard={portfolio?.scorecard ?? null}
          regime={status.market_regime}
        />
      )}

      <div className="grid">
        {!isReadOnly && (
          <ManualTradePanel
            whitelist={whitelist}
            onChanged={refresh}
            venue={venue}
            title={`Ręczna transakcja — ${isCrypto ? "Krypto" : "Akcje US"}`}
          />
        )}
        <TradesTable trades={trades} title={`Transakcje — ${isCrypto ? "Krypto" : "Akcje US"}`} />
      </div>

      <InvestmentThesis whitelist={whitelist} />

      <div style={{ marginBottom: 16 }}>
        <DecisionsLog decisions={decisions} />
      </div>
    </>
  );
}
