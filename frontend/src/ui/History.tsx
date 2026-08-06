import { useEffect, useState } from "react";
import { api, HistoryResponse, HistoryTrade } from "../api/client";
import { ago, money, pct } from "./kit";

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
