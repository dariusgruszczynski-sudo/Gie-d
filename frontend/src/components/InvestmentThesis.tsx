import { useState } from "react";

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
      "Spółka software'owa, która swój bilans oparła na gigantycznych zapasach bitcoina finansowanych długiem — w praktyce lewarowana zakładka na kurs BTC, nie zwykła akcja tech. Potrafi ruszyć się kilkanaście procent w jeden dzień w obie strony. Celowo najbardziej szalona i najbardziej ryzykowna pozycja na liście — rozmiar pozycji jest tu automatycznie zmniejszany przez skalowanie wg zmienności.",
  },
  TSLA: {
    name: "Tesla Inc.",
    description:
      "Wysokobetowa spółka z ogromnym przepływem newsów (Elon, dostawy, robotaxi, AI) — świetnie współgra z triggerem newsowym bota. Zmienna, ale płynna i ułamkowa; rozmiar pozycji jest automatycznie przycinany przez skalowanie wg zmienności.",
  },
  GLD: {
    name: "SPDR Gold Shares",
    description:
      "ETF odwzorowujący cenę złota. Aktywo defensywne, często rośnie, gdy akcje spadają albo rośnie niepewność/inflacja — nieskorelowane z tech. Daje botowi gdzie się schować, gdy rynek akcji słabnie.",
  },
  TLT: {
    name: "iShares 20+ Year Treasury Bond",
    description:
      "ETF długoterminowych obligacji skarbowych USA. Klasyczny „risk-off” — zwykle zyskuje, gdy inwestorzy uciekają z akcji do bezpieczeństwa. Mocno reaguje na stopy procentowe. Uzupełnia portfel o coś, co zwykle zachowuje się odwrotnie niż SPY/QQQ.",
  },
  XLE: {
    name: "Energy Select Sector SPDR",
    description:
      "ETF sektora energetycznego (spółki naftowe/gazowe). Napędzany cenami ropy, często idzie własnym rytmem względem tech — dobra dywersyfikacja i ekspozycja na inflację surowcową.",
  },
  IWM: {
    name: "iShares Russell 2000 (small caps)",
    description:
      "ETF 2000 mniejszych spółek amerykańskich. Bardziej wrażliwy na kondycję krajowej gospodarki i apetyt na ryzyko niż wielkie techy — bywa liderem odbić i wcześnie sygnalizuje zmiany nastroju.",
  },
  SH: {
    name: "ProShares Short S&P 500 (inverse)",
    description:
      "ETF ODWROTNY — rośnie, gdy S&P 500 spada (1x, bez lewara). Pozwala botowi ZARABIAĆ na spadkach kupując go jak zwykłą pozycję, bez ryzyka klasycznego shorta (strata ograniczona jak przy każdym long). Używany, gdy rynek jest w trendzie spadkowym.",
  },
  PSQ: {
    name: "ProShares Short QQQ (inverse Nasdaq)",
    description:
      "ETF ODWROTNY do Nasdaq-100 — rośnie, gdy tech spada (1x, bez lewara). Odpowiednik SH, ale wycelowany w sektor technologiczny. Sposób na grę pod korektę tech bez shortowania z nieograniczoną stratą.",
  },
  // --- Portfel nocny eToro: krypto (spot) + forex ---
  BTC: {
    name: "Bitcoin",
    description:
      "Największa i najpłynniejsza kryptowaluta, handlowana 24/7 (także w weekend) — rdzeń portfela nocnego. Zmienna, ale spot (bez dźwigni), więc strata ograniczona jak przy każdej długiej pozycji. Reaguje mocno na newsy o ETF-ach, regulacjach i przepływach on-chain.",
  },
  ETH: {
    name: "Ethereum",
    description:
      "Druga co do wielkości kryptowaluta, baza dla DeFi i większości tokenów. Trochę bardziej zmienna niż BTC, często podąża za nim z większą amplitudą. Spot, 24/7.",
  },
  SOL: {
    name: "Solana",
    description:
      "Szybki, wysokobetowy blockchain warstwy 1 — potrafi ruszyć się mocniej niż BTC/ETH w obie strony. Płynny, ale bardziej ryzykowny; rozmiar pozycji przycina skalowanie wg zmienności.",
  },
  EURUSD: {
    name: "EUR/USD (forex)",
    description:
      "Najpłynniejsza para walutowa świata, handel 24/5. Napędzana decyzjami banków centralnych (EBC/Fed) i danymi makro. Na eToro to instrument CFD — ruchy zwykle mniejsze niż krypto.",
  },
  GBPUSD: {
    name: "GBP/USD (forex)",
    description:
      "Funt do dolara — płynna para 24/5, bardziej zmienna niż EUR/USD, wrażliwa na dane z UK i USA oraz nastroje risk-on/risk-off.",
  },
  USDJPY: {
    name: "USD/JPY (forex)",
    description:
      "Dolar do jena — bardzo płynna para 24/5, klasyczny barometr apetytu na ryzyko (jen to waluta „bezpiecznej przystani”). Silnie reaguje na różnice stóp procentowych USA/Japonia.",
  },
};

function fallbackInfo(ticker: string): TickerInfo {
  return {
    name: ticker,
    description: "Ticker na liście handlowej automatu — decyzje o nim podejmuje Claude na tych samych zasadach co pozostałe pozycje w portfelu.",
  };
}

export function InvestmentThesis({ whitelist }: { whitelist: string[] }) {
  // Collapsed by default: with 11 tickers the full card grid is a wall of
  // static text pushing the live panels (chart, positions) below the fold.
  const [expanded, setExpanded] = useState(false);

  if (whitelist.length === 0) return null;

  return (
    <div className="panel" style={{ marginBottom: 16 }}>
      <button
        type="button"
        className="thesis-toggle"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        <h2 style={{ margin: 0 }}>Inwestuję w</h2>
        <span className="thesis-toggle-summary">
          {whitelist.join(" · ")}
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            aria-hidden="true"
            style={{ transform: expanded ? "rotate(180deg)" : "none", transition: "transform 0.2s ease" }}
          >
            <path d="M2 4 L6 8 L10 4" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" />
          </svg>
        </span>
      </button>
      {expanded && (
        <>
          <p className="subtitle" style={{ marginTop: 8, marginBottom: 12 }}>
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
        </>
      )}
    </div>
  );
}
