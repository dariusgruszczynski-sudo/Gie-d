import { useEffect, useRef, useState } from "react";
import { api, DryRunResponse, StatusResponse } from "../api/client";

/* STER — szuflada sterowania dostępna z każdego ekranu (zasada KONTROLA).
   Trzyma tylko sterowanie: kto rządzi, pauza/wznów, „przemyśl teraz", awaryjny
   STOP, ręczna transakcja, symulacja (dry-run) i podgląd limitów ryzyka. */

type Venue = "alpaca" | "extended" | "crypto";

function useAction() {
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ t: string; ok: boolean } | null>(null);
  async function run(key: string, fn: () => Promise<unknown>, okMsg: string) {
    setBusy(key); setMsg(null);
    try { await fn(); setMsg({ t: okMsg, ok: true }); } catch (e) { setMsg({ t: String(e), ok: false }); } finally { setBusy(null); }
  }
  return { busy, msg, run };
}

function EngineSection({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  const a = useAction();
  const venue: Venue = status.crypto_enabled ? "crypto" : "alpaca";
  const paused = status.crypto_enabled ? !!status.crypto_paused : status.is_paused;
  const halted = !!status.is_halted;
  return (
    <div className="cr-sec">
      <h4>Silnik {status.crypto_enabled ? "· KRYPTO 24/7 (paper)" : "· Akcje US"}</h4>
      {halted && <p className="hint" style={{ color: "var(--cr-down)" }}>⛔ Zatrzymany bezpiecznikiem: {status.halted_reason || ""}. „Odblokuj" wznawia i zeruje punkty odniesienia.</p>}
      <div className="cr-btnrow">
        {paused || halted ? (
          <button className="cr-btn primary" disabled={a.busy === "r"} onClick={() => a.run("r", () => api.resume(venue).then(onChanged), halted ? "Odblokowano" : "Wznowiono")}>▶ {halted ? "Odblokuj" : "Wznów"}</button>
        ) : (
          <button className="cr-btn warn" disabled={a.busy === "p"} onClick={() => a.run("p", () => api.pause(venue).then(onChanged), "Zatrzymano")}>❚❚ Pauza</button>
        )}
        <button className="cr-btn" disabled={a.busy === "c"} onClick={() => a.run("c", () => api.runCycleNow(venue).then(onChanged), "Cykl uruchomiony")}>↻ Przemyśl teraz</button>
        <button className="cr-btn" disabled={a.busy === "f"} onClick={() => a.run("f", () => api.refreshPortfolio(venue).then(onChanged), "Odświeżono wycenę")}>⟳ Odśwież wycenę</button>
      </div>
      {a.msg && <div className={`cr-msg ${a.msg.ok ? "ok" : "err"}`}>{a.msg.t}</div>}
    </div>
  );
}

function PanicSection({ onChanged }: { onChanged: () => void }) {
  const a = useAction();
  async function panic() {
    if (!window.confirm("🛑 STOP WSZYSTKO?\n\nWstrzyma bota i SPRZEDA wszystkie pozycje po cenie rynkowej. Nieodwracalne. Kontynuować?")) return;
    await a.run("panic", async () => { const r = await api.panic(); window.alert(r.message || "Zrobione."); onChanged(); }, "Wstrzymano i sprzedano.");
  }
  return (
    <div className="cr-sec">
      <h4>🛑 Awaryjny STOP</h4>
      <p className="hint">Wstrzymuje bota i zamyka wszystkie pozycje. Na wypadek paniki.</p>
      <button className="cr-panicbtn" disabled={a.busy === "panic"} onClick={panic}>{a.busy === "panic" ? "Zamykam wszystko…" : "🛑 Sprzedaj wszystko i wstrzymaj"}</button>
      {a.msg && <div className={`cr-msg ${a.msg.ok ? "ok" : "err"}`}>{a.msg.t}</div>}
    </div>
  );
}

function ManualSection({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  const a = useAction();
  const crypto = !!status.crypto_enabled;
  const list = crypto ? (status.crypto_universe ?? []) : status.whitelist;
  const venue: Venue = crypto ? "crypto" : "alpaca";
  const [symbol, setSymbol] = useState(list[0] ?? "");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [usd, setUsd] = useState("50");
  const paper = status.mode !== "live";
  return (
    <div className="cr-sec">
      <h4>Ręczna transakcja{crypto ? " · krypto" : ""}</h4>
      <p className="hint">Przejmij ster na jedną transakcję. {paper ? "Konto papierowe." : "REALNE środki."}</p>
      <div className="cr-field"><label>Instrument</label>
        <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>{list.map((s) => <option key={s} value={s}>{s}</option>)}</select>
      </div>
      <div className="cr-field"><label>Strona</label>
        <select value={side} onChange={(e) => setSide(e.target.value as "BUY" | "SELL")}><option value="BUY">KUP</option><option value="SELL">SPRZEDAJ</option></select>
      </div>
      <div className="cr-field"><label>Kwota USD</label><input type="number" min="1" value={usd} onChange={(e) => setUsd(e.target.value)} /></div>
      <button className="cr-btn primary block" disabled={a.busy === "mt" || !symbol}
        onClick={() => { if (window.confirm(`${side} ${symbol} za $${usd}? ${paper ? "Konto papierowe." : "REALNE zlecenie."}`)) a.run("mt", () => api.manualTrade({ symbol, side, usdt_amount: Number(usd), venue }).then(onChanged), "Zlecenie złożone"); }}>
        Złóż zlecenie
      </button>
      {a.msg && <div className={`cr-msg ${a.msg.ok ? "ok" : "err"}`}>{a.msg.t}</div>}
    </div>
  );
}

function DrySection({ status }: { status: StatusResponse }) {
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<DryRunResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const venue: Venue = status.crypto_enabled ? "crypto" : "alpaca";
  async function run() {
    setBusy(true); setErr(null); setRes(null);
    try { setRes(await api.dryRun(venue)); } catch (e) { setErr(String(e)); } finally { setBusy(false); }
  }
  const acts = (res?.proposals ?? []).filter((p) => p.action !== "HOLD");
  return (
    <div className="cr-sec">
      <h4>🧪 Symulacja (nic nie zleca)</h4>
      <p className="hint">Pokaż, co bot BY zrobił na żywych danych — bez składania zleceń.</p>
      <button className="cr-btn block" disabled={busy} onClick={run}>{busy ? "Analizuję…" : "▶ Odpal symulację"}</button>
      {err && <div className="cr-msg err">{err}</div>}
      {res && (
        <div style={{ marginTop: 8 }}>
          {res.regime && <p className="hint" style={{ margin: "0 0 4px" }}>Reżim: <b>{res.regime}</b></p>}
          {acts.length === 0 ? <p className="cr-prop-mut">Bot by nie handlował — wszystko na HOLD (czeka).</p>
            : acts.map((p, i) => (
              <div className="cr-prop" key={i}>
                <div className="cr-prop-top"><b>{p.symbol ?? "—"}</b><span className={`cr-prop-act ${p.action === "BUY" ? "buy" : "sell"}`}>{p.action}</span><span className="cr-prop-mut">pewność {Math.round(p.confidence * 100)}% · ~{p.effective_size_pct.toFixed(1)}%</span></div>
                <div className="cr-prop-why">{p.reasoning}</div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}

function LimitsSection({ status }: { status: StatusResponse }) {
  return (
    <div className="cr-sec">
      <h4>Limity ryzyka (bezpieczniki)</h4>
      <p className="hint">Po przekroczeniu bot sam się wstrzyma. Zmiana knobów strategii = w configu, świadomie.</p>
      <div className="cr-limits">
        <div className="cr-limit"><div className="k">Dzień</div><div className="v" style={{ color: "var(--cr-down)" }}>−{status.daily_loss_limit_pct}%</div></div>
        <div className="cr-limit"><div className="k">Tydzień</div><div className="v" style={{ color: "var(--cr-down)" }}>−{status.weekly_loss_limit_pct}%</div></div>
        <div className="cr-limit"><div className="k">Obsunięcie</div><div className="v" style={{ color: "var(--cr-down)" }}>−{status.max_drawdown_halt_pct}%</div></div>
      </div>
      <div className="cr-limits" style={{ marginTop: 8 }}>
        <div className="cr-limit"><div className="k">Maks. pozycja</div><div className="v">{status.max_position_pct}%</div></div>
        <div className="cr-limit"><div className="k">Szczyt konta</div><div className="v">{status.peak_account_value ? `$${Math.round(status.peak_account_value).toLocaleString("pl-PL")}` : "—"}</div></div>
        <div className="cr-limit"><div className="k">Skan</div><div className="v">~{status.poll_interval_minutes}m</div></div>
      </div>
    </div>
  );
}

export function SterDrawer({ status, onChanged, onClose }: { status: StatusResponse; onChanged: () => void; onClose: () => void }) {
  const paused = status.crypto_enabled ? !!status.crypto_paused : status.is_paused;
  const halted = !!status.is_halted;
  const dotCol = halted ? "var(--cr-down)" : paused ? "var(--cr-warn)" : "var(--cr-up)";

  // POWRÓT ze STER: sprzętowy „wstecz" (Android / gest na telefonie) i Escape
  // zamykają szufladę zamiast wychodzić z apki. Wypychamy jeden wpis historii na
  // wejściu i zdejmujemy go przy zamknięciu — bez tego „wstecz" opuszczał całą
  // apkę i nie było jak wrócić do poprzedniego ekranu (zgłoszone przez użytkownika).
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => {
    window.history.pushState({ crSter: true }, "");
    const onPop = () => onCloseRef.current();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onCloseRef.current(); };
    window.addEventListener("popstate", onPop);
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("popstate", onPop);
      window.removeEventListener("keydown", onKey);
      // Zamknięto przyciskiem (nie „wstecz") -> zdejmij nasz wpis, żeby historia
      // była czysta. Gdy zamknięto „wstecz", wpisu już nie ma -> nic nie robimy.
      if (window.history.state && (window.history.state as { crSter?: boolean }).crSter) {
        window.history.back();
      }
    };
  }, []);

  return (
    <>
      <div className="cr-scrim" onClick={onClose} />
      <aside className="cr-drawer" role="dialog" aria-label="Sterowanie botem">
        <div className="cr-drawer-head">
          <h2>⛭ Ster</h2>
          <button className="x" onClick={onClose} aria-label="Zamknij sterowanie">✕ Zamknij</button>
        </div>
        <div className="cr-drawer-body">
          <div className="cr-ster-who">
            <span className="dot" style={{ background: dotCol }} />
            teraz steruje <b style={{ color: dotCol }}>{halted ? "BEZPIECZNIK (HALT)" : paused ? "TY (wstrzymany)" : "BOT"}</b>
          </div>
          <EngineSection status={status} onChanged={onChanged} />
          <PanicSection onChanged={onChanged} />
          <ManualSection status={status} onChanged={onChanged} />
          <DrySection status={status} />
          <LimitsSection status={status} />
          <button className="cr-drawer-back" onClick={onClose}>← Wróć do pulpitu</button>
        </div>
      </aside>
    </>
  );
}
