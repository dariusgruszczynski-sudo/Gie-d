import { useEffect, useState } from "react";
import { api, isReadOnly, PortfolioResponse } from "../api/client";

type Leg = "us" | "extended";

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
    // Both legs are US equities/ETFs now -- prices are keyed by the plain ticker.
    const price = prices[asset] ?? null;
    const value = price !== null ? qty * price : 0;
    if (value < 1) continue; // ignore unsellable dust
    const entry = cost[asset] ?? null;
    const pnlPct = price !== null && entry !== null && entry > 0 ? ((price - entry) / entry) * 100 : null;
    const pnlUsd = price !== null && entry !== null ? (price - entry) * qty : null;
    out.push({ asset, leg, qty, entry, price, value, pnlPct, pnlUsd });
  }
  return out;
}

function PositionCard({ p, note, onChanged }: { p: Pos; note?: string; onChanged?: () => void }) {
  const up = (p.pnlPct ?? 0) >= 0;
  const legLabel = p.leg === "extended" ? "Poza sesją" : "Akcje US";
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Both legs trade plain US tickers; venue follows the leg.
  const symbol = p.asset;
  const venue = p.leg === "extended" ? "extended" : "alpaca";
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
        <span className={`venue-dot venue-dot-${p.leg === "extended" ? "extended" : "alpaca"}`} />
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
      {note && (
        <div className="pos-plan">
          <span className="pos-plan-label">Co robię</span>
          <span className="pos-plan-note">{note}</span>
        </div>
      )}
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
  extended,
  onChanged,
}: {
  alpaca: PortfolioResponse | null;
  extended: PortfolioResponse | null;
  onChanged?: () => void;
}) {
  const positions = [...extract(alpaca, "us"), ...extract(extended, "extended")].sort((a, b) => b.value - a.value);
  const invested = positions.reduce((s, p) => s + p.value, 0);
  const pnl = positions.reduce((s, p) => s + (p.pnlUsd ?? 0), 0);
  const hasPnl = positions.some((p) => p.pnlUsd !== null);
  const up = pnl >= 0;

  // Per-position "co robię" notes: the mechanical exit plan per held symbol,
  // keyed by `${leg}:${asset}`. Fetched read-only; refreshes when holdings change.
  const [notes, setNotes] = useState<Record<string, string>>({});
  const hasAlpaca = !!alpaca?.current;
  const hasExtended = !!extended?.current;
  useEffect(() => {
    let cancelled = false;
    async function load() {
      const map: Record<string, string> = {};
      const legs: Array<["us" | "extended", string]> = [];
      if (hasAlpaca) legs.push(["us", "alpaca"]);
      if (hasExtended) legs.push(["extended", "extended"]);
      await Promise.all(
        legs.map(async ([leg, venue]) => {
          try {
            const res = await api.positionPlans(venue);
            res.positions.forEach((pp) => (map[`${leg}:${pp.asset}`] = pp.note));
          } catch {
            /* plan is best-effort context; ignore failures */
          }
        }),
      );
      if (!cancelled) setNotes(map);
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [hasAlpaca, hasExtended, invested]);

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
            <PositionCard key={`${p.leg}-${p.asset}`} p={p} note={notes[`${p.leg}:${p.asset}`]} onChanged={onChanged} />
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
