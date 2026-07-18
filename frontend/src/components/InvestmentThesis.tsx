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
  DIA: {
    name: "SPDR Dow Jones Industrial Average",
    description:
      "ETF na indeks Dow Jones — 30 dużych, dojrzałych spółek przemysłowo-usługowych. Mniej tech niż SPY/QQQ, spokojniejszy, „stary” rdzeń rynku. Dobra przeciwwaga dla technologicznej części listy.",
  },
  SLV: {
    name: "iShares Silver Trust",
    description:
      "ETF odwzorowujący cenę srebra. Jak złoto (GLD), ale bardziej zmienny — łączy cechy metalu szlachetnego (risk-off) i surowca przemysłowego. Dywersyfikacja poza akcje.",
  },
  XLF: {
    name: "Financial Select Sector SPDR",
    description:
      "ETF sektora finansowego (banki, ubezpieczyciele). Wrażliwy na stopy procentowe i cykl gospodarczy — często prowadzi, gdy rynek stawia na wzrost i wyższe stopy. Nieskorelowany z tech.",
  },
  XLK: {
    name: "Technology Select Sector SPDR",
    description:
      "ETF sektora technologicznego (podobny do QQQ, ale czysty sektor). Ekspozycja na trend tech bez pojedynczej spółki — sposób, by grać momentum technologii z mniejszym ryzykiem jednej nazwy.",
  },
  XLV: {
    name: "Health Care Select Sector SPDR",
    description:
      "ETF sektora ochrony zdrowia (farma, biotech, sprzęt medyczny). Klasyczny defensywny sektor — popyt stabilny niezależnie od cyklu, często trzyma się lepiej w słabszym rynku.",
  },
  XLU: {
    name: "Utilities Select Sector SPDR",
    description:
      "ETF sektora użyteczności publicznej (energetyka, woda). Najbardziej defensywny sektor, płaci dywidendy, zachowuje się jak „obligacyjny” — zwykle mocny w risk-off i przy spadających stopach.",
  },
  XLI: {
    name: "Industrial Select Sector SPDR",
    description:
      "ETF sektora przemysłowego (lotnictwo, maszyny, logistyka). Cykliczny — rośnie, gdy gospodarka przyspiesza. Barometr realnej aktywności gospodarczej, inny rytm niż tech.",
  },
  XLP: {
    name: "Consumer Staples Select Sector SPDR",
    description:
      "ETF dóbr podstawowych (żywność, napoje, chemia domowa). Defensywny — ludzie kupują je zawsze, więc trzyma się stabilnie w bessie. Schronienie, gdy apetyt na ryzyko spada.",
  },
  EEM: {
    name: "iShares MSCI Emerging Markets",
    description:
      "ETF rynków wschodzących (Chiny, Indie, Brazylia i in.). Ekspozycja poza USA — inny cykl, wrażliwy na dolara i surowce. Dywersyfikacja geograficzna wobec amerykańskiej reszty listy.",
  },
  EFA: {
    name: "iShares MSCI EAFE (rynki rozwinięte ex-US)",
    description:
      "ETF rozwiniętych rynków poza USA (Europa, Japonia, Australia). Pozwala botowi złapać trend, gdy to rynki zagraniczne, a nie amerykańskie, są liderem.",
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
  // --- Portfel krypto (24/7, spot, to samo konto Alpaca) ---
  BTCUSD: {
    name: "Bitcoin",
    description:
      "Największa i najpłynniejsza kryptowaluta, handlowana 24/7 (także w weekend) — rdzeń portfela krypto. Zmienna, ale spot (bez dźwigni), więc strata ograniczona jak przy każdej długiej pozycji. Reaguje mocno na newsy o ETF-ach, regulacjach i przepływach on-chain.",
  },
  ETHUSD: {
    name: "Ethereum",
    description:
      "Druga co do wielkości kryptowaluta, baza dla DeFi i większości tokenów. Trochę bardziej zmienna niż BTC, często podąża za nim z większą amplitudą. Spot, 24/7.",
  },
  LTCUSD: {
    name: "Litecoin",
    description:
      "Jedna z najstarszych kryptowalut, „srebro do bitcoinowego złota”. Płynna, zwykle podąża za BTC z podobną lub nieco większą amplitudą. Spot, 24/7.",
  },
  BCHUSD: {
    name: "Bitcoin Cash",
    description:
      "Fork bitcoina nastawiony na tańsze płatności. Płynny altcoin, koreluje z BTC. Spot, 24/7; rozmiar przycina skalowanie wg zmienności.",
  },
  DOGEUSD: {
    name: "Dogecoin",
    description:
      "Kryptowaluta „memowa”, bardzo zmienna i napędzana sentymentem/social media (Elon). Wysokie ryzyko i amplituda — spot, 24/7, rozmiar mocno przycinany przez skalowanie wg zmienności.",
  },
  LINKUSD: {
    name: "Chainlink",
    description:
      "Sieć oracle łącząca blockchain z danymi ze świata rzeczywistego — infrastrukturalny token DeFi. Wysokobetowy altcoin, podąża za sentymentem krypto z większą amplitudą niż BTC. Spot, 24/7.",
  },
  AVAXUSD: {
    name: "Avalanche",
    description:
      "Szybki blockchain warstwy 1, konkurent Ethereum dla DeFi i aplikacji. Wysokobetowy altcoin — potrafi ruszyć się mocniej niż BTC/ETH w obie strony. Spot, 24/7.",
  },
  ADAUSD: {
    name: "Cardano",
    description:
      "Blockchain warstwy 1 (proof-of-stake). Wysokobetowy altcoin — potrafi ruszyć się mocniej niż BTC/ETH. Spot, 24/7; rozmiar przycina skalowanie wg zmienności.",
  },
  SOLUSD: {
    name: "Solana",
    description:
      "Szybki, wysokobetowy blockchain warstwy 1 — potrafi ruszyć się mocniej niż BTC/ETH w obie strony. Płynny, ale bardziej ryzykowny; rozmiar pozycji przycina skalowanie wg zmienności. Spot, 24/7.",
  },
  DOTUSD: {
    name: "Polkadot",
    description:
      "Protokół łączący wiele blockchainów („internet blockchainów”). Wysokobetowy altcoin infrastrukturalny, podąża za sentymentem krypto z większą amplitudą niż BTC. Spot, 24/7.",
  },
  UNIUSD: {
    name: "Uniswap",
    description:
      "Token największej zdecentralizowanej giełdy (DEX) na Ethereum — barometr aktywności DeFi. Zmienny altcoin, mocno reaguje na newsy regulacyjne o DeFi. Spot, 24/7.",
  },
  AAVEUSD: {
    name: "Aave",
    description:
      "Token wiodącego protokołu pożyczkowego DeFi. Wysokobetowy altcoin „blue chip DeFi”, koreluje z ETH i ogólnym apetytem na ryzyko w krypto. Spot, 24/7.",
  },
  XRPUSD: {
    name: "XRP (Ripple)",
    description:
      "Kryptowaluta skupiona na płatnościach transgranicznych. Płynna, mocno reaguje na newsy regulacyjne (sprawy sądowe SEC). Spot, 24/7.",
  },
  SHIBUSD: {
    name: "Shiba Inu",
    description:
      "Kryptowaluta „memowa”, skrajnie zmienna i napędzana sentymentem/social media. Najbardziej ryzykowna, spekulacyjna pozycja krypto — rozmiar bardzo mocno przycinany przez skalowanie wg zmienności. Spot, 24/7.",
  },
  // --- Portfel akcji US: mega-capy tech + extended-proxy (dodane) ---
  MSFT: {
    name: "Microsoft Corp.",
    description:
      "Jeden z największych, najstabilniejszych „blue chipów” tech (chmura Azure, Office, AI/OpenAI). Bardzo płynny, spokojniejszy niż NVDA/TSLA — rdzeń koszyka tech.",
  },
  AMZN: {
    name: "Amazon.com Inc.",
    description:
      "Gigant e-commerce i chmury (AWS). Płynny mega-cap, reaguje na wyniki kwartalne i dane o konsumencie. Ekspozycja na handel detaliczny + chmurę w jednej nazwie.",
  },
  GOOGL: {
    name: "Alphabet (Google)",
    description:
      "Dominujący gracz w wyszukiwarce, reklamie i AI (Gemini). Płynny mega-cap tech, spokojniejszy profil niż półprzewodniki, wrażliwy na newsy o AI i regulacjach.",
  },
  META: {
    name: "Meta Platforms",
    description:
      "Właściciel Facebooka, Instagrama i WhatsAppa — reklama cyfrowa + inwestycje w AI/VR. Zmienniejszy niż MSFT, mocno reaguje na wyniki i wydatki na AI.",
  },
  AMD: {
    name: "Advanced Micro Devices",
    description:
      "Producent procesorów i układów AI, główny konkurent Nvidii. Wysokobetowy — mocno napędzany cyklem AI/półprzewodników, zmienny jak NVDA. Rozmiar przycinany wg zmienności.",
  },
  AVGO: {
    name: "Broadcom Inc.",
    description:
      "Gigant półprzewodników i oprogramowania infrastrukturalnego, kluczowy dostawca układów AI/sieciowych. Płynny, wysokobetowy beneficjent trendu AI.",
  },
  NFLX: {
    name: "Netflix Inc.",
    description:
      "Lider streamingu. Zmienny mega-cap, wyraźnie reaguje na dane o subskrybentach i wyniki kwartalne. Inny cykl niż półprzewodniki — dywersyfikacja w ramach tech.",
  },
  COIN: {
    name: "Coinbase Global",
    description:
      "Największa notowana giełda krypto w USA — akcja poruszająca się razem z kursem BTC/krypto. Dzienny „odpowiednik” portfela krypto: pozwala grać sentyment krypto także w sesji US. Wysokobetowa, rozmiar przycinany wg zmienności.",
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
