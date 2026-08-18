import { useEffect, useState } from "react";
import { api, AuditResponse, HistoryResponse, HistoryTrade, StatusResponse } from "../api/client";
import { ago, money, pct } from "./kit";

/* Głęboki audyt (to co diag: przecieki per symbol, wejścia vs limit,
   odrzucenia, ustawienia). Lazy-fetch z /api/audit; chowa się jak nie ma. */
function AuditDetails() {
  const [d, setD] = useState<AuditResponse | null>(null);
  const [open, setOpen] = useState(false);
  const [tried, setTried] = useState(false);
  async function toggle() {
    const next = !open; setOpen(next);
    if (next && !d && !tried) {
      setTried(true);
      try { setD(await api.audit()); } catch { /* endpoint może jeszcze nie być wdrożony */ }
    }
  }
  const maxDay = d ? Math.max(1, ...d.entries.per_day.map((x) => x.n), d.entries.cap) : 1;
  return (
    <div className="gd-audit-deep">
      <button className="gd-audit-toggle" onClick={toggle}>{open ? "ukryj szczegóły ▲" : "szczegóły: przecieki · wejścia · odrzucenia ▾"}</button>
      {open && (!d ? <p className="gd-empty" style={{ margin: "8px 0" }}>Liczę szczegóły…</p> : (
        <div className="gd-audit-deepgrid">
          <div className="gd-audit-block">
            <h5>Które nazwy krwawią</h5>
            {d.per_symbol.slice(0, 6).map((s) => (
              <div key={s.symbol} className="gd-audit-row">
                <span>{s.symbol}</span>
                <span className={s.pnl_usd >= 0 ? "gd-up" : "gd-down"}>{s.pnl_usd >= 0 ? "+" : ""}{money(s.pnl_usd)}</span>
                <span className="gd-audit-mut">{s.closed} zamk.{s.win_rate !== null ? ` · ${s.win_rate}%` : ""}</span>
              </div>
            ))}
          </div>
          <div className="gd-audit-block">
            <h5>Wejścia dziennie vs limit ({d.entries.cap}/dzień)</h5>
            {d.entries.per_day.slice(-8).map((x) => (
              <div key={x.date} className="gd-audit-bar">
                <span className="gd-audit-mut">{x.date.slice(5)}</span>
                <span className="gd-audit-track"><i style={{ width: `${(x.n / maxDay) * 100}%`, background: x.n >= d.entries.cap ? "var(--rose)" : "var(--brand)" }} /></span>
                <b>{x.n}</b>
              </div>
            ))}
            <div className="gd-audit-mut" style={{ marginTop: 6 }}>
              {d.entries.binds ? `Limit osiągany w ${d.entries.days_at_limit} dni — hamuje.` : `Limit nigdy nie osiągnięty (max ${d.entries.max_in_day}) — nie hamuje.`}
            </div>
          </div>
          <div className="gd-audit-block">
            <h5>Czemu tyle wejść (300 decyzji)</h5>
            <div className="gd-audit-mut" style={{ marginBottom: 6 }}>Odrzuconych mimo sygnału: <b style={{ color: "var(--txt)" }}>{d.decisions.rejected}</b></div>
            {d.decisions.reasons.slice(0, 5).map((r, i) => (
              <div key={i} className="gd-audit-row"><span className="gd-audit-mut" style={{ flex: 1 }}>{r.reason}</span><b>{r.n}×</b></div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

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

function AuditCard({ trades, epoch }: { trades: HistoryTrade[]; epoch?: string | null }) {
  const now = Date.now();
  const daysAgo = (t: HistoryTrade) => (t.sold_at ? (now - Date.parse(t.sold_at)) / 86400000 : Infinity);
  const recent = trades.filter((t) => daysAgo(t) <= 7);          // ostatni tydzień
  const midPrior = trades.filter((t) => daysAgo(t) > 7 && daysAgo(t) <= 30); // 8–30 dni (do trendu)
  const last30 = trades.filter((t) => daysAgo(t) <= 30);
  // „Od resetu" (Świeży start) — jeśli ustawiony, trzecia kolumna i edge liczą
  // się od tego momentu, żeby stara epoka nie zaniżała obrazu nowej strategii.
  const epochMs = epoch ? Date.parse(epoch) : NaN;
  const sinceTrades = Number.isFinite(epochMs)
    ? trades.filter((t) => t.sold_at && Date.parse(t.sold_at) >= epochMs)
    : trades;
  const r = statsOf(recent), p = statsOf(midPrior), m = statsOf(last30), a = statsOf(sinceTrades);
  const totalLabel = Number.isFinite(epochMs) ? "Od resetu" : "Całość";

  // ---- EDGE: ile ŚREDNIO zarabia wygrana vs traci strata + na 1 transakcję ----
  // Najważniejsza liczba przy niskiej trafności — zysk bierze się z asymetrii.
  const winsA = sinceTrades.filter((t) => t.pnl_usd >= 0);
  const lossA = sinceTrades.filter((t) => t.pnl_usd < 0);
  const sumP = (arr: HistoryTrade[]) => arr.reduce((s, t) => s + t.pnl_usd, 0);
  const avgWin = winsA.length ? sumP(winsA) / winsA.length : null;
  const avgLoss = lossA.length ? sumP(lossA) / lossA.length : null; // ujemna
  const perTrade = sinceTrades.length ? sumP(sinceTrades) / sinceTrades.length : null;
  const payoff = avgWin !== null && avgLoss !== null && avgLoss !== 0 ? avgWin / Math.abs(avgLoss) : null;

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
    // 1b) EDGE — ważniejsze niż trafność: czy wygrana bije stratę
    if (avgWin !== null && avgLoss !== null && perTrade !== null) {
      const good = perTrade >= 0;
      notes.push({
        t: `Średnia wygrana +${money(avgWin)} vs strata −${money(Math.abs(avgLoss))}${payoff ? ` (wygrana ${payoff.toFixed(1)}× większa)` : ""} → na transakcję ${perTrade >= 0 ? "+" : "−"}${money(Math.abs(perTrade))}. ${good ? "Zarabia mimo <50% trafności." : "Wygrane za małe wobec strat — to psuje wynik."}`,
        tone: good ? "good" : "bad",
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
        <span className="gd-audit-note">
          {Number.isFinite(epochMs)
            ? `pomiar od świeżego startu · ${new Date(epochMs).toLocaleDateString("pl-PL", { day: "numeric", month: "long" })}`
            : "od zmiany na progresywne wejścia + realizację zysku"}
        </span>
      </div>
      <div className="gd-audit-cols">
        <Col label="Ostatnie 7 dni" s={r} />
        <Col label="30 dni" s={m} />
        <Col label={totalLabel} s={a} />
      </div>

      {avgWin !== null && avgLoss !== null && perTrade !== null && (
        <div className="gd-edge">
          <div className="gd-edge-note">Ważniejsze niż „ile razy wygrywa" — czy <b>wygrana bije stratę</b>:</div>
          <div className="gd-edge-row">
            <div className="gd-edge-i"><small>śr. wygrana</small><b className="gd-up">+{money(avgWin)}</b></div>
            <div className="gd-edge-sep">vs</div>
            <div className="gd-edge-i"><small>śr. strata</small><b className="gd-down">−{money(Math.abs(avgLoss))}</b></div>
            <div className="gd-edge-arrow">→</div>
            <div className="gd-edge-i big"><small>na transakcję</small><b className={perTrade >= 0 ? "gd-up" : "gd-down"}>{perTrade >= 0 ? "+" : "−"}{money(Math.abs(perTrade))}</b></div>
          </div>
        </div>
      )}
      <ul className="gd-audit-notes">
        {notes.map((n, i) => <li key={i} className={`t-${n.tone}`}>{n.t}</li>)}
      </ul>
      <AuditDetails />
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

export function History({ status }: { status: StatusResponse | null }) {
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

      {data && data.trades.length > 0 && <AuditCard trades={data.trades} epoch={status?.stats_epoch} />}

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
