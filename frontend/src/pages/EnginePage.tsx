import { DecisionsLog } from "../components/DecisionsLog";
import { InvestmentThesis } from "../components/InvestmentThesis";
import { ManualTradePanel } from "../components/ManualTradePanel";
import { MarketStrip } from "../components/MarketStrip";
import { PositionsBoard } from "../components/PositionsBoard";
import { PriceTicker } from "../components/PriceTicker";
import { RegimeBadge } from "../components/RegimeBadge";
import { SectionTitle } from "../components/SectionTitle";
import { TradesTable } from "../components/TradesTable";
import { VenueControls } from "../components/VenueControls";
import { isReadOnly } from "../api/client";
import { PageData } from "./types";

/** One engine's cockpit, organised into clear chapters: a live ticker + regime
 *  header, START/STOP, its positions, the market/session strip (US), manual
 *  trade + history, the whitelist thesis, and that engine's Claude decisions —
 *  all filtered to just this venue (Akcje US OR Poza sesją). */
export function EnginePage({ data, venue }: { data: PageData; venue: "alpaca" | "extended" }) {
  const { status, refresh } = data;
  const isExtended = venue === "extended";
  const portfolio = isExtended ? data.extendedPortfolio : data.portfolio;
  const trades = isExtended ? data.extendedTrades : data.trades;
  const whitelist = isExtended ? status.extended_whitelist : status.whitelist;
  const regime = isExtended ? status.extended_market_regime : status.market_regime;
  const dot = isExtended ? "extended" : "alpaca";
  const label = isExtended ? "Silnik — Poza sesją (pre & after-market)" : "Silnik — Akcje US (sesja dzienna)";
  const short = isExtended ? "Poza sesją" : "Akcje US";
  const decisions = data.decisions.filter((d) => (d.venue ?? "alpaca") === venue);

  if (isExtended && !status.extended_enabled) {
    return (
      <div className="panel">
        <div className="venue-controls-head">
          <span className="venue-dot venue-dot-extended" /> {label}
        </div>
        <p className="subtitle" style={{ margin: 0 }}>
          Silnik poza sesją jest wyłączony (EXTENDED_ENABLED=false). Włącz go w konfiguracji i zasil konto, żeby handlować
          w pre-market i after-hours.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="ticker-labeled engine-ticker">
        <span className="ticker-venue-label">
          <span className={`venue-dot venue-dot-${dot}`} /> {label}
          {regime && <RegimeBadge regime={regime} prefix={isExtended ? "Poza sesją" : "Rynek"} />}
        </span>
        <div className="ticker">
          <PriceTicker history={portfolio?.history ?? []} whitelist={whitelist} />
        </div>
      </div>

      {!isReadOnly && (
        <VenueControls
          venue={venue}
          label={label}
          paused={isExtended ? status.extended_paused : status.is_paused}
          halted={isExtended ? undefined : status.is_halted}
          enabled={isExtended ? status.extended_enabled : true}
          onChanged={refresh}
        />
      )}

      <SectionTitle eyebrow={short} title="Otwarte pozycje" />
      <PositionsBoard alpaca={isExtended ? null : portfolio} extended={isExtended ? portfolio : null} onChanged={refresh} />

      {!isExtended && (
        <>
          <SectionTitle eyebrow="Rynek" title="Sesja i skuteczność" />
          <MarketStrip
            session={status.market_session}
            bounds={status.session_bounds}
            lastCycleAt={portfolio?.current?.timestamp ?? null}
            pollIntervalMinutes={status.poll_interval_minutes}
            scorecard={portfolio?.scorecard ?? null}
            regime={status.market_regime}
          />
        </>
      )}

      <SectionTitle eyebrow={short} title={isReadOnly ? "Historia transakcji" : "Ręcznie i historia"} />
      <div className="grid">
        {!isReadOnly && (
          <ManualTradePanel
            whitelist={whitelist}
            onChanged={refresh}
            venue={venue}
            title={`Ręczna transakcja — ${short}`}
          />
        )}
        <TradesTable trades={trades} title={`Transakcje — ${short}`} />
      </div>

      <SectionTitle eyebrow="Whitelist" title="Teza inwestycyjna" />
      <InvestmentThesis whitelist={whitelist} />

      <SectionTitle eyebrow="Mózg" title="Decyzje Claude" />
      <div style={{ marginBottom: 16 }}>
        <DecisionsLog decisions={decisions} />
      </div>
    </>
  );
}
