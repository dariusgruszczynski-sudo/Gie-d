export type MarketSession = "closed" | "regular" | null;

export interface SessionBounds {
  regular_open: string | null;
  regular_close: string | null;
}

export interface StatusResponse {
  mode: "testnet" | "live";
  quote_currency: string;
  is_paused: boolean;
  etoro_paused: boolean;
  is_halted: boolean;
  halted_reason: string | null;
  day_pnl_pct: number | null;
  week_pnl_pct: number | null;
  daily_loss_limit_pct: number;
  weekly_loss_limit_pct: number;
  max_position_pct: number;
  whitelist: string[];
  poll_interval_minutes: number;
  etoro_enabled: boolean;
  etoro_whitelist: string[];
  etoro_mode: "paper" | "live" | null;
  market_session: MarketSession;
  session_bounds: SessionBounds | null;
  claude_monthly_budget_usd: number;
  claude_spend_usd_this_month: number;
  claude_budget_pct_used: number;
  claude_budget_alert: boolean;
}

export interface PortfolioSnapshot {
  id: number;
  timestamp: string;
  total_value_usdt: number;
  usdt_balance: number;
  // JSON-encoded { [baseAsset]: qty } / { [symbol]: price } -- generic across
  // however many coins are in TRADING_WHITELIST. Parse with JSON.parse if a
  // future UI needs the per-coin breakdown; not currently rendered.
  balances_json: string;
  prices_json: string;
  // JSON list of whitelist symbols that failed to price this cycle (network
  // hiccup, delisted pair, ...) -- distinguishes "genuinely unavailable" from
  // "just hasn't loaded yet" in the UI.
  failed_symbols_json: string;
}

export interface Scorecard {
  portfolio_value: number;
  benchmark_symbol: string;
  benchmark_start_price: number | null;
  benchmark_start_value: number | null;
  benchmark_value: number | null;
  alpha_usd: number | null;
  alpha_pct: number | null;
  realized_pnl_usd: number;
  closed_trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number | null;
  since: string | null;
}

export interface PortfolioResponse {
  current: PortfolioSnapshot | null;
  history: PortfolioSnapshot[];
  // The very first snapshot ever recorded (independent of the `history`
  // window/limit) -- baseline for "since the beginning" P&L.
  inception: PortfolioSnapshot | null;
  // Average entry price per currently-held ticker ("SPY" -> 512.34), for
  // per-position unrealized P&L. Empty for assets not currently held.
  cost_basis: Record<string, number>;
  // Strategy scorecard vs buy-and-hold benchmark (null on a fresh account).
  scorecard: Scorecard | null;
  venue?: string;
}

export interface Trade {
  id: number;
  timestamp: string;
  symbol: string;
  side: string;
  quantity: number;
  price: number;
  usdt_value: number;
  order_id: string;
  mode: string;
  is_manual: boolean;
  decision_id: number | null;
}

export interface Decision {
  id: number;
  timestamp: string;
  symbol: string | null;
  action: "BUY" | "SELL" | "HOLD";
  size_pct: number;
  confidence: number;
  reasoning: string;
  triggered_by: string;
  executed: boolean;
  rejection_reason: string | null;
  // JSON-encoded snapshots of what Claude saw for this decision -- parse with
  // JSON.parse for per-symbol technical indicators / market sentiment.
  market_data_snapshot: string;
  market_context_snapshot: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  status: () => apiFetch<StatusResponse>("/api/status"),
  portfolio: (venue: string = "alpaca") => apiFetch<PortfolioResponse>(`/api/portfolio?limit=2000&venue=${venue}`),
  trades: (venue?: string) => apiFetch<Trade[]>(venue ? `/api/trades?venue=${venue}` : "/api/trades"),
  decisions: (venue?: string) => apiFetch<Decision[]>(venue ? `/api/decisions?venue=${venue}` : "/api/decisions"),
  logout: () => apiFetch<{ message: string }>("/api/auth/logout", { method: "POST" }),
  pause: (venue: string = "alpaca") => apiFetch<unknown>(`/api/control/pause?venue=${venue}`, { method: "POST" }),
  resume: (venue: string = "alpaca") => apiFetch<unknown>(`/api/control/resume?venue=${venue}`, { method: "POST" }),
  runCycleNow: (venue: string = "alpaca") =>
    apiFetch<unknown>(`/api/control/run-cycle-now?venue=${venue}`, { method: "POST" }),
  refreshPortfolio: (venue: string = "alpaca") =>
    apiFetch<{
      total_value: number;
      quote_balance: number;
      balances: Record<string, number>;
      prices: Record<string, number>;
      failed_symbols: string[];
      quote_currency: string;
    }>(`/api/control/refresh-portfolio?venue=${venue}`, { method: "POST" }),
  sendReportNow: () => apiFetch<{ message: string }>("/api/control/send-report-now", { method: "POST" }),
  restart: () => apiFetch<{ message: string }>("/api/control/restart", { method: "POST" }),
  manualTrade: (body: {
    symbol: string;
    side: "BUY" | "SELL";
    usdt_amount?: number;
    quantity?: number;
    venue?: "alpaca" | "etoro";
  }) => apiFetch<Trade>("/api/control/manual-trade", { method: "POST", body: JSON.stringify(body) }),
};
