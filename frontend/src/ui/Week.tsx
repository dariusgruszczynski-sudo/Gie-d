import { useEffect, useState } from "react";
import { api, HistoryTrade, StatusResponse } from "../api/client";
import { money, money0 } from "./kit";

/* EKRAN TYDZIEŃ (paczka D) — proste podsumowanie ostatnich 7 dni na telefon:
   ile bot zarobił, ile transakcji, najlepsza/najgorsza, dzień po dniu. Liczone
   z Historii (tylko akcje sesji), plus aktualny stan konta ze statusu. */
export function Week({ status }: { status: StatusResponse | null }) {
  const [trades, setTrades] = useState<HistoryTrade[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let dead = false;
    (async () => {
      try { const r = await api.history(); if (!dead) setTrades(r.trades.filter((t) => (t.venue ?? "alpaca") === "alpaca")); }
      catch (e) { if (!dead) setErr(String(e)); }
    })();
    return () => { dead = true; };
  }, []);

  const now = Date.now();
  const week = (trades ?? []).filter((t) => t.sold_at && now - Date.parse(t.sold_at) <= 7 * 86400000);
  const wins = week.filter((t) => t.pnl_usd >= 0);
  const losses = week.filter((t) => t.pnl_usd < 0);
  const total = week.reduce((s, t) => s + t.pnl_usd, 0);
  const best = week.reduce<HistoryTrade | null>((b, t) => (b === null || t.pnl_usd > b.pnl_usd ? t : b), null);
  const worst = week.reduce<HistoryTrade | null>((w, t) => (w === null || t.pnl_usd < w.pnl_usd ? t : w), null);
  const winRate = week.length ? Math.round((wins.length / week.length) * 100) : null;

  // Dzień po dniu (ostatnie 7 dni, dziś po prawej).
  const days: Array<{ label: string; pnl: number; n: number }> = [];
  const dow = ["Nd", "Pn", "Wt", "Śr", "Cz", "Pt", "Sb"];
  for (let d = 6; d >= 0; d--) {
    const day = new Date(now - d * 86400000);
    const key = day.toDateString();
    const dayTrades = week.filter((t) => t.sold_at && new Date(Date.parse(t.sold_at)).toDateString() === key);
    days.push({ label: dow[day.getDay()], pnl: dayTrades.reduce((s, t) => s + t.pnl_usd, 0), n: dayTrades.length });
  }
  const maxAbs = Math.max(1, ...days.map((d) => Math.abs(d.pnl)));
  const acc = status?.account;

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Tydzień · ostatnie 7 dni</span>
        <span className="gd-mode"><span className="gd-blip" />{week.length} transakcji</span>
      </div>
      {err && <div className="gd-ribbon">{err}</div>}

      {/* HERO tygodnia */}
      <div className="gd-hero">
        <div className="gd-hero-label">📅 W tym tygodniu bot {total >= 0 ? "zarobił" : "stracił"}</div>
        <div className={`gd-hero-val ${total >= 0 ? "gd-up" : "gd-down"}`}>{total >= 0 ? "+" : ""}{money(total)}</div>
        <div className="gd-hero-sub">
          {week.length} {week.length === 1 ? "transakcja" : "transakcji"}
          {winRate !== null && <> · skuteczność <b>{winRate}%</b> ({wins.length} plus / {losses.length} minus)</>}
        </div>
      </div>

      {/* Dzień po dniu */}
      <div className="gd-sec"><h3>Dzień po dniu</h3><span className="gd-sec-note">zysk każdego dnia</span></div>
      <div className="gd-weekbars">
        {days.map((d, i) => {
          const h = Math.round((Math.abs(d.pnl) / maxAbs) * 46);
          const up = d.pnl >= 0;
          return (
            <div className="gd-weekbar" key={i}>
              <span className="gd-weekbar-v" style={{ color: d.n ? (up ? "var(--mint)" : "var(--rose)") : "var(--dim-2)" }}>
                {d.n ? `${up ? "+" : "−"}${money0(Math.abs(d.pnl)).replace("$", "$")}` : "—"}
              </span>
              <div className="gd-weekbar-col">
                <i className={up ? "up" : "down"} style={{ height: `${d.n ? Math.max(4, h) : 2}px` }} />
              </div>
              <span className="gd-weekbar-l">{d.label}</span>
            </div>
          );
        })}
      </div>

      {/* Najlepsza / najgorsza */}
      {week.length > 0 && (
        <div className="gd-statgrid" style={{ marginTop: 18 }}>
          <div className="gd-stat up">
            <span className="gd-stat-l">🏆 Najlepsza</span>
            <b className="gd-stat-v gd-up">{best ? `+${money(best.pnl_usd)}` : "—"}</b>
            <span className="gd-stat-sub">{best ? best.symbol : ""}</span>
          </div>
          <div className="gd-stat down">
            <span className="gd-stat-l">💧 Najgorsza</span>
            <b className="gd-stat-v gd-down">{worst && worst.pnl_usd < 0 ? money(worst.pnl_usd) : "—"}</b>
            <span className="gd-stat-sub">{worst && worst.pnl_usd < 0 ? worst.symbol : "brak strat 🎉"}</span>
          </div>
        </div>
      )}

      {/* Stan konta teraz */}
      <div className="gd-sec"><h3>Konto teraz</h3><span className="gd-sec-note">stan na dziś</span></div>
      <div className="gd-statgrid gd-statgrid-3">
        <div className="gd-stat neu"><span className="gd-stat-l">Na koncie</span><b className="gd-stat-v">{acc ? money0(acc.total_value) : "…"}</b></div>
        <div className="gd-stat neu"><span className="gd-stat-l">W akcjach</span><b className="gd-stat-v">{acc ? money0((acc.equity_positions_value ?? 0) + (acc.extended_positions_value ?? 0)) : "…"}</b></div>
        <div className="gd-stat neu"><span className="gd-stat-l">Gotówka</span><b className="gd-stat-v">{acc ? money0(acc.cash) : "…"}</b></div>
      </div>

      {!trades && <p className="gd-empty">Wczytuję tydzień…</p>}
      {trades && week.length === 0 && <p className="gd-empty">W tym tygodniu żadnej zamkniętej transakcji.</p>}
    </div>
  );
}
