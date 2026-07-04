export interface StatusResponse {
  mode: "testnet" | "live";
  is_paused: boolean;
  is_halted: boolean;
  halted_reason: string | null;
  day_pnl_pct: number | null;
  week_pnl_pct: number | null;
  daily_loss_limit_pct: number;
  weekly_loss_limit_pct: number;
  max_position_pct: number;
  whitelist: string[];
  poll_interval_minutes: number;
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
}

export interface PortfolioResponse {
  current: PortfolioSnapshot | null;
  history: PortfolioSnapshot[];
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
  portfolio: () => apiFetch<PortfolioResponse>("/api/portfolio"),
  trades: () => apiFetch<Trade[]>("/api/trades"),
  decisions: () => apiFetch<Decision[]>("/api/decisions"),
  pause: () => apiFetch<unknown>("/api/control/pause", { method: "POST" }),
  resume: () => apiFetch<unknown>("/api/control/resume", { method: "POST" }),
  runCycleNow: () => apiFetch<unknown>("/api/control/run-cycle-now", { method: "POST" }),
  sendReportNow: () => apiFetch<{ message: string }>("/api/control/send-report-now", { method: "POST" }),
  restart: () => apiFetch<{ message: string }>("/api/control/restart", { method: "POST" }),
  manualTrade: (body: { symbol: string; side: "BUY" | "SELL"; usdt_amount?: number; quantity?: number }) =>
    apiFetch<Trade>("/api/control/manual-trade", { method: "POST", body: JSON.stringify(body) }),
};
