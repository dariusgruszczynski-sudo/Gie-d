import { useCallback, useEffect, useState } from "react";
import { api, Decision, PortfolioResponse, StatusResponse, Trade } from "./api/client";
import { ControlPanel } from "./components/ControlPanel";
import { DecisionsLog } from "./components/DecisionsLog";
import { PortfolioChart } from "./components/PortfolioChart";
import { StatusBanner } from "./components/StatusBanner";
import { TradesTable } from "./components/TradesTable";

const REFRESH_MS = 15000;

export default function App() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioResponse | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, p, t, d] = await Promise.all([
        api.status(),
        api.portfolio(),
        api.trades(),
        api.decisions(),
      ]);
      setStatus(s);
      setPortfolio(p);
      setTrades(t);
      setDecisions(d);
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(id);
  }, [refresh]);

  return (
    <div className="app">
      <div className="brand-banner">
        <p className="slogan">Kto gra grubo, wygrać musi</p>
      </div>

      <h1>Gie-d — automatyczny bot inwestycyjny</h1>
      <p className="subtitle">
        Decyzje: Claude Opus · Wykonanie: Binance · To narzędzie prywatne, nie jest to porada inwestycyjna.
      </p>

      {error && <p className="error-text">Błąd komunikacji z API: {error}</p>}

      {status && <StatusBanner status={status} />}

      <div className="grid">
        {portfolio && <PortfolioChart history={portfolio.history} current={portfolio.current} />}
        {status && <ControlPanel status={status} onChanged={refresh} />}
      </div>

      <div style={{ marginBottom: 16 }}>
        <DecisionsLog decisions={decisions} />
      </div>

      <TradesTable trades={trades} />
    </div>
  );
}
