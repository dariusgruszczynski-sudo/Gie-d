interface TickerInfo {
  name: string;
  description: string;
}

const TICKER_INFO: Record<string, TickerInfo> = {
  SPY: {
    name: "SPDR S&P 500 ETF Trust",
    description:
      "Największy i najpłynniejszy ETF na świecie, odwzorowujący indeks S&P 500 — 500 największych spółek giełdowych w USA. Jednym zakupem daje szeroką dywersyfikację, więc jest spokojniejszym, defensywnym rdzeniem portfela w porównaniu z pojedynczymi akcjami. Niska zmienność względem rynku, bo w praktyce sam nim jest.",
  },
  QQQ: {
    name: "Invesco QQQ Trust",
    description:
      "Śledzi indeks Nasdaq-100, mocno przeważony w stronę największych spółek technologicznych (Apple, Microsoft, Nvidia, Amazon i inne). Bardziej zmienny niż SPY, ale z wyższym potencjałem wzrostu w hossie technologicznej. Dobre uzupełnienie SPY, gdy strategia szuka większej ekspozycji na wzrost.",
  },
  AAPL: {
    name: "Apple Inc.",
    description:
      "Jedna z największych i najpłynniejszych spółek na świecie (iPhone, Mac, usługi cyfrowe). Stabilny „blue chip”, ale cena wyraźnie reaguje na premiery produktów i wyniki kwartalne. Wysoka płynność ułatwia szybkie wejścia i wyjścia bez dużego wpływu na kurs.",
  },
  NVDA: {
    name: "Nvidia Corp.",
    description:
      "Dominujący producent układów GPU napędzających rozwój sztucznej inteligencji. Wysoki potencjał wzrostu, ale też jedna z bardziej zmiennych dużych spółek — gwałtowne ruchy po wynikach i newsach związanych z AI. Wymaga większej tolerancji na wahania niż SPY czy QQQ.",
  },
  MSTR: {
    name: "MicroStrategy (Strategy Inc.)",
    description:
      "Spółka software'owa, która swój bilans oparła na gigantycznych zapasach bitcoina finansowanych długiem — w praktyce lewarowana zakładka na kurs BTC, nie zwykła akcja tech. Potrafi ruszyć się kilkanaście procent w jeden dzień w obie strony. Celowo najbardziej szalona i najbardziej ryzykowna pozycja na liście — mały rozmiar pozycji jest tu kluczowy.",
  },
};

function fallbackInfo(ticker: string): TickerInfo {
  return {
    name: ticker,
    description: "Ticker na liście handlowej automatu — decyzje o nim podejmuje Claude na tych samych zasadach co pozostałe pozycje w portfelu.",
  };
}

export function InvestmentThesis({ whitelist }: { whitelist: string[] }) {
  if (whitelist.length === 0) return null;

  return (
    <div className="panel" style={{ marginBottom: 16 }}>
      <h2>Inwestuję w</h2>
      <p className="subtitle" style={{ marginTop: -6, marginBottom: 12 }}>
        Lista tickerów, którymi automat może handlować, wraz z krótkim opisem każdego.
      </p>
      <div className="thesis-grid">
        {whitelist.map((ticker) => {
          const info = TICKER_INFO[ticker.toUpperCase()] ?? fallbackInfo(ticker);
          return (
            <div className="thesis-card" key={ticker}>
              <div className="thesis-card-header">
                <span className="thesis-ticker">{ticker}</span>
                <span className="thesis-name">{info.name}</span>
              </div>
              <p className="thesis-description">{info.description}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
