import { useEffect, useState } from "react";
import { api, HealthReport, isReadOnly } from "../api/client";

const ACTION_LABEL: Record<string, string> = {
  resume_alpaca: "Wznów SESJA",
  resume_extended: "Wznów POZA SESJĄ",
  clear_halt: "Zdejmij halt",
  refresh_snapshots: "Odśwież snapshoty",
  restart_scheduler: "Restart schedulera",
  rebaseline_pnl: "Wpłata/wypłata — przelicz P&L",
  reset_budget_meter: "Wyzeruj licznik tokenów",
};

export function Health() {
  const [rep, setRep] = useState<HealthReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  async function load() { setBusy(true); try { setRep(await api.health()); } catch (e) { setMsg(String(e)); } finally { setBusy(false); } }
  useEffect(() => { load(); }, []);

  async function reset(action: string) {
    setBusy(true); setMsg(null);
    try { const r = await api.healthReset(action); setMsg((r as { message?: string }).message ?? "OK"); await load(); }
    catch (e) { setMsg(String(e)); } finally { setBusy(false); }
  }

  return (
    <div className="gd-view">
      <div className="gd-topline">
        <span className="gd-kicker">Puls systemu {rep ? `· ${rep.counts?.ok ?? 0} OK` : ""}</span>
        <button className="gd-btn" disabled={busy} onClick={load}>{busy ? "…" : "Odśwież"}</button>
      </div>
      {msg && <div className="gd-ribbon">{msg}</div>}
      {!rep ? <p className="gd-empty">Sprawdzam…</p> : (
        <div className="gd-hl">
          {rep.checks.map((c) => (
            <div className="gd-hl-item" key={c.key}>
              <span className={`gd-hl-led ${c.status}`} />
              <div className="gd-hl-txt">
                <div className="l">{c.label}</div>
                <div className="d">{c.detail}</div>
                {!isReadOnly && c.action && (
                  <button className="gd-btn" style={{ marginTop: 8, padding: "7px 12px", fontSize: "0.74rem" }} disabled={busy} onClick={() => reset(c.action!)}>
                    {ACTION_LABEL[c.action] ?? c.action}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
