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
  extended_positions_value: number;
  total_value: number;
}

export interface ClaudeBudget {
  budget_usd: number;
  spent_usd: number;
  remaining_usd: number;
  pct_used: number;
  halt_at_zero: boolean;
  exhausted: boolean;
  // Odczytane (nie szacowane) liczby tokenów za bieżący miesiąc.
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
}

export interface StatusResponse {
  mode: "testnet" | "live";
  quote_currency: string;
  is_paused: boolean;
  extended_paused: boolean;
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
  extended_enabled: boolean;
  extended_whitelist: string[];
  market_session: MarketSession;
  session_bounds: SessionBounds | null;
  market_regime: MarketRegime | null;
  extended_market_regime: MarketRegime | null;
  // Live licznik tokenów AI: ile zostało z budżetu; halt gdy exhausted.
  claude_budget: ClaudeBudget;
  // The ONE Alpaca account shared by both engines (cash counted once).
  account: AccountView | null;
  // Ile zarobił/stracił SAM automat (odporne na wpłaty): zrealizowany + papierowy.
  trading_pnl: { realized_usd: number; unrealized_usd: number; total_usd: number };
  // Alfa vs trzymanie SPY (czy bijemy zwykłe DCA w indeks); null bez baseline'u.
  alpha_vs_spy: { benchmark: string; benchmark_value: number; alpha_usd: number; alpha_pct: number | null } | null;
  // Read-only share link enabled on the server (token stays server-side).
  share_enabled: boolean;
  // Honest bottom line: realized P&L across BOTH engines (one account) and
  // that same figure minus what Claude has actually cost this month.
  realized_pnl_usd: number;
  net_result_usd: number;
  // Every live tuning knob per venue, resolved through the same
  // effective_settings() the engine itself runs with -- exact, not a guess.
  profiles: { alpaca: EngineProfile; extended: EngineProfile };
  // Stempel wersji: jaki kod realnie działa na serwerze (SHA + czas buildu).
  build_sha: string;
  build_time: string;
  claude_monthly_budget_usd: number;
  claude_spend_usd_this_month: number;
  claude_budget_remaining_usd: number;
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
  progressive_confidence_step: number;
  progressive_confidence_cap: number;
  max_new_positions_per_day: number;
  max_concurrent_positions: number;
  min_hold_minutes: number;
  min_hold_profit_bypass_pct: number;
  hard_take_profit_pct: number;
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
  // Deposit-proof P&L curve aligned 1:1 with `history`: realized+unrealized at
  // each snapshot, so it doesn't jump when you top the account up.
  pnl_history?: number[];
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
  // "alpaca" (US equities) or "extended" -- which engine made the call.
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

// Twardy timeout na KAŻDE zapytanie. Bez tego zawieszone połączenie (typowe na
// mobilnej sieci) wisi w nieskończoność i zajmuje jeden z ~6 slotów połączeń,
// które iOS daje na host -- kilka takich i apka nie dobija się już do NICZEGO
// ("panel bez bebechów"). AbortController ubija zawieszkę, zwalnia slot, a pętla
// odświeżania sama ponawia i dociąga dane, gdy serwer odpowie.
const REQUEST_TIMEOUT_MS = 12000;
// Akcje, które z natury trwają długo (pełny cykl = analiza Claude + broker,
// ręczna transakcja, odświeżenie z brokera) dostają DŁUŻSZY limit -- 12s to za
// mało na wywołanie Claude i zwracało "serwer nie odpowiedział w 12s" na
// "Przemyśl teraz". Odczyty dashboardu zostają na krótkim 12s.
const LONG_TIMEOUT_MS = 90000;

async function apiFetch<T>(path: string, init?: RequestInit, timeoutMs: number = REQUEST_TIMEOUT_MS): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...init,
      signal: ctrl.signal,
    });
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`${res.status}: ${body}`);
    }
    return res.json() as Promise<T>;
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error(`timeout: serwer nie odpowiedział w ${Math.round(timeoutMs / 1000)}s`);
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
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
  news: () => apiFetch<{ items: NewsItem[] }>(withShare("/api/news")),
  logout: () => apiFetch<{ message: string }>("/api/auth/logout", { method: "POST" }),
  pause: (venue: string = "alpaca") => apiFetch<unknown>(`/api/control/pause?venue=${venue}`, { method: "POST" }),
  resume: (venue: string = "alpaca") => apiFetch<unknown>(`/api/control/resume?venue=${venue}`, { method: "POST" }),
  runCycleNow: (venue: string = "alpaca") =>
    apiFetch<unknown>(`/api/control/run-cycle-now?venue=${venue}`, { method: "POST" }, LONG_TIMEOUT_MS),
  refreshPortfolio: (venue: string = "alpaca") =>
    apiFetch<{
      total_value: number;
      quote_balance: number;
      balances: Record<string, number>;
      prices: Record<string, number>;
      failed_symbols: string[];
      quote_currency: string;
    }>(`/api/control/refresh-portfolio?venue=${venue}`, { method: "POST" }, LONG_TIMEOUT_MS),
  sendReportNow: () => apiFetch<{ message: string }>("/api/control/send-report-now", { method: "POST" }),
  restart: () => apiFetch<{ message: string }>("/api/control/restart", { method: "POST" }),
  manualTrade: (body: {
    symbol: string;
    side: "BUY" | "SELL";
    usdt_amount?: number;
    quantity?: number;
    venue?: "alpaca" | "extended";
  }) => apiFetch<Trade>("/api/control/manual-trade", { method: "POST", body: JSON.stringify(body) }, LONG_TIMEOUT_MS),
  sellAll: (symbol: string, venue: "alpaca" | "extended" = "alpaca") =>
    apiFetch<Trade>(`/api/control/sell-all?symbol=${encodeURIComponent(symbol)}&venue=${venue}`, { method: "POST" }, LONG_TIMEOUT_MS),
  setBudget: (amount: number) =>
    apiFetch<{ claude_budget: ClaudeBudget }>(`/api/control/set-budget?amount=${amount}`, { method: "POST" }),
  resetBudgetMeter: () =>
    apiFetch<{ claude_budget: ClaudeBudget }>("/api/control/reset-budget-meter", { method: "POST" }),
  shareLink: () => apiFetch<{ enabled: boolean; token: string }>("/api/control/share-link"),
  claudeEdge: (venue: string = "alpaca") =>
    apiFetch<ClaudeEdge>(withShare(`/api/claude-edge?venue=${venue}`)),
  pushConfig: () => apiFetch<{ enabled: boolean; vapid_public_key: string }>("/api/push/config"),
  pushSubscribe: (sub: PushSubscriptionJSON) =>
    apiFetch<{ message: string }>("/api/push/subscribe", { method: "POST", body: JSON.stringify(sub) }),
  pushUnsubscribe: (sub: { endpoint: string; keys: { p256dh: string; auth: string } }) =>
    apiFetch<{ message: string }>("/api/push/unsubscribe", { method: "POST", body: JSON.stringify(sub) }),
  pushTest: () => apiFetch<{ message: string }>("/api/push/test", { method: "POST" }),
  positionPlans: (venue: string = "alpaca") =>
    apiFetch<PositionPlansResponse>(withShare(`/api/position-plans?venue=${venue}`)),
  history: () => apiFetch<HistoryResponse>(withShare("/api/history")),
  health: () => apiFetch<HealthReport>("/api/health"),
  newsSources: () => apiFetch<NewsSourcesResponse>("/api/news/sources"),
  healthReset: (action: string) =>
    apiFetch<{ action: string; message: string }>("/api/health/reset", {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
};

export interface HistoryTrade {
  symbol: string;
  venue: string;
  qty: number;
  avg_buy_price: number;
  sell_price: number;
  cost_usd: number;
  proceeds_usd: number;
  pnl_usd: number;
  pnl_pct: number | null;
  opened_at: string | null;
  sold_at: string | null;
  days_held: number | null;
}
export interface HistoryResponse {
  trades: HistoryTrade[];
  summary: {
    count: number;
    wins: number;
    losses: number;
    total_pnl_usd: number;
    best: HistoryTrade | null;
    worst: HistoryTrade | null;
  };
}

export interface NewsItem {
  title: string;
  source: string;
  published_at: string | null;
  tickers: string[];
}

export interface NewsSource {
  name: string;
  group: string;
  status: "ok" | "down";
  count: number;
}

export interface NewsSourceHeadline {
  title: string;
  source: string;
  published_at: string | null;
  sentiment_label?: string;
  sentiment_score?: number;
}

export interface NewsSourcesResponse {
  sources: NewsSource[];
  headlines: NewsSourceHeadline[];
  summary: { ok: number; down: number; headlines: number };
  // Auto-odkrywanie źródeł: ile trwale odkrytych + ile dołożył ostatni przebieg.
  discovery?: { total: number; added_last: number; date: string | null };
  generated_at?: string;
  cached?: boolean;
}

export interface PositionPlan {
  asset: string;
  qty: number;
  basis: number | null;
  price: number;
  value: number;
  adopted: boolean;
  change_pct: number | null;
  stop_pct: number;
  take_profit_arm_pct: number;
  partial_at_pct: number;
  trailing_dist_pct: number;
  action: "hold" | "near_stop" | "partial_ready" | "trailing_protected" | "adopted";
  note: string;
  // Strategia pozycyjna: kontekst "po co trzymamy".
  days_held: number | null;
  stop_price: number | null;
  target_price: number | null;
  thesis: string | null;
  // "KIEDY SPRZEDAM" — kiedy i dlaczego bot zamknie tę pozycję (miarka + opis).
  sell_plan?: SellPlan;
}

export type SellState = "sell_now" | "profit_ready" | "climbing" | "locked" | "waiting" | "near_stop";
export interface SellPlan {
  state: SellState;
  headline: string;
  when: string;
  progress_pct: number;
  release: string | null;
  locked: boolean;
  detail: string;
}

export interface PositionPlansResponse {
  venue: string;
  positions: PositionPlan[];
}

export type HealthStatus = "ok" | "warn" | "down" | "off";

export interface HealthCheck {
  key: string;
  label: string;
  group: string;
  status: HealthStatus;
  detail: string;
  action: string | null;
}

export interface HealthReport {
  overall: HealthStatus;
  counts: Record<HealthStatus, number>;
  checks: HealthCheck[];
  checked_at: string;
}
