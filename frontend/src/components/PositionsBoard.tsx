import { useState } from "react";
import { api, isReadOnly, PortfolioResponse } from "../api/client";

type Leg = "us" | "crypto";

interface Pos {
  asset: string;
  leg: Leg;
  qty: number;
  entry: number | null;
  price: number | null;
  value: number;
  pnlPct: number | null;
  pnlUsd: number | null;
}

function money(v: number, min = 2, max = 2): string {
  return "$" + v.toLocaleString("pl-PL", { minimumFractionDigits: min, maximumFractionDigits: max });
}

function extract(portfolio: PortfolioResponse | null, leg: Leg): Pos[] {
  const cur = portfolio?.current;
  if (!cur) return [];
  const balances: Record<string, number> = JSON.parse(cur.balances_json || "{}");
  const prices: Record<string, number> = JSON.parse(cur.prices_json || "{}");
  const cost = portfolio?.cost_basis ?? {};
  const out: Pos[] = [];
  for (const [asset, qtyRaw] of Object.entries(balances)) {
    const qty = Number(qtyRaw);
    if (!(qty > 0)) continue;
    // balances are keyed by base asset ("BTC"); prices are keyed by the full
    // trading symbol ("BTCUSD") for crypto but by the plain ticker for equities
    // -- try both so crypto prices don't silently come back null.
    const price = prices[asset] ?? prices[asset + "USD"] ?? null;
    const value = price !== null ? qty * price : 0;
    if (value < 1) continue; // ignore unsellable dust
    const entry = cost[asset] ?? null;
    const pnlPct = price !== null && entry !== null && entry > 0 ? ((price - entry) / entry) * 100 : null;
    const pnlUsd = price !== null && entry !== null ? (price - entry) * qty : null;
    out.push({ asset, leg, qty, entry, price, value, pnlPct, pnlUsd });
  }
  return out;
}

function PositionCard({ p, onChanged }: { p: Pos; onChanged?: () => void }) {
  const up = (p.pnlPct ?? 0) >= 0;
  const legLabel = p.leg === "crypto" ? "Krypto" : "Akcje US";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Full symbol the backend expects: crypto is the pair ("BTCUSD"), equities the
  // plain ticker. venue follows the leg.
  const symbol = p.leg === "crypto" ? p.asset + "USD" : p.asset;
  const venue = p.leg === "crypto" ? "crypto" : "alpaca";
  const canSell = !isReadOnly && !!onChanged;

  async function sellAll() {
    if (!window.confirm(`Sprzedać CAŁĄ pozycję ${p.asset} (~${money(p.value)})? To realne zlecenie.`)) return;
    setBusy(true);
    setError(null);
    try {
      await api.sellAll(symbol, venue);
      onChanged?.();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={`pos-card pos-card-${p.leg}`}>
      <div className="pos-card-head">
        <span className={`venue-dot venue-dot-${p.leg === "crypto" ? "crypto" : "alpaca"}`} />
        <span className="pos-asset">{p.asset}</span>
        <span className="pos-leg-tag">{legLabel}</span>
        {p.pnlPct !== null ? (
          <span className={`pos-pnl-pct ${up ? "up" : "down"}`}>
            {up ? "+" : ""}
            {p.pnlPct.toFixed(2)}%
          </span>
        ) : (
          <span className="pos-pnl-pct muted">—</span>
        )}
      </div>
      <div className="pos-card-body">
        <div className="pos-metric">
          <span>Ilość</span>
          <b>{p.qty.toLocaleString("pl-PL", { maximumFractionDigits: 6 })}</b>
        </div>
        <div className="pos-metric">
          <span>Za ile → teraz</span>
          <b>
            {p.entry !== null ? money(p.entry) : "—"} → {p.price !== null ? money(p.price) : "—"}
          </b>
        </div>
        <div className="pos-metric">
          <span>Wartość</span>
          <b>{money(p.value)}</b>
        </div>
        <div className="pos-metric">
          <span>Zysk/strata</span>
          <b className={p.pnlUsd !== null ? (up ? "up" : "down") : ""}>
            {p.pnlUsd !== null ? `${p.pnlUsd >= 0 ? "+" : ""}${money(p.pnlUsd)}` : "—"}
          </b>
        </div>
      </div>
      {canSell && (
        <div className="pos-card-actions">
          <button className="btn-outline-danger pos-sell-all" disabled={busy} onClick={sellAll}>
            {busy ? "Sprzedaję…" : "Sprzedaj wszystko"}
          </button>
          {error && <span className="pos-sell-err">{error}</span>}
        </div>
      )}
    </div>
  );
}

/** One clean board of every open position across BOTH engines: what you own,
 *  in which leg, how much, at what price, and the live profit/loss. Each card
 *  can one-click sell the WHOLE position (exact held qty, no 'insufficient
 *  qty'); hidden in read-only view. */
export function PositionsBoard({
  alpaca,
  crypto,
  onChanged,
}: {
  alpaca: PortfolioResponse | null;
  crypto: PortfolioResponse | null;
  onChanged?: () => void;
}) {
  const positions = [...extract(alpaca, "us"), ...extract(crypto, "crypto")].sort((a, b) => b.value - a.value);
  const invested = positions.reduce((s, p) => s + p.value, 0);
  const pnl = positions.reduce((s, p) => s + (p.pnlUsd ?? 0), 0);
  const hasPnl = positions.some((p) => p.pnlUsd !== null);
  const up = pnl >= 0;

  return (
    <div className="panel pos-board">
      <div className="pos-board-head">
        <h2>Pozycje — w co inwestujesz</h2>
        {positions.length > 0 && (
          <div className="pos-board-summary">
            <span className="pos-board-stat">
              <span className="pos-board-stat-label">Zainwestowane</span>
              <b>{money(invested)}</b>
            </span>
            {hasPnl && (
              <span className="pos-board-stat">
                <span className="pos-board-stat-label">Zysk/strata</span>
                <b className={up ? "up" : "down"}>
                  {up ? "+" : ""}
                  {money(pnl)}
                </b>
              </span>
            )}
          </div>
        )}
      </div>
      {positions.length > 0 ? (
        <div className="pos-grid">
          {positions.map((p) => (
            <PositionCard key={`${p.leg}-${p.asset}`} p={p} onChanged={onChanged} />
          ))}
        </div>
      ) : (
        <p className="subtitle" style={{ margin: 0 }}>
          Brak otwartych pozycji — cała gotówka konta czeka na wejścia. Gdy silnik kupi, pozycje pojawią się tutaj z
          ceną wejścia i bieżącym zyskiem.
        </p>
      )}
    </div>
  );
}
