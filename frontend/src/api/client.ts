export type MarketSession = "closed" | "regular" | null;

export interface SessionBounds {
  regular_open: string | null;
  regular_close: string | null;
}

export interface MarketRegime {
  regime: "risk_on" | "neutral" | "risk_off";
  score: number;
  reasons: string[];
  // Self-tuning aggression the engine picked for this regime (adaptive risk):
  // ~1.3 aggressive, 1.0 neutral, ~0.4 defensive. Optional (absent when
  // adaptive risk is off).
  aggression?: number;
  aggression_label?: string;
}

// The single Alpaca account both engines share. Cash is counted ONCE; each
// engine contributes only its own positions' market value.
export interface AccountView {
  cash: number;
  equity_positions_value: number;
  crypto_positions_value: number;
  total_value: number;
}

export interface StatusResponse {
  mode: "testnet" | "live";
  quote_currency: string;
  is_paused: boolean;
  crypto_paused: boolean;
  is_halted: boolean;
  halted_reason: string | null;
  day_pnl_pct: number | null;
  week_pnl_pct: number | null;
  daily_loss_limit_pct: number;
  weekly_loss_limit_pct: number;
  max_drawdown_halt_pct: number;
  peak_account_value: number;
  max_position_pct: number;
  whitelist: string[];
  poll_interval_minutes: number;
  crypto_enabled: boolean;
  crypto_whitelist: string[];
  market_session: MarketSession;
  session_bounds: SessionBounds | null;
  market_regime: MarketRegime | null;
  crypto_market_regime: MarketRegime | null;
  // The ONE Alpaca account shared by both engines (cash counted once).
  account: AccountView | null;
  // Read-only share link enabled on the server (token stays server-side).
  share_enabled: boolean;
  // Honest bottom line: realized P&L across BOTH engines (one account) and
  // that same figure minus what Claude has actually cost this month.
  realized_pnl_usd: number;
  net_result_usd: number;
  // Every live tuning knob per venue, resolved through the same
  // effective_settings() the engine itself runs with -- exact, not a guess.
  profiles: { alpaca: EngineProfile; crypto: EngineProfile };
  claude_monthly_budget_usd: number;
  claude_spend_usd_this_month: number;
  claude_budget_pct_used: number;
  claude_budget_alert: boolean;
  claude_input_tokens_this_month: number;
  claude_output_tokens_this_month: number;
  claude_total_tokens_this_month: number;
}

export interface EngineProfile {
  signal_timeframe: string;
  poll_interval_minutes: number;
  risk_per_trade_pct: number;
  min_buy_confidence: number;
  max_new_positions_per_day: number;
  max_concurrent_positions: number;
  min_hold_minutes: number;
  max_position_pct: number;
  stop_loss_min_pct: number;
  stop_loss_max_pct: number;
  reward_risk_ratio: number;
  trailing_stop_frac: number;
  partial_take_profit_frac: number;
  partial_take_profit_r: number;
  price_move_trigger_pct: number;
  full_analysis_every_minutes: number;
  volatility_reference_pct: number;
  allocation_pct: number;
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
  // "alpaca" (US equities) or "crypto" -- which engine made the call.
  venue?: string;
  // JSON-encoded snapshots of what Claude saw for this decision -- parse with
  // JSON.parse for per-symbol technical indicators / market sentiment.
  market_data_snapshot: string;
  market_context_snapshot: string;
}

// Read-only share mode: a "?share=<token>" in the URL grants view-only access
// (no login, no controls). Every GET must carry the token so the server lets it
// through; nothing else is exposed.
export const shareToken =
  typeof window !== "undefined" ? new URLSearchParams(window.location.search).get("share") || "" : "";
export const isReadOnly = !!shareToken;

export function withShare(path: string): string {
  if (!shareToken) return path;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}share=${encodeURIComponent(shareToken)}`;
}

export interface ClaudeEdgeSide {
  closed_trades: number;
  wins: number;
  losses: number;
  win_rate_pct: number | null;
  avg_return_pct?: number | null;
  notional_realized_usd?: number;
  realized_usd?: number;
}

export interface ClaudeEdge {
  venue: string;
  cycles_analyzed: number;
  mechanical_only: ClaudeEdgeSide;
  with_claude: ClaudeEdgeSide;
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
  status: () => apiFetch<StatusResponse>(withShare("/api/status")),
  // 600 per-cycle snapshots (~kilka dni handlu) to plenty for the chart while
  // keeping every 15s/SSE refresh light -- 2000 uncompressed rows on each poll
  // was a big chunk of the "apka działa wolno". P&L "od początku" stays correct
  // regardless: the backend anchors it on the inception snapshot, not this window.
  portfolio: (venue: string = "alpaca") => apiFetch<PortfolioResponse>(withShare(`/api/portfolio?limit=600&venue=${venue}`)),
  trades: (venue?: string) => apiFetch<Trade[]>(withShare(venue ? `/api/trades?venue=${venue}` : "/api/trades")),
  decisions: (venue?: string) => apiFetch<Decision[]>(withShare(venue ? `/api/decisions?venue=${venue}` : "/api/decisions")),
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
    venue?: "alpaca" | "crypto";
  }) => apiFetch<Trade>("/api/control/manual-trade", { method: "POST", body: JSON.stringify(body) }),
  shareLink: () => apiFetch<{ enabled: boolean; token: string }>("/api/control/share-link"),
  claudeEdge: (venue: string = "alpaca") =>
    apiFetch<ClaudeEdge>(withShare(`/api/claude-edge?venue=${venue}`)),
  pushConfig: () => apiFetch<{ enabled: boolean; vapid_public_key: string }>("/api/push/config"),
  pushSubscribe: (sub: PushSubscriptionJSON) =>
    apiFetch<{ message: string }>("/api/push/subscribe", { method: "POST", body: JSON.stringify(sub) }),
  pushUnsubscribe: (sub: { endpoint: string; keys: { p256dh: string; auth: string } }) =>
    apiFetch<{ message: string }>("/api/push/unsubscribe", { method: "POST", body: JSON.stringify(sub) }),
  pushTest: () => apiFetch<{ message: string }>("/api/push/test", { method: "POST" }),
};
