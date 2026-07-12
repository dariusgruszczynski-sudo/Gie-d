import { MarketRegime } from "../api/client";

function temperature(regime: MarketRegime | null): { emoji: string; text: string } {
  if (!regime) return { emoji: "🌫️", text: "brak danych" };
  const score = regime.score;
  if (regime.regime === "risk_on") {
    return score >= 2 ? { emoji: "🔥", text: "hossa — silny trend wzrostowy" } : { emoji: "☀️", text: "raczej byczo" };
  }
  if (regime.regime === "risk_off") {
    // The backend only ever classifies risk_off at score <= -2 (see
    // compute_market_regime) -- it's always the strong case, never mild.
    return { emoji: "🧊", text: "bessa — silny trend spadkowy" };
  }
  // "neutral" covers everything between the risk_on/risk_off thresholds --
  // a mild negative score still leans bearish, so give it its own wording
  // instead of lumping it in with a genuinely flat/neutral read.
  if (score <= -1) return { emoji: "🌧️", text: "raczej niedźwiedzio" };
  return { emoji: "⛅", text: "neutralnie — brak wyraźnego kierunku" };
}

/** "Temperatura wody" jednym zdaniem pod nazwą apki: hossa/bessa dla USA i
 *  osobno dla krypto — czysty odczyt rynku, niezależny od tego czy dany silnik
 *  akurat handluje. Najedź na zdanie, żeby zobaczyć konkretne przesłanki. */
export function MarketTemperature({ us, crypto }: { us: MarketRegime | null; crypto: MarketRegime | null }) {
  const usT = temperature(us);
  const cryptoT = temperature(crypto);
  return (
    <div className="market-temp">
      <span className="market-temp-line" title={us?.reasons.join(" · ") || "Brak danych o rynku"}>
        <span className="market-temp-emoji">{usT.emoji}</span> Rynek USA: <strong>{usT.text}</strong>
      </span>
      <span className="market-temp-line" title={crypto?.reasons.join(" · ") || "Brak danych o rynku"}>
        <span className="market-temp-emoji">{cryptoT.emoji}</span> Krypto: <strong>{cryptoT.text}</strong>
      </span>
    </div>
  );
}
