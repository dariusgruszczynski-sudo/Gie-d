import { useEffect, useState } from "react";
import { api, HistoryResponse, HistoryTrade } from "../api/client";
import { ago, money, pct } from "./kit";

/* ===== AUDYT STRATEGII =====================================================
   Liczy wynik zamkniętych transakcji w oknach 7 dni / 30 dni / całość i sam
   wypisuje wnioski po ludzku — w tym KLUCZOWE „czy zyski są trzymane dłużej niż
   straty" (obawa właściciela). Wszystko z danych, które apka już ma. */
interface Stat {
  n: number; wins: number; winRate: number | null; pnl: number;
  holdWin: number | null; holdLoss: number | null; worst: HistoryTrade | null;
}
function statsOf(ts: HistoryTrade[]): Stat {
  const wins = ts.filter((t) => t.pnl_usd >= 0);
  const losses = ts.filter((t) => t.pnl_usd < 0);
  const avg = (a: number[]) => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : null);
  const holdOf = (set: HistoryTrade[]) => avg(set.map((t) => t.days_held).filter((d): d is number => d !== null));
  return {
    n: ts.length,
    wins: wins.length,
    winRate: ts.length ? (wins.length / ts.length) * 100 : null,
    pnl: ts.reduce((s, t) => s + t.pnl_usd, 0),
    holdWin: holdOf(wins),
    holdLoss: holdOf(losses),
    worst: ts.reduce<HistoryTrade | null>((w, t) => (w === null || t.pnl_usd < w.pnl_usd ? t : w), null),
  };
}
function fmtDays(d: number | null): string {
  if (d === null) return "—";
  return d < 1 ? "<1 dnia" : d < 1.5 ? "~1 dzień" : `~${Math.round(d)} dni`;
}

function AuditCard({ trades }: { trades: HistoryTrade[] }) {
  const now = Date.now();
  const daysAgo = (t: HistoryTrade) => (t.sold_at ? (now - Date.parse(t.sold_at)) / 86400000 : Infinity);
  const recent = trades.filter((t) => daysAgo(t) <= 7);          // ostatni tydzień
  const midPrior = trades.filter((t) => daysAgo(t) > 7 && daysAgo(t) <= 30); // 8–30 dni (do trendu)
  const last30 = trades.filter((t) => daysAgo(t) <= 30);
  const r = statsOf(recent), p = statsOf(midPrior), m = statsOf(last30), a = statsOf(trades);

  // ---- WNIOSKI (po ludzku) ----
  const notes: Array<{ t: string; tone: "good" | "bad" | "neu" }> = [];
  if (a.n < 3) {
    notes.push({ t: `Za mało zamkniętych transakcji (${a.n}), żeby wyciągać mocne wnioski — bot dopiero zbiera próbkę.`, tone: "neu" });
  } else {
    // 1) Trend skuteczności: ostatni tydzień vs wcześniej
    if (r.n >= 2 && p.winRate !== null && r.winRate !== null) {
      const diff = r.winRate - p.winRate;
      notes.push({
        t: `Skuteczność 7 dni: ${Math.round(r.winRate)}% vs ${Math.round(p.winRate)}% wcześniej — ${diff >= 5 ? "rośnie" : diff <= -5 ? "spada" : "bez zmian"}.`,
        tone: diff >= 5 ? "good" : diff <= -5 ? "bad" : "neu",
      });
    }
    // 2) KLUCZOWE: czy zyski trzymane dłużej niż straty
    if (a.holdWin !== null && a.holdLoss !== null) {
      if (a.holdWin > a.holdLoss + 0.5) {
        notes.push({ t: `⚠ Zyskowne trzymane dłużej (${fmtDays(a.holdWin)}) niż stratne (${fmtDays(a.holdLoss)}) — automat wciąż zwleka z realizacją zysków.`, tone: "bad" });
      } else if (a.holdLoss > a.holdWin + 0.5) {
        notes.push({ t: `Straty trzymane dłużej (${fmtDays(a.holdLoss)}) niż zyski (${fmtDays(a.holdWin)}) — warto szybciej ciąć przegrane.`, tone: "bad" });
      } else {
        notes.push({ t: `Czas trzymania zysków (${fmtDays(a.holdWin)}) i strat (${fmtDays(a.holdLoss)}) podobny — bez patologii „siedzenia na zysku".`, tone: "good" });
      }
    }
    // 3) Wynik ostatniego tygodnia
    if (r.n >= 1) {
      notes.push({ t: `Ostatnie 7 dni: ${r.pnl >= 0 ? "+" : ""}${money(r.pnl)} z ${r.n} ${r.n === 1 ? "zamknięcia" : "zamknięć"}.`, tone: r.pnl >= 0 ? "good" : "bad" });
    }
    // 4) Największy przeciek
    if (a.worst && a.worst.pnl_usd < 0) {
      notes.push({ t: `Największa strata: ${a.worst.symbol} (${money(a.worst.pnl_usd)}) — sprawdź, czy to nie powtarzalny przeciek.`, tone: "neu" });
    }
  }

  const Col = ({ label, s }: { label: string; s: Stat }) => (
    <div className="gd-audit-col">
      <div className="gd-audit-col-h">{label}</div>
      <div className="gd-audit-metric"><i>skuteczność</i><b>{s.winRate === null ? "—" : `${Math.round(s.winRate)}%`}</b></div>
      <div className="gd-audit-metric"><i>zysk</i><b className={s.pnl >= 0 ? "gd-up" : "gd-down"}>{s.n ? `${s.pnl >= 0 ? "+" : ""}${money(s.pnl)}` : "—"}</b></div>
      <div className="gd-audit-metric"><i>zamknięć</i><b>{s.n}</b></div>
    </div>
  );

  return (
    <div className="gd-audit">
      <div className="gd-audit-head">
        <span className="gd-audit-title">◈ Audyt strategii</span>
        <span className="gd-audit-note">od zmiany na progresywne wejścia + realizację zysku</span>
      </div>
      <div className="gd-audit-cols">
        <Col label="Ostatnie 7 dni" s={r} />
        <Col label="30 dni" s={m} />
        <Col label="Całość" s={a} />
      </div>
      <ul className="gd-audit-notes">
        {notes.map((n, i) => <li key={i} className={`t-${n.tone}`}>{n.t}</li>)}
      </ul>
    </div>
  );
}

/* EKRAN HISTORIA — lista zamkniętych transakcji po ludzku:
   „kupiłem X po $a → sprzedałem po $b → zarobiłem $z". Najnowsze na górze. */
function Row({ t }: { t: HistoryTrade }) {
  const up = t.pnl_usd >= 0;
  const qtyStr = t.qty.toLocaleString("pl-PL", { maximumFractionDigits: 4 });
  const daysStr = t.days_held === null ? null : t.days_held === 0 ? "tego samego dnia" : t.days_held === 1 ? "1 dzień" : `${t.days_held} dni`;
  return (
    <div className={`gd-hist ${up ? "up" : "down"}`}>
      <div className="gd-hist-l">
        <div className="gd-hist-top">
          <b className="gd-hist-sym">{t.symbol}</b>
          <span className="gd-hist-qty">{qtyStr} szt.</span>
          {daysStr && <span className="gd-hist-days">· trzymane {daysStr}</span>}
        </div>
        <div className="gd-hist-flow">
          <span className="gd-hist-leg">kupno <b>{money(t.avg_buy_price)}</b></span>
          <span className="gd-hist-arrow">→</span>
          <span className="gd-hist-leg">sprzedaż <b>{money(t.sell_price)}</b></span>
          <span className="gd-hist-when">{t.sold_at ? ago(t.sold_at) : ""}</span>
        </div>
      </div>
      <div className="gd-hist-r">
        <span className={`gd-hist-pnl ${up ? "gd-up" : "gd-down"}`}>{up ? "+" : ""}{money(t.pnl_usd)}</span>
        <span className={`gd-hist-pct ${up ? "gd-up" : "gd-down"}`}>{t.pnl_pct !== null ? pct(t.pnl_pct) : "—"}</span>
      </div>
    </div>
  );
}

export function History() {
  const [data, setData] = useState<HistoryResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    try { setData(await api.history()); setErr(null); } catch (e) { setErr(String(e)); }
  }
  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  const s = data?.summary;
  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Historia · zamknięte transakcje</span>
        {s && <span className="gd-mode"><span className="gd-blip" />{s.count} zamknięć</span>}
      </div>
      {err && <div className="gd-ribbon">{err}</div>}

      {data && data.trades.length > 0 && <AuditCard trades={data.trades} />}

      {s && s.count > 0 && (
        <div className="gd-posbar">
          <div className="gd-posbar-i"><b className={s.total_pnl_usd >= 0 ? "gd-up" : "gd-down"}>{s.total_pnl_usd >= 0 ? "+" : ""}{money(s.total_pnl_usd)}</b><small>łączny zysk</small></div>
          <div className="gd-posbar-sep" />
          <div className="gd-posbar-i"><b className="gd-up">{s.wins}</b><small>na plus</small></div>
          <div className="gd-posbar-sep" />
          <div className="gd-posbar-i"><b className="gd-down">{s.losses}</b><small>na minus</small></div>
          <div className="gd-posbar-sep" />
          <div className="gd-posbar-i"><b>{s.best ? s.best.symbol : "—"}</b><small>najlepsza {s.best ? `+${money(s.best.pnl_usd)}` : ""}</small></div>
        </div>
      )}

      {!data ? (
        <p className="gd-empty">Wczytuję historię…</p>
      ) : data.trades.length === 0 ? (
        <p className="gd-empty">Jeszcze żadnej zamkniętej transakcji — historia pojawi się po pierwszej sprzedaży.</p>
      ) : (
        <div className="gd-histlist">
          {data.trades.map((t, i) => <Row key={`${t.symbol}-${t.sold_at}-${i}`} t={t} />)}
        </div>
      )}
    </div>
  );
}
