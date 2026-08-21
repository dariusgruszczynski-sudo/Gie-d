import { useEffect, useState } from "react";
import { api, AuditResponse, Decision, MonthlyRow, PortfolioResponse } from "../api/client";
import { money } from "./kit";

/* Krzywa: wzrost automatu (deposit-proof %) vs wzrost SPY (%) od początku okna.
   Obie linie startują od 0% — uczciwe „czy bijesz zwykłe trzymanie indeksu".
   Bot% = skumulowany zysk automatu (odporny na wpłaty) jako % konta na starcie;
   SPY% = zmiana ceny SPY. Liczone z danych, które /api/portfolio już zwraca. */
function VsSpy({ pf }: { pf: PortfolioResponse | null }) {
  const hist = pf?.history ?? [];
  const pnl = pf?.pnl_history ?? [];
  if (hist.length < 2 || pnl.length !== hist.length) return null;
  const base = hist[0].total_value_usdt || 0;
  const spyAt = (i: number): number | null => {
    try { const p = JSON.parse(hist[i].prices_json || "{}"); return typeof p.SPY === "number" ? p.SPY : null; } catch { return null; }
  };
  const spy0 = spyAt(0);
  if (base <= 0 || spy0 === null || spy0 <= 0) return null;
  const pts = hist.map((_, i) => {
    const s = spyAt(i);
    return { bot: (pnl[i] / base) * 100, spy: s !== null ? (s / spy0 - 1) * 100 : null };
  });
  const botVals = pts.map((p) => p.bot);
  const spyVals = pts.map((p) => p.spy).filter((v): v is number => v !== null);
  const all = [...botVals, ...spyVals, 0];
  const lo = Math.min(...all), hi = Math.max(...all);
  const span = hi - lo || 1;
  const W = 320, H = 90;
  const x = (i: number) => (i / (pts.length - 1)) * W;
  const y = (v: number) => H - ((v - lo) / span) * H;
  const line = (key: "bot" | "spy") => pts.map((p, i) => (p[key] === null ? null : `${x(i).toFixed(1)},${y(p[key] as number).toFixed(1)}`))
    .filter(Boolean).join(" ");
  const botNow = botVals[botVals.length - 1];
  const spyNow = spyVals.length ? spyVals[spyVals.length - 1] : null;
  const beating = spyNow !== null && botNow >= spyNow;
  return (
    <div className="gd-anz-spy">
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="gd-anz-spysvg">
        <line x1="0" y1={y(0)} x2={W} y2={y(0)} className="gd-anz-zero" />
        <polyline points={line("spy")} className="gd-anz-spline spy" fill="none" />
        <polyline points={line("bot")} className="gd-anz-spline bot" fill="none" />
      </svg>
      <div className="gd-anz-spylegend">
        <span className="bot">● Automat {botNow >= 0 ? "+" : ""}{botNow.toFixed(1)}%</span>
        <span className="spy">● SPY {spyNow !== null ? `${spyNow >= 0 ? "+" : ""}${spyNow.toFixed(1)}%` : "—"}</span>
        {spyNow !== null && <b className={beating ? "gd-up" : "gd-down"}>{beating ? "bijesz indeks" : "poniżej indeksu"}</b>}
      </div>
    </div>
  );
}

/* EKRAN ANALIZA (Funkcjonalności — wgląd): trzy pierwszoklasowe widoki, dotąd
   schowane w „szczegółach" Historii albo w ogóle niepokazane:
   1) Miesięczny raport wyników (zysk/skuteczność per miesiąc),
   2) Rozbicie zysku PER SPÓŁKA (kto zarabia, kto przecieka),
   3) „Czemu nie kupił" — ostatnie decyzje odrzucone mimo sygnału, z powodem. */

const PL_MONTH = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"];
function monthLabel(ym: string): string {
  const [y, m] = ym.split("-");
  const idx = Math.max(0, Math.min(11, Number(m) - 1));
  return `${PL_MONTH[idx]} ${y}`;
}

export function Analiza() {
  const [audit, setAudit] = useState<AuditResponse | null>(null);
  const [months, setMonths] = useState<MonthlyRow[] | null>(null);
  const [decisions, setDecisions] = useState<Decision[] | null>(null);
  const [pf, setPf] = useState<PortfolioResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const [a, m, d, p] = await Promise.all([api.audit(), api.monthly(), api.decisions("alpaca"), api.portfolio("alpaca")]);
        if (!dead) { setAudit(a); setMonths(m.months); setDecisions(d); setPf(p); }
      } catch (e) {
        if (!dead) setErr(String(e));
      }
    })();
    return () => { dead = true; };
  }, []);

  // Per-spółka: łączymy przecieki (per_symbol) i najlepsze (per_symbol_best),
  // sortujemy od najlepszej do najgorszej — pełny obraz kto zarabia/kto traci.
  const perSymbol = audit
    ? [...audit.per_symbol_best, ...audit.per_symbol].filter(
        (s, i, arr) => arr.findIndex((x) => x.symbol === s.symbol) === i,
      ).sort((a, b) => b.pnl_usd - a.pnl_usd)
    : [];

  // „Czemu nie kupił": ostatnie decyzje NIEwykonane z podanym powodem odrzucenia.
  const rejected = (decisions ?? [])
    .filter((d) => !d.executed && (d.rejection_reason || d.action === "HOLD"))
    .slice(0, 12);

  const maxMonthAbs = Math.max(1, ...(months ?? []).map((m) => Math.abs(m.realized_usd)));

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Analiza · wgląd w wyniki</span>
      </div>
      {err && <div className="gd-ribbon">{err}</div>}

      {/* 0) KRZYWA vs SPY */}
      <div className="gd-sec"><h3>Ty vs trzymanie SPY</h3><span className="gd-sec-note">wzrost automatu (bez wpłat) vs indeks, od początku</span></div>
      {pf ? (<VsSpy pf={pf} />) : <p className="gd-empty">Liczę…</p>}

      {/* 1) MIESIĘCZNY RAPORT */}
      <div className="gd-sec"><h3>Miesiąc po miesiącu</h3><span className="gd-sec-note">zysk zrealizowany per miesiąc</span></div>
      {!months ? <p className="gd-empty">Liczę…</p> : months.length === 0 ? (
        <p className="gd-empty">Brak zamkniętych transakcji do podsumowania.</p>
      ) : (
        <div className="gd-anz-months">
          {months.map((m) => {
            const up = m.realized_usd >= 0;
            const w = Math.round((Math.abs(m.realized_usd) / maxMonthAbs) * 100);
            return (
              <div className="gd-anz-mrow" key={m.month}>
                <span className="gd-anz-mlbl">{monthLabel(m.month)}</span>
                <span className="gd-anz-mtrack">
                  <i className={up ? "up" : "down"} style={{ width: `${Math.max(3, w)}%` }} />
                </span>
                <span className={`gd-anz-mval ${up ? "gd-up" : "gd-down"}`}>{up ? "+" : ""}{money(m.realized_usd)}</span>
                <span className="gd-anz-mmut">{m.closed} zamk.{m.win_rate !== null ? ` · ${m.win_rate}%` : ""}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* 2) PER SPÓŁKA */}
      <div className="gd-sec"><h3>Kto zarabia, kto przecieka</h3><span className="gd-sec-note">zysk łączny per spółka</span></div>
      {!audit ? <p className="gd-empty">Liczę…</p> : perSymbol.length === 0 ? (
        <p className="gd-empty">Brak danych per spółka.</p>
      ) : (
        <div className="gd-anz-syms">
          {perSymbol.map((s) => (
            <div className="gd-anz-sym" key={s.symbol}>
              <b className="gd-anz-symname">{s.symbol}</b>
              <span className={`gd-anz-sympnl ${s.pnl_usd >= 0 ? "gd-up" : "gd-down"}`}>{s.pnl_usd >= 0 ? "+" : ""}{money(s.pnl_usd)}</span>
              <span className="gd-anz-symmut">{s.closed} zamk.{s.win_rate !== null ? ` · ${s.win_rate}% traf.` : ""}</span>
            </div>
          ))}
        </div>
      )}

      {/* 3) CZEMU NIE KUPIŁ */}
      <div className="gd-sec"><h3>Czemu nie wchodzi</h3><span className="gd-sec-note">ostatnie decyzje wstrzymane — z powodem</span></div>
      {audit && (
        <div className="gd-anz-reasons">
          <div className="gd-anz-rsum">Odrzuconych mimo sygnału (ostatnie 300 decyzji): <b>{audit.decisions.rejected}</b></div>
          {audit.decisions.reasons.slice(0, 5).map((r, i) => (
            <div className="gd-anz-rrow" key={i}><span>{r.reason}</span><b>{r.n}×</b></div>
          ))}
        </div>
      )}
      {!decisions ? null : rejected.length === 0 ? (
        <p className="gd-empty">Brak ostatnich wstrzymań — bot wchodził albo czekał bez odrzuceń.</p>
      ) : (
        <div className="gd-anz-cyc">
          {rejected.map((d) => (
            <div className="gd-anz-cycrow" key={d.id}>
              <div className="gd-anz-cyctop">
                <b>{d.symbol ?? "—"}</b>
                <span className={`gd-anz-cycact ${d.action === "BUY" ? "buy" : d.action === "SELL" ? "sell" : ""}`}>{d.action}</span>
                <span className="gd-anz-cycmut">pewność {Math.round((d.confidence ?? 0) * 100)}%</span>
              </div>
              <div className="gd-anz-cycwhy">{d.rejection_reason || d.reasoning || "—"}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
