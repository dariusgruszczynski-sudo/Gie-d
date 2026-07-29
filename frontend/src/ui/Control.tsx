import { useState } from "react";
import { api, isReadOnly, StatusResponse } from "../api/client";
import { PushState, usePushNotifications } from "../hooks/usePushNotifications";

function useAction() {
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ t: string; ok: boolean } | null>(null);
  async function run(key: string, fn: () => Promise<unknown>, okMsg: string) {
    setBusy(key); setMsg(null);
    try { await fn(); setMsg({ t: okMsg, ok: true }); } catch (e) { setMsg({ t: String(e), ok: false }); } finally { setBusy(null); }
  }
  return { busy, msg, run };
}

function LegControls({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  const a = useAction();
  // Jeden silnik: gdy POZA SESJĄ wyłączona, pokazujemy tylko silnik pozycyjny.
  const legs: Array<{ v: "alpaca" | "extended"; name: string; paused: boolean; on: boolean }> = [
    { v: "alpaca", name: status.extended_enabled ? "SESJA · Akcje US" : "Silnik pozycyjny · Akcje US", paused: status.is_paused, on: true },
    ...(status.extended_enabled
      ? [{ v: "extended" as const, name: "POZA SESJĄ · ETF", paused: status.extended_paused, on: status.extended_enabled }]
      : []),
  ];
  return (
    <div className="gd-card">
      <h4>{status.extended_enabled ? "Silniki" : "Silnik"}</h4>
      {legs.map((l) => (
        <div key={l.v} style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <b style={{ fontFamily: "var(--font-display)" }}>{l.name}</b>
            <span className={`gd-chip ${!l.on ? "gd-chip-neu" : l.paused ? "gd-chip-off" : "gd-chip-on"}`}>
              {!l.on ? "wyłączony" : l.paused ? "zatrzymany" : "handluje"}
            </span>
          </div>
          <div className="gd-btnrow">
            {l.paused ? (
              <button className="gd-btn primary" disabled={!l.on || a.busy === `r${l.v}`} onClick={() => a.run(`r${l.v}`, () => api.resume(l.v).then(onChanged), "Wznowiono")}>▶ Wznów</button>
            ) : (
              <button className="gd-btn warn" disabled={!l.on || a.busy === `p${l.v}`} onClick={() => a.run(`p${l.v}`, () => api.pause(l.v).then(onChanged), "Zatrzymano")}>❚❚ Stop</button>
            )}
            <button className="gd-btn" disabled={!l.on || a.busy === `c${l.v}`} onClick={() => a.run(`c${l.v}`, () => api.runCycleNow(l.v).then(onChanged), "Cykl uruchomiony")}>↻ Przemyśl teraz</button>
            <button className="gd-btn" disabled={a.busy === `f${l.v}`} onClick={() => a.run(`f${l.v}`, () => api.refreshPortfolio(l.v).then(onChanged), "Odświeżono")}>⟳ Odśwież wycenę</button>
          </div>
        </div>
      ))}
      {a.msg && <div className={`gd-msg ${a.msg.ok ? "ok" : "err"}`}>{a.msg.t}</div>}
    </div>
  );
}

const PUSH_LABEL: Record<PushState, { text: string; tone: "on" | "off" | "neu" }> = {
  on: { text: "włączone na tym urządzeniu", tone: "on" },
  off: { text: "wyłączone na tym urządzeniu", tone: "off" },
  denied: { text: "zablokowane w przeglądarce", tone: "off" },
  "server-off": { text: "serwer nie ma kluczy VAPID", tone: "neu" },
  unsupported: { text: "przeglądarka nie wspiera Push API", tone: "neu" },
};

function Notifications() {
  const { state, busy, message, enable, disable, test } = usePushNotifications();
  const info = PUSH_LABEL[state];
  return (
    <div className="gd-card">
      <h4>Powiadomienia push</h4>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span className={`gd-chip ${info.tone === "on" ? "gd-chip-on" : info.tone === "off" ? "gd-chip-off" : "gd-chip-neu"}`}>
          {info.text}
        </span>
      </div>
      <div className="gd-btnrow">
        {state === "on" ? (
          <button className="gd-btn warn" disabled={busy} onClick={disable}>Wyłącz na tym urządzeniu</button>
        ) : (
          <button className="gd-btn primary" disabled={busy || state === "unsupported" || state === "server-off"} onClick={enable}>
            🔔 Włącz powiadomienia
          </button>
        )}
        <button className="gd-btn" disabled={busy || state !== "on"} onClick={test}>Wyślij testowe</button>
      </div>
      {state === "denied" && (
        <p className="gd-msg err" style={{ marginTop: 10 }}>
          Zablokowane w ustawieniach przeglądarki/systemu — odblokuj powiadomienia dla tej strony ręcznie, potem odśwież.
        </p>
      )}
      {message && <div className={`gd-msg ${message.toLowerCase().includes("nie udał") || message.toLowerCase().includes("nieudan") ? "err" : "ok"}`}>{message}</div>}
    </div>
  );
}

function Ops({ onChanged }: { onChanged: () => void }) {
  const a = useAction();
  return (
    <div className="gd-card">
      <h4>Operacje</h4>
      <div className="gd-btnrow">
        <button className="gd-btn" disabled={a.busy === "rep"} onClick={() => a.run("rep", () => api.sendReportNow(), "Raport wysłany")}>📈 Wyślij raport</button>
        <button className="gd-btn danger" disabled={a.busy === "res"} onClick={() => { if (window.confirm("Zrestartować backend automatu?")) a.run("res", () => api.restart().then(onChanged), "Restart zlecony"); }}>⟲ Restart</button>
      </div>
      {a.msg && <div className={`gd-msg ${a.msg.ok ? "ok" : "err"}`}>{a.msg.t}</div>}
    </div>
  );
}

function ManualTrade({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  const a = useAction();
  const [venue, setVenue] = useState<"alpaca" | "extended">("alpaca");
  const list = venue === "extended" ? status.extended_whitelist : status.whitelist;
  const [symbol, setSymbol] = useState(list[0] ?? "");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [usd, setUsd] = useState("50");
  return (
    <div className="gd-card">
      <h4>Ręczna transakcja</h4>
      {status.extended_enabled && (
        <div className="gd-field">
          <label>Noga</label>
          <select value={venue} onChange={(e) => { const v = e.target.value as "alpaca" | "extended"; setVenue(v); setSymbol((v === "extended" ? status.extended_whitelist : status.whitelist)[0] ?? ""); }}>
            <option value="alpaca">SESJA · Akcje US</option>
            <option value="extended">POZA SESJĄ · ETF</option>
          </select>
        </div>
      )}
      <div className="gd-field">
        <label>Instrument</label>
        <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
          {list.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <div className="gd-field">
        <label>Strona</label>
        <select value={side} onChange={(e) => setSide(e.target.value as "BUY" | "SELL")}>
          <option value="BUY">KUP</option><option value="SELL">SPRZEDAJ</option>
        </select>
      </div>
      <div className="gd-field">
        <label>Kwota USD</label>
        <input type="number" value={usd} min="1" onChange={(e) => setUsd(e.target.value)} />
      </div>
      <button className="gd-btn primary" disabled={a.busy === "mt" || !symbol}
        onClick={() => { if (window.confirm(`${side} ${symbol} za $${usd}? Realne zlecenie.`)) a.run("mt", () => api.manualTrade({ symbol, side, usdt_amount: Number(usd), venue }).then(onChanged), "Zlecenie złożone"); }}>
        Złóż zlecenie
      </button>
      {a.msg && <div className={`gd-msg ${a.msg.ok ? "ok" : "err"}`}>{a.msg.t}</div>}
    </div>
  );
}

export function Control({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  return (
    <div className="gd-view">
      <div className="gd-topline"><span className="gd-kicker">Sterowanie automatem</span></div>
      {isReadOnly ? (
        <p className="gd-empty">Widok tylko do odczytu — sterowanie ukryte.</p>
      ) : (
        <>
          <LegControls status={status} onChanged={onChanged} />
          <Notifications />
          <ManualTrade status={status} onChanged={onChanged} />
          <Ops onChanged={onChanged} />
        </>
      )}
    </div>
  );
}
