import { AccountHero } from "../components/AccountHero";
import { DecisionsLog } from "../components/DecisionsLog";
import { PortfolioChart } from "../components/PortfolioChart";
import { PositionsBoard } from "../components/PositionsBoard";
import { PageData } from "./types";

/** Dashboard główny — TYLKO najważniejsze na jeden rzut oka: ile masz i jak się
 *  rusza (hero), w co jesteś zainwestowany (pozycje + „co robię"), krzywa konta
 *  i ostatnie decyzje. Szczegóły (nastawy silników) są w Centrum sterowania
 *  i zakładkach silników. */
export function OverviewPage({ data }: { data: PageData }) {
  const { status, portfolio, extendedPortfolio, decisions, refresh } = data;
  return (
    <>
      <AccountHero status={status} />
      <PositionsBoard alpaca={portfolio} extended={extendedPortfolio} onChanged={refresh} />
      <PortfolioChart
        history={portfolio?.history ?? []}
        current={portfolio?.current ?? null}
        scorecard={portfolio?.scorecard ?? null}
      />
      <div style={{ marginBottom: 16 }}>
        <DecisionsLog decisions={decisions.slice(0, 8)} />
      </div>
    </>
  );
}
