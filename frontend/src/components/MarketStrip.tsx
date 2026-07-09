import { useEffect, useState } from "react";
import { MarketSession, Scorecard as ScorecardData, SessionBounds } from "../api/client";

// Jeden scalony pasek u góry: status sesji + zegar (kompaktowo) po lewej,
// wynik vs benchmark (alpha) po prawej. Zastępuje dwa duże panele
// (Zegar sesji + Wynik vs SPY), które nie mieściły się w nowym layoucie.

const WARSAW_TZ = "Europe/Warsaw";
const NY_TZ = "America/New_York";

const SESSION_LABELS: Record<string, { label: string; className: string }> = {
  closed: { label: "GIEŁDA ZAMKNIĘTA", className: "session-badge-closed" },
  regular: { label: "SESJA OTWARTA", className: "session-badge-regular" },
};

function fmtTime(date: Date, tz: string): string {
  return date.toLocaleTimeString("pl-PL", { timeZone: tz, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function fmtBoundary(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("pl-PL", { timeZone: WARSAW_TZ, hour: "2-digit", minute: "2-digit" });
}

function fmtAgo(iso: string, now: Date): string {
  const mins = Math.max(0, Math.round((now.getTime() - new Date(iso).getTime()) / 60000));
  if (mins < 1) return "przed chwilą";
  if (mins === 1) return "1 min temu";
  if (mins < 60) return `${mins} min temu`;
  const hours = Math.floor(mins / 60);
  return `${hours} h ${mins % 60} min temu`;
}

function fmtUsd(v: number): string {
  const sign = v >= 0 ? "+" : "−";
  return `${sign}$${Math.abs(v).toFixed(2)}`;
}

function fmtPct(v: number): string {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

export function MarketStrip({
  session,
  bounds,
  lastCycleAt,
  pollIntervalMinutes,
  scorecard,
}: {
  session: MarketSession;
  bounds: SessionBounds | null;
  lastCycleAt: string | null;
  pollIntervalMinutes: number;
  scorecard: ScorecardData | null;
}) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const sessionInfo = session ? SESSION_LABELS[session] : null;
  const isOpen = session === "regular";

  const hasAlpha = scorecard && scorecard.alpha_pct !== null && scorecard.alpha_usd !== null;
  const beating = (scorecard?.alpha_pct ?? 0) >= 0;

  return (
    <div className={`market-strip ${isOpen ? "market-strip-open" : ""}`}>
      <div className="market-strip-sweep" aria-hidden="true" />

      {/* --- Lewa strona: sesja + zegar --- */}
      <div className="market-strip-cluster">
        {sessionInfo && (
          <span className={`session-badge ${sessionInfo.className} ${isOpen ? "session-badge-pulse" : ""}`}>
            {sessionInfo.label}
          </span>
        )}
        <div className="market-strip-clock">
          <div className="market-strip-clock-item">
            <span className="market-strip-tz">Warszawa</span>
            <span className="market-strip-time">{fmtTime(now, WARSAW_TZ)}</span>
          </div>
          <div className="market-strip-clock-item">
            <span className="market-strip-tz">Nowy Jork</span>
            <span className="market-strip-time">{fmtTime(now, NY_TZ)}</span>
          </div>
          {bounds && (
            <div className="market-strip-clock-item market-strip-schedule">
              <span className="market-strip-tz">Sesja US (PL)</span>
              <span className="market-strip-time-sm">
                {fmtBoundary(bounds.regular_open)}–{fmtBoundary(bounds.regular_close)}
              </span>
            </div>
          )}
        </div>
        {lastCycleAt && (
          <span className="market-strip-cycle">
            <span className="market-strip-cycle-dot" />
            cykl {fmtAgo(lastCycleAt, now)} · co {pollIntervalMinutes} min
          </span>
        )}
      </div>

      {/* --- Prawa strona: wynik vs benchmark (alpha) --- */}
      {scorecard && (
        <div className="market-strip-cluster market-strip-alpha">
          {hasAlpha && (
            <span className={`session-badge ${beating ? "session-badge-regular" : "session-badge-closed"}`}>
              {beating ? "▲ BIJESZ RYNEK" : "▼ PONIŻEJ RYNKU"}
            </span>
          )}
          <div className="market-strip-figs">
            <div className="market-strip-fig">
              <span className="market-strip-fig-label">Portfel</span>
              <strong>${scorecard.portfolio_value.toFixed(2)}</strong>
            </div>
            <div className="market-strip-fig">
              <span className="market-strip-fig-label">vs {scorecard.benchmark_symbol}</span>
              <strong className={hasAlpha ? (beating ? "up" : "down") : ""}>
                {hasAlpha ? fmtPct(scorecard.alpha_pct!) : "—"}
              </strong>
            </div>
            <div className="market-strip-fig">
              <span className="market-strip-fig-label">Alpha $</span>
              <strong className={hasAlpha ? (beating ? "up" : "down") : ""}>
                {hasAlpha ? fmtUsd(scorecard.alpha_usd!) : "—"}
              </strong>
            </div>
            <div className="market-strip-fig">
              <span className="market-strip-fig-label">Zreal. P&L</span>
              <strong className={scorecard.realized_pnl_usd >= 0 ? "up" : "down"}>
                {fmtUsd(scorecard.realized_pnl_usd)}
              </strong>
            </div>
            <div className="market-strip-fig">
              <span className="market-strip-fig-label">Trafność</span>
              <strong>
                {scorecard.win_rate_pct !== null ? `${scorecard.win_rate_pct.toFixed(0)}%` : "—"}
                <span className="market-strip-fig-sub">
                  {" "}
                  ({scorecard.wins}W/{scorecard.losses}L)
                </span>
              </strong>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
