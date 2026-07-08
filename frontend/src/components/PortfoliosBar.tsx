import { PortfolioResponse } from "../api/client";

function pnl(current: number | null, baseline: number | null): { usd: number; pct: number } | null {
  if (current === null || baseline === null || baseline <= 0) return null;
  const usd = current - baseline;
  return { usd, pct: (usd / baseline) * 100 };
}

function VenueCard({
  label,
  sub,
  accent,
  portfolio,
  enabled,
  mode,
}: {
  label: string;
  sub: string;
  accent: "alpaca" | "etoro";
  portfolio: PortfolioResponse | null;
  enabled: boolean;
  mode?: string | null;
}) {
  const current = portfolio?.current?.total_value_usdt ?? null;
  const inception = portfolio?.inception?.total_value_usdt ?? null;
  const pl = pnl(current, inception);

  return (
    <div className={`portfolio-card portfolio-card-${accent}`}>
      <div className="portfolio-card-head">
        <span className={`venue-dot venue-dot-${accent}`} />
        <span className="portfolio-card-label">{label}</span>
        {mode && <span className="venue-mode-tag">{mode === "paper" ? "DEMO" : "LIVE"}</span>}
        <span className="portfolio-card-sub">{sub}</span>
      </div>
      {!enabled ? (
        <div className="portfolio-card-value muted">wyłączony</div>
      ) : current === null ? (
        <div className="portfolio-card-value muted">oczekiwanie na zasilenie…</div>
      ) : (
        <>
          <div className="portfolio-card-value">${current.toFixed(2)}</div>
          {pl && (
            <div className={`portfolio-card-pnl ${pl.usd >= 0 ? "up" : "down"}`}>
              {pl.usd >= 0 ? "+" : ""}
              ${pl.usd.toFixed(2)} ({pl.usd >= 0 ? "+" : ""}
              {pl.pct.toFixed(2)}%)
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function PortfoliosBar({
  alpaca,
  etoro,
  etoroEnabled,
  etoroMode,
}: {
  alpaca: PortfolioResponse | null;
  etoro: PortfolioResponse | null;
  etoroEnabled: boolean;
  etoroMode?: string | null;
}) {
  const total =
    (alpaca?.current?.total_value_usdt ?? 0) + (etoroEnabled ? etoro?.current?.total_value_usdt ?? 0 : 0);

  return (
    <div className="portfolios-bar">
      <VenueCard
        label="Portfel dzienny"
        sub="Alpaca · akcje US"
        accent="alpaca"
        portfolio={alpaca}
        enabled={true}
      />
      <VenueCard
        label="Portfel nocny"
        sub="eToro · krypto/forex 24-7"
        accent="etoro"
        portfolio={etoro}
        enabled={etoroEnabled}
        mode={etoroMode}
      />
      {etoroEnabled && (
        <div className="portfolio-card portfolio-card-total">
          <div className="portfolio-card-head">
            <span className="portfolio-card-label">Razem</span>
            <span className="portfolio-card-sub">oba portfele</span>
          </div>
          <div className="portfolio-card-value">${total.toFixed(2)}</div>
        </div>
      )}
    </div>
  );
}
