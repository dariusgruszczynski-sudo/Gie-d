import { Decision, PortfolioResponse, StatusResponse, Trade } from "../api/client";

export type TabKey = "overview" | "us" | "extended" | "control" | "health";

/** All the shared, already-fetched dashboard state, passed down to each page so
 *  data is fetched ONCE in App and every tab renders from the same snapshot. */
export interface PageData {
  status: StatusResponse;
  portfolio: PortfolioResponse | null;
  extendedPortfolio: PortfolioResponse | null;
  trades: Trade[];
  extendedTrades: Trade[];
  decisions: Decision[];
  refresh: () => void;
  muted: boolean;
  toggleMuted: () => void;
  // Shows the loading splash, then does a REAL page reload -- picks up any
  // frontend update immediately instead of just replaying an animation.
  shutdown: () => void;
}
