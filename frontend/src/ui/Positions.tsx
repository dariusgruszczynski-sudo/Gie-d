import { useEffect, useState } from "react";
import { api, Decision, PortfolioResponse, PositionPlan, StatusResponse } from "../api/client";
import { DecRow, extract, Leg, PositionCard } from "./Console";
import { money } from "./kit";

/* EKRAN 2 — POZYCJE: każda akcja z miarką „kiedy sprzedam", opisem planu
   wyjścia i przyciskiem sprzedaży, plus pasek podsumowania i decyzje Claude'a. */
export function Positions({ status, alpaca, extended, decisions, onChanged }: {
  status: StatusResponse;
  alpaca: PortfolioResponse | null;
  extended: PortfolioResponse | null;
  decisions: Decision[];
  onChanged: () => void;
}) {
  const positions = [...extract(alpaca, "sesja"), ...extract(extended, "poza")].sort((a, b) => b.value - a.value);
  const invested = positions.reduce((s, p) => s + p.value, 0);

  const [plans, setPlans] = useState<Record<string, PositionPlan>>({});
  const hasA = !!alpaca?.current, hasE = !!extended?.current;
  useEffect(() => {
    let dead = false;
    (async () => {
      const map: Record<string, PositionPlan> = {};
      const legs: Array<[Leg, "alpaca" | "extended"]> = [];
      if (hasA) legs.push(["sesja", "alpaca"]);
      if (hasE) legs.push(["poza", "extended"]);
      await Promise.all(legs.map(async ([leg, venue]) => {
        try { const r = await api.positionPlans(venue); r.positions.forEach((pp) => (map[`${leg}:${pp.asset}`] = pp)); } catch { /* best effort */ }
      }));
      if (!dead) setPlans(map);
    })();
    return () => { dead = true; };
  }, [hasA, hasE, invested]);

  // Podsumowanie stanów wyjścia — ile pozycji jest „do wzięcia", ile blisko stopu.
  const states = positions.map((p) => plans[`${p.leg}:${p.asset}`]?.sell_plan?.state);
  const ripe = states.filter((s) => s === "profit_ready" || s === "sell_now").length;
  const climbing = states.filter((s) => s === "climbing").length;
  const nearStop = states.filter((s) => s === "near_stop").length;
  const bypassPct = status.profiles.alpaca.min_hold_profit_bypass_pct;

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Pozycje · plany wyjścia</span>
        <span className="gd-mode"><span className="gd-blip" />{positions.length} otwartych</span>
      </div>

      {/* Pasek podsumowania — jednym rzutem oka: ile w grze, co dojrzało */}
      <div className="gd-posbar">
        <div className="gd-posbar-i"><b>{money(invested)}</b><small>w grze</small></div>
        <div className="gd-posbar-sep" />
        <div className="gd-posbar-i"><b className="gd-up">{ripe}</b><small>🟢 zysk do wzięcia</small></div>
        <div className="gd-posbar-sep" />
        <div className="gd-posbar-i"><b>{climbing}</b><small>↗ rośnie</small></div>
        <div className="gd-posbar-sep" />
        <div className="gd-posbar-i"><b className={nearStop ? "gd-down" : ""}>{nearStop}</b><small>⚠ blisko stopu</small></div>
      </div>

      {positions.length ? (
        <div className="gd-pcards">
          {positions.map((p) => (
            <PositionCard key={`${p.leg}:${p.asset}`} p={p} plan={plans[`${p.leg}:${p.asset}`]}
              bypassPct={bypassPct} onChanged={onChanged} />
          ))}
        </div>
      ) : <p className="gd-empty">Brak otwartych pozycji — gotówka czeka na najlepsze wejścia.</p>}

      <div className="gd-sec"><h3>Decyzje Claude</h3><span className="gd-sec-note">dlaczego kupuję / trzymam / sprzedaję</span></div>
      {decisions.length ? (
        <div className="gd-stream">{decisions.slice(0, 14).map((d) => <DecRow key={d.id} d={d} />)}</div>
      ) : <p className="gd-empty">Jeszcze brak decyzji w tym oknie.</p>}
    </div>
  );
}
