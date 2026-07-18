import { AccountHero } from "../components/AccountHero";
import { DecisionsLog } from "../components/DecisionsLog";
import { PortfolioChart } from "../components/PortfolioChart";
import { PositionsBoard } from "../components/PositionsBoard";
import { PulsCockpit } from "../components/PulsCockpit";
import { SectionTitle } from "../components/SectionTitle";
import { PageData } from "./types";

/** Dashboard główny — jednym rzutem oka: ile masz i jak się rusza (hero), żywy
 *  puls maszyny (sesja + nastawienie + stan silników), w co jesteś
 *  zainwestowany, krzywa konta i najnowsze decyzje. Szczegóły są w zakładkach
 *  silników i Centrum sterowania. */
export function OverviewPage({ data }: { data: PageData }) {
  const { status, portfolio, extendedPortfolio, decisions, refresh } = data;
  return (
    <>
      <AccountHero status={status} />
      <PulsCockpit status={status} />

      <SectionTitle eyebrow="Portfel" title="W co jesteś wejściem" />
      <PositionsBoard alpaca={portfolio} extended={extendedPortfolio} onChanged={refresh} />

      <SectionTitle eyebrow="Kapitał" title="Krzywa konta" />
      <PortfolioChart
        history={portfolio?.history ?? []}
        current={portfolio?.current ?? null}
        scorecard={portfolio?.scorecard ?? null}
      />

      <SectionTitle eyebrow="Mózg" title="Najnowsze decyzje Claude" />
      <div style={{ marginBottom: 16 }}>
        <DecisionsLog decisions={decisions.slice(0, 8)} />
      </div>
    </>
  );
}
