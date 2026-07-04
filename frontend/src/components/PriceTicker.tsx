import { PortfolioSnapshot } from "../api/client";

interface TickerEntry {
  symbol: string;
  price: number;
  changePct: number | null;
}

function buildEntries(history: PortfolioSnapshot[], whitelist: string[]): TickerEntry[] {
  if (history.length === 0) {
    return whitelist.map((symbol) => ({ symbol, price: 0, changePct: null }));
  }
  const first = history[0];
  const last = history[history.length - 1];
  const firstPrices: Record<string, number> = JSON.parse(first.prices_json || "{}");
  const lastPrices: Record<string, number> = JSON.parse(last.prices_json || "{}");

  return whitelist.map((symbol) => {
    const price = lastPrices[symbol] ?? 0;
    const basePrice = firstPrices[symbol];
    const changePct = basePrice ? ((price - basePrice) / basePrice) * 100 : null;
    return { symbol, price, changePct };
  });
}

function fmtPrice(value: number): string {
  const decimals = value > 0 && value < 10 ? 4 : 2;
  return value.toLocaleString("pl-PL", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function PriceTicker({ history, whitelist }: { history: PortfolioSnapshot[]; whitelist: string[] }) {
  const entries = buildEntries(history, whitelist);
  if (entries.length === 0) return null;
  const track = [...entries, ...entries];

  return (
    <div className="ticker">
      <div className="ticker-track">
        {track.map((e, i) => (
          <div className="ticker-item" key={`${e.symbol}-${i}`}>
            <span className="ticker-symbol">{e.symbol.replace("USDT", "")}/USDT</span>
            <span className="ticker-price">${fmtPrice(e.price)}</span>
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
          </div>
        ))}
      </div>
    </div>
  );
}
