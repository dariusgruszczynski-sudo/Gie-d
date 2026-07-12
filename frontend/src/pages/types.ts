import { Decision, PortfolioResponse, StatusResponse, Trade } from "../api/client";

export type TabKey = "overview" | "us" | "crypto" | "control";

/** All the shared, already-fetched dashboard state, passed down to each page so
 *  data is fetched ONCE in App and every tab renders from the same snapshot. */
export interface PageData {
  status: StatusResponse;
  portfolio: PortfolioResponse | null;
  cryptoPortfolio: PortfolioResponse | null;
  trades: Trade[];
  cryptoTrades: Trade[];
  decisions: Decision[];
  refresh: () => void;
  muted: boolean;
  toggleMuted: () => void;
}
