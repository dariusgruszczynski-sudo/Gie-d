import { useState } from "react";
import { api, StatusResponse } from "../api/client";

export function ControlPanel({ status, onChanged }: { status: StatusResponse; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [symbol, setSymbol] = useState(status.whitelist[0] ?? "BTCUSDT");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [usdtAmount, setUsdtAmount] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [reportMessage, setReportMessage] = useState<string | null>(null);
  const [restartMessage, setRestartMessage] = useState<string | null>(null);

  const isStopped = status.is_paused || status.is_halted;

  async function togglePause() {
    setBusy(true);
    setError(null);
    try {
      if (isStopped) {
        await api.resume();
      } else {
        await api.pause();
      }
      onChanged();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function forceRunCycle() {
    setBusy(true);
    setError(null);
    try {
      await api.runCycleNow();
      onChanged();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function sendTestReport() {
    setBusy(true);
    setError(null);
    setReportMessage(null);
    try {
      const res = await api.sendReportNow();
      setReportMessage(res.message);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function restart() {
    setBusy(true);
    setError(null);
    setRestartMessage(null);
    try {
      const res = await api.restart();
      setRestartMessage(res.message);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function submitManualTrade(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const amount = parseFloat(usdtAmount);
    if (!amount || amount <= 0) {
      setError("Podaj poprawną kwotę USDT");
      return;
    }
    setBusy(true);
    try {
      await api.manualTrade({ symbol, side, usdt_amount: amount });
      setUsdtAmount("");
      onChanged();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>Kontrola automatu</h2>
      <button className={isStopped ? "btn-primary" : "btn-danger"} disabled={busy} onClick={togglePause}>
        {isStopped ? "▶ Wznów automat" : "⏸ Zatrzymaj automat"}
      </button>
      {status.is_halted && (
        <p className="subtitle" style={{ marginTop: 8 }}>
          Automat zatrzymał się sam po przekroczeniu limitu strat. Wznowienie czyści ten stan.
        </p>
      )}

      <button className="btn-primary" style={{ marginTop: 10 }} disabled={busy} onClick={forceRunCycle}>
        ⚡ Wymuś analizę teraz
      </button>
      <p className="subtitle" style={{ marginTop: 6 }}>
        Nie czeka na harmonogram — od razu pyta Opusa o decyzję na podstawie aktualnych danych.
      </p>

      <button className="btn-primary" style={{ marginTop: 10 }} disabled={busy} onClick={sendTestReport}>
        ✉️ WYŚLIJ RAPORT
      </button>
      <p className="subtitle" style={{ marginTop: 6 }}>
        Codzienny raport idzie automatycznie o 6:00 — tym przyciskiem możesz sprawdzić czy SMTP działa bez czekania.
      </p>
      {reportMessage && <p className="subtitle" style={{ color: "var(--green)" }}>{reportMessage}</p>}

      <button className="btn-danger" style={{ marginTop: 10 }} disabled={busy} onClick={restart}>
        🔄 RESTART
      </button>
      <p className="subtitle" style={{ marginTop: 6 }}>
        Restartuje proces backendu (np. gdy harmonogram się zawiesi). Nie pobiera nowego kodu z git ani zmian
        w .env — do tego nadal potrzeba <code>git pull &amp;&amp; docker compose up -d --build</code> na serwerze.
      </p>
      {restartMessage && <p className="subtitle" style={{ color: "var(--green)" }}>{restartMessage}</p>}

      <h2 style={{ marginTop: 22 }}>Ręczna transakcja (pomija Opus)</h2>
      <form className="control-form" onSubmit={submitManualTrade}>
        <div className="row">
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {status.whitelist.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select value={side} onChange={(e) => setSide(e.target.value as "BUY" | "SELL")}>
            <option value="BUY">KUP</option>
            <option value="SELL">SPRZEDAJ</option>
          </select>
        </div>
        <input
          type="number"
          step="any"
          placeholder="Kwota w USDT"
          value={usdtAmount}
          onChange={(e) => setUsdtAmount(e.target.value)}
        />
        <button className="btn-primary" type="submit" disabled={busy}>
          Wykonaj transakcję
        </button>
      </form>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
