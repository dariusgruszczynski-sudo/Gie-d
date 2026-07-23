import { useEffect, useState } from "react";
import { api, Decision, PositionPlan, StatusResponse } from "../api/client";

const TRIGGER_LABEL: Record<string, string> = {
  scheduled_daily: "cykl",
  price_move: "ruch ceny",
  news_event: "news",
  manual: "ręczne",
};

const PLAN_LABEL: Record<string, { txt: string; cls: string }> = {
  hold: { txt: "Trzymam", cls: "neu" },
  near_stop: { txt: "Blisko stopa", cls: "neg" },
  partial_ready: { txt: "Częściowa realizacja", cls: "pos" },
  take_profit_ready: { txt: "Realizuję zysk", cls: "pos" },
  trailing_protected: { txt: "Zysk chroniony trailingiem", cls: "pos" },
  adopted: { txt: "Adoptowana", cls: "neu" },
};

function venueLabel(v?: string): string {
  return v === "extended" ? "Poza sesją" : "Akcje US";
}

function timeAgo(iso: string): string {
  const d = new Date(iso).getTime();
  const mins = Math.max(0, Math.round((Date.now() - d) / 60000));
  if (mins < 1) return "teraz";
  if (mins < 60) return `${mins} min temu`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `${h} h temu`;
  return `${Math.floor(h / 24)} dni temu`;
}

type Status = { kind: "buy" | "sell" | "hold" | "reject"; label: string };
function decisionStatus(d: Decision): Status {
  if (d.rejection_reason) return { kind: "reject", label: "Odrzucono" };
  if (d.executed && d.action === "BUY") return { kind: "buy", label: "Kupiono" };
  if (d.executed && d.action === "SELL") return { kind: "sell", label: "Sprzedano" };
  if (d.action === "HOLD") return { kind: "hold", label: "Czeka" };
  return { kind: "hold", label: d.action };
}

export function Journal({ decisions, status }: { decisions: Decision[]; status: StatusResponse }) {
  const [plansA, setPlansA] = useState<PositionPlan[]>([]);
  const [plansE, setPlansE] = useState<PositionPlan[]>([]);
  const [venue, setVenue] = useState<"all" | "alpaca" | "extended">("all");

  async function loadPlans() {
    try {
      setPlansA((await api.positionPlans("alpaca")).positions ?? []);
    } catch { /* ignore */ }
    if (status.extended_enabled) {
      try {
        setPlansE((await api.positionPlans("extended")).positions ?? []);
      } catch { /* ignore */ }
    }
  }
  useEffect(() => {
    loadPlans();
    const id = setInterval(loadPlans, 30000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status.extended_enabled]);

  const plans: Array<PositionPlan & { venue: string }> = [
    ...plansA.map((p) => ({ ...p, venue: "alpaca" })),
    ...plansE.map((p) => ({ ...p, venue: "extended" })),
  ].filter((p) => venue === "all" || p.venue === venue);

  const feed = decisions
    .filter((d) => venue === "all" || (d.venue ?? "alpaca") === venue)
    .slice(0, 80);

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Dziennik · co bot robi i zamierza</span>
        <div className="gd-seg">
          {(["all", "alpaca", "extended"] as const).map((v) => (
            <button key={v} className={`gd-seg-b ${venue === v ? "on" : ""}`} onClick={() => setVenue(v)}>
              {v === "all" ? "Wszystko" : v === "alpaca" ? "Akcje US" : "Poza sesją"}
            </button>
          ))}
        </div>
      </div>

      <div className="gd-newsgrp-h">Co zamierza z otwartymi pozycjami</div>
      {plans.length === 0 ? (
        <p className="gd-empty">Brak otwartych pozycji — gotówka czeka na wejścia.</p>
      ) : (
        <div className="gd-feed" style={{ marginBottom: 18 }}>
          {plans.map((p) => {
            const pl = PLAN_LABEL[p.action] ?? { txt: p.action, cls: "neu" };
            return (
              <div className="gd-feed-item" key={`${p.venue}-${p.asset}`}>
                <div className="gd-jrow">
                  <b>{p.asset}</b>
                  <span className={`gd-sent ${pl.cls}`}>{pl.txt}</span>
                  {p.change_pct !== null && (
                    <span className={`gd-jchg ${p.change_pct >= 0 ? "gd-up" : "gd-down"}`}>
                      {p.change_pct >= 0 ? "+" : ""}{p.change_pct.toFixed(1)}%
                    </span>
                  )}
                  <span className="gd-feed-src">{venueLabel(p.venue)}</span>
                </div>
                <div className="gd-feed-title" style={{ fontSize: "0.82rem", marginTop: 4 }}>{p.note}</div>
              </div>
            );
          })}
        </div>
      )}

      <div className="gd-newsgrp-h">Dziennik decyzji</div>
      {feed.length === 0 ? (
        <p className="gd-empty">Brak decyzji w historii.</p>
      ) : (
        <div className="gd-feed">
          {feed.map((d) => {
            const st = decisionStatus(d);
            return (
              <div className="gd-feed-item" key={d.id}>
                <div className="gd-jrow">
                  <span className={`gd-badge gd-badge-${st.kind}`}>{st.label}</span>
                  {d.symbol && <b>{d.symbol}</b>}
                  {(d.action === "BUY" || d.action === "SELL") && d.size_pct > 0 && (
                    <span className="gd-feed-src">{d.size_pct.toFixed(0)}%</span>
                  )}
                  {d.confidence > 0 && <span className="gd-feed-src">pewność {Math.round(d.confidence * 100)}%</span>}
                  <span className="gd-feed-src">· {TRIGGER_LABEL[d.triggered_by] ?? d.triggered_by}</span>
                  <span className="gd-jspacer" />
                  <span className="gd-feed-src">{venueLabel(d.venue)} · {timeAgo(d.timestamp)}</span>
                </div>
                {(d.reasoning || d.rejection_reason) && (
                  <div className="gd-feed-title" style={{ fontSize: "0.82rem", marginTop: 4 }}>
                    {d.rejection_reason ? `⛔ ${d.rejection_reason}` : d.reasoning}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
