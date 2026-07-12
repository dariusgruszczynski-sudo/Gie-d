import { AccountBar } from "../components/AccountBar";
import { DecisionsLog } from "../components/DecisionsLog";
import { PortfolioChart } from "../components/PortfolioChart";
import { PositionsBoard } from "../components/PositionsBoard";
import { StatusBanner } from "../components/StatusBanner";
import { PageData } from "./types";

/** Dashboard główny: jednym rzutem oka — ile masz kasy i akcji TERAZ, stan
 *  obu silników, statystyki (P&L, budżet, żywe tokeny Claude), pozycje i wykres
 *  wartości całego konta. Szczegóły per silnik są w osobnych zakładkach. */
export function OverviewPage({ data }: { data: PageData }) {
  const { status, portfolio, cryptoPortfolio, decisions } = data;
  return (
    <>
      <AccountBar account={status.account} dayPnlPct={status.day_pnl_pct} />
      <StatusBanner status={status} />
      <PositionsBoard alpaca={portfolio} crypto={cryptoPortfolio} />
      <PortfolioChart
        history={portfolio?.history ?? []}
        current={portfolio?.current ?? null}
        scorecard={portfolio?.scorecard ?? null}
      />
      <div style={{ marginBottom: 16 }}>
        <DecisionsLog decisions={decisions.slice(0, 12)} />
      </div>
    </>
  );
}
