import { PortfolioSnapshot } from "../api/client";

interface TickerEntry {
  symbol: string;
  price: number | null;
  changePct: number | null;
  sparkline: number[];
  unavailable: boolean;
}

function priceFor(snapshot: PortfolioSnapshot, symbol: string): number | null {
  const prices: Record<string, number> = JSON.parse(snapshot.prices_json || "{}");
  const value = prices[symbol];
  return typeof value === "number" && value > 0 ? value : null;
}

function buildEntries(history: PortfolioSnapshot[], whitelist: string[]): TickerEntry[] {
  return whitelist.map((symbol) => {
    // Scan from newest to oldest so a symbol added to the whitelist after
    // older snapshots were recorded (which don't have its price yet) still
    // resolves to its most recent real value instead of showing $0.00.
    let price: number | null = null;
    for (let i = history.length - 1; i >= 0; i--) {
      price = priceFor(history[i], symbol);
      if (price !== null) break;
    }

    let basePrice: number | null = null;
    for (let i = 0; i < history.length; i++) {
      basePrice = priceFor(history[i], symbol);
      if (basePrice !== null) break;
    }

    const changePct = price !== null && basePrice !== null ? ((price - basePrice) / basePrice) * 100 : null;

    const sparkline = history
      .map((h) => priceFor(h, symbol))
      .filter((v): v is number => v !== null)
      .slice(-30);

    // Only the most recent cycle's failure list matters -- a symbol that
    // failed once but recovered shouldn't stay flagged as unavailable.
    const latest = history[history.length - 1];
    const latestFailed: string[] = latest ? JSON.parse(latest.failed_symbols_json || "[]") : [];
    const unavailable = price === null && latestFailed.includes(symbol);

    return { symbol, price, changePct, sparkline, unavailable };
  });
}

function fmtPrice(value: number): string {
  const decimals = value > 0 && value < 10 ? 4 : 2;
  return value.toLocaleString("pl-PL", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function Sparkline({ values, up }: { values: number[]; up: boolean }) {
  if (values.length < 2) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 46;
  const h = 16;
  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="ticker-sparkline" aria-hidden="true">
      <polyline points={points} fill="none" stroke={up ? "var(--green)" : "var(--red)"} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export function PriceTicker({ history, whitelist }: { history: PortfolioSnapshot[]; whitelist: string[] }) {
  if (whitelist.length === 0) return null;
  const entries = buildEntries(history, whitelist);
  const track = [...entries, ...entries];

  return (
    <div className="ticker-scroll">
      <div className="ticker-track">
        {track.map((e, i) => (
          <div className="ticker-item" key={`${e.symbol}-${i}`}>
            <span className="ticker-symbol">{e.symbol}</span>
            {e.price !== null ? (
              <>
                <span className={`ticker-price ${e.changePct !== null ? (e.changePct >= 0 ? "up" : "down") : ""}`}>
                  ${fmtPrice(e.price)}
                </span>
                {e.sparkline.length >= 2 && <Sparkline values={e.sparkline} up={(e.changePct ?? 0) >= 0} />}
                {e.changePct !== null && (
                  <span className={`ticker-change ${e.changePct >= 0 ? "up" : "down"}`}>
                    <svg width="9" height="9" viewBox="0 0 10 10" aria-hidden="true">
                      {e.changePct >= 0 ? (
                        <path d="M5 1 L9 8 L1 8 Z" fill="currentColor" />
                      ) : (
                        <path d="M5 9 L1 2 L9 2 Z" fill="currentColor" />
                      )}
                    </svg>
                    {Math.abs(e.changePct).toFixed(2)}%
                  </span>
                )}
              </>
            ) : e.unavailable ? (
              <span className="ticker-price ticker-price-unavailable" title="Alpaca nie zwróciła ceny dla tego tickera w tym cyklu -- tymczasowo pominięty.">
                niedostępne na Alpaca
              </span>
            ) : (
              <span className="ticker-price ticker-price-pending">oczekiwanie na dane…</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
