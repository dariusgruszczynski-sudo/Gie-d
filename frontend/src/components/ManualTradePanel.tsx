import { useState } from "react";
import { api } from "../api/client";

export function ManualTradePanel({
  whitelist,
  onChanged,
  venue = "alpaca",
  title = "Ręczna transakcja",
}: {
  whitelist: string[];
  onChanged: () => void;
  venue?: "alpaca" | "crypto";
  title?: string;
}) {
  const [busy, setBusy] = useState(false);
  const [symbol, setSymbol] = useState(whitelist[0] ?? "");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [usdtAmount, setUsdtAmount] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submitManualTrade(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const amount = parseFloat(usdtAmount);
    if (!amount || amount <= 0) {
      setError("Podaj poprawną kwotę USD");
      return;
    }
    setBusy(true);
    try {
      await api.manualTrade({ symbol: symbol || whitelist[0], side, usdt_amount: amount, venue });
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
      <h2>{title}</h2>
      <form className="control-form" onSubmit={submitManualTrade}>
        <div className="row">
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {whitelist.map((s) => (
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
          placeholder="Kwota w USD"
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
