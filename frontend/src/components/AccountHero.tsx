import { StatusResponse } from "../api/client";
import { useCountUp } from "../hooks/useCountUp";
import { MarketTemperature } from "./MarketTemperature";

function fmt(v: number): string {
  return v.toLocaleString("pl-PL", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function PnlPill({ label, value }: { label: string; value: number | null }) {
  if (value === null) return null;
  const up = value >= 0;
  return (
    <span className={`hero-pnl ${up ? "up" : "down"}`}>
      <span className="hero-pnl-arrow">{up ? "▲" : "▼"}</span>
      {up ? "+" : ""}
      {value.toFixed(2)}%<span className="hero-pnl-label">{label}</span>
    </span>
  );
}

function EngineDot({ dot, name, statusText, tone }: { dot: string; name: string; statusText: string; tone: string }) {
  return (
    <span className={`hero-engine hero-engine-${tone}`}>
      <span className={`venue-dot venue-dot-${dot}`} />
      <span className="hero-engine-name">{name}</span>
      <span className="hero-engine-status">{statusText}</span>
    </span>
  );
}

/** The single most-important glance: how much you have, how it's moving, the
 *  market read, and whether the two engines are live. Everything else lives on
 *  the detail tabs. */
export function AccountHero({ status }: { status: StatusResponse }) {
  const account = status.account;
  const total = useCountUp(account?.total_value ?? 0);
  const netUp = status.net_result_usd >= 0;

  const usTone = status.is_halted ? "halt" : status.is_paused ? "paused" : "live";
  const usText = status.is_halted ? "HALT" : status.is_paused ? "STOP" : "aktywny";
  const extTone = !status.extended_enabled ? "off" : status.extended_paused ? "paused" : "live";
  const extText = !status.extended_enabled ? "wył." : status.extended_paused ? "STOP" : "aktywny";

  return (
    <div className="hero panel">
      <div className="hero-glow" aria-hidden="true" />
      <div className="hero-body">
        <div className="hero-top">
          <span className="hero-label">Wartość konta</span>
          <MarketTemperature us={status.market_regime} extended={status.extended_market_regime} />
        </div>

        <div className="hero-value">
          {account ? `$${fmt(total)}` : <span className="hero-pending">oczekiwanie na dane…</span>}
        </div>

        <div className="hero-pnls">
          <PnlPill label="dziś" value={status.day_pnl_pct} />
          <PnlPill label="tydzień" value={status.week_pnl_pct} />
          <span className={`hero-net ${netUp ? "up" : "down"}`}>
            netto {netUp ? "+" : "−"}${fmt(Math.abs(status.net_result_usd))}
          </span>
        </div>

        {account && (
          <div className="hero-split">
            <span className="hero-chip">
              <span className="hero-chip-label">Wolna gotówka</span>
              <b>${fmt(account.cash)}</b>
            </span>
            <span className="hero-chip">
              <span className="venue-dot venue-dot-alpaca" />
              <span className="hero-chip-label">SESJA</span>
              <b>${fmt(account.equity_positions_value)}</b>
            </span>
            <span className="hero-chip">
              <span className="venue-dot venue-dot-extended" />
              <span className="hero-chip-label">POZA SESJĄ</span>
              <b>${fmt(account.extended_positions_value)}</b>
            </span>
          </div>
        )}

        <div className="hero-engines">
          <EngineDot dot="alpaca" name="SESJA" statusText={usText} tone={usTone} />
          <EngineDot dot="extended" name="POZA SESJĄ" statusText={extText} tone={extTone} />
          {status.is_halted && status.halted_reason && (
            <span className="hero-halt-reason">⛔ {status.halted_reason}</span>
          )}
        </div>
      </div>
    </div>
  );
}
