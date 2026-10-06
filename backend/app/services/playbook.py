"""Trwała baza wiedzy ("playbook") -- zestaw zasad zachowania destylowany z
praktyki doświadczonych traderów i systemowych botów. W ODRÓŻNIENIU od
`lessons_json` (które Claude sam dopisuje z własnej historii i które rotują),
playbook jest STAŁY: zawsze doklejany do kontekstu decyzji jako baza, na której
Claude buduje własne, świeższe lekcje. To jest ta "baza zachowań zbudowana na
podstawie historii innych traderów i aplikacji", od której startujemy.

Zasady są celowo krótkie, konkretne i wykonalne -- nie ogólniki. Karmione do
Claude przez trading_engine.build_performance_context -> your_performance.playbook.
"""

# Każda zasada ma format "Kategoria · treść" -- pozwala UI pogrupować je w domeny
# (jak realny playbook), a LLM-owi czytać tematycznie zamiast płaskiej listy.
SEED_PLAYBOOK: list[str] = [
    # --- Ryzyko i rozmiar: matematyka przetrwania, nie przeczucie. ---
    "Ryzyko i rozmiar · Przewagę daje ASYMETRIA, nie trafność: system 40%/2,5R bije 60%/1R. Pilnuj stosunku średniej wygranej do średniej straty (payoff), a nie samego win-rate.",
    "Ryzyko i rozmiar · Ryzykuj stały, mały % konta na transakcję liczony DO odległości stopa (odległość do stopa × rozmiar = stała kwota R). Tak samo bolesny stop na każdej nazwie, niezależnie od ceny nominalnej.",
    "Ryzyko i rozmiar · Rozmiar pod ZMIENNOŚĆ: skaluj pozycję odwrotnie do ATR/zmienności, żeby $-ryzyko było równe między aktywami. Stały % bez korekty o vol = w zmiennej nazwie bierzesz wielokrotność ryzyka.",
    "Ryzyko i rozmiar · Nie uśredniaj w dół stratnej pozycji — dokładasz do błędu. Dokładać (piramidować) wolno tylko do tego, co już pracuje na plus, przesuwając stop za ceną.",
    "Ryzyko i rozmiar · Skorelowane nazwy to JEDNA transakcja na czynnik ryzyka — licz i tnij ekspozycję na czynnik, nie liczbę tickerów. Pozorna dywersyfikacja znika w zjeździe, gdy korelacje idą do 1.",
    # --- Reżim i trend: najpierw zdiagnozuj rynek, potem wybierz narzędzie. ---
    "Reżim i trend · Handluj zgodnie z trendem wyższego interwału; nie łap spadających noży ani nie graj przeciw tape. Kierunek wyższego TF ma pierwszeństwo przed sygnałem niższego.",
    "Reżim i trend · W realnym trendzie 'wykupienie' (wysokie RSI) utrzymuje się długo — to norma, nie sygnał wyjścia. Z pozycji wyrzuca złamanie STRUKTURY, nie sam oscylator.",
    "Reżim i trend · Jeden reżim, jedno narzędzie: w trendzie graj kontynuację i pozwól biec; w zakresie graj powrót do średniej od krawędzi, nie wybicia. Mylenie reżimów to główne źródło strat.",
    "Reżim i trend · Dostosuj agresję do reżimu: risk-off / wysoka zmienność → mniejszy rozmiar albo gotówka. Gotówka to pełnoprawna pozycja, a nie brak decyzji.",
    "Reżim i trend · Kupuj siłę względną (mocniejsze od rynku), unikaj słabości względnej w słabym tape — kapitał płynie do liderów, nie do 'tanich' maruderów.",
    # --- Mikrostruktura i egzekucja: gdzie małe konto traci po cichu. ---
    "Mikrostruktura i egzekucja · Płynność i spread > cena nominalna: cienkie nazwy z szerokim spreadem i płytką księgą zjadają konto na poślizgu round-tripu, zanim edge zdąży zadziałać.",
    "Mikrostruktura i egzekucja · Luka po binarnym evencie (wynik/odblokowanie) PRZESKAKUJE stop — nie otwieraj świeżej pozycji tuż przed znanym, dwustronnym wydarzeniem; stop nie chroni przed gapem.",
    # --- Sentyment i katalizatory: przewaga, której kalkulator nie policzy. ---
    "Sentyment i narracja · Świeży, materialny katalizator bije sam setup techniczny — ale reaguj na to, co WŁAŚNIE się opublikowało, nie na odgrzewany nagłówek, który rynek już wycenił.",
    "Sentyment i narracja · Odróżniaj sygnał od szumu: jeden wyraźny powód wejścia + katalizator wystarczy. Czekanie na konfluencję wszystkiego naraz = wejście po fakcie.",
    # --- Proces i meta: jak nie oszukiwać samego siebie. ---
    "Proces i meta · Overtrading zabija: seria drobnych, wysoko-prawdopodobnych zysków SKŁADA się w wynik; handel dla samego handlu to czysty koszt (fee + spread + błędy).",
    "Proces i meta · Trzymaj TEZĘ per pozycja: wychodź, gdy teza się łamie, nie na losowym szumie. Od mikrozarządzania wyjściami są mechaniczne stopy/cele, nie emocje.",
    "Proces i meta · Preferuj nazwy z dodatnią własną historią (per_symbol_stats), odpuszczaj te z powtarzalnymi stratami — Twoja realizacja na danym rynku to też dane.",
    "Proces i meta · Oddzielaj DECYZJĘ od WYNIKU: dobra decyzja bywa stratna, zła — zyskowna. Oceniaj proces przy wiedzy z chwili wejścia, nie po tym, jak wyszła świeca.",
    "Proces i meta · Bądź uczciwy co do pewności — zawyżona pewność, byle wejść, marnuje kapitał i cykl. Podawaj realne prawdopodobieństwo, nie życzeniowe.",
]


# Krypto (venue 24/7) -- doklejane do playbooka TYLKO dla nogi krypto. Koduje
# strategię + TWARDE lekcje z 4 miesięcy akcji (patrz docs/) i jest napisane pod
# DANE, które realnie podajemy modelowi: cena + wskaźniki (RSI/SMA/ATR), funding,
# open interest i long/short z rynku perpetualów oraz Fear&Greed. Dzięki temu gdy
# właściciel włączy LLM (Sonnet), model startuje z operacyjną wiedzą, nie na zimno.
SEED_PLAYBOOK_CRYPTO: list[str] = [
    # --- Ryzyko i rozmiar w świecie 24/7 i wysokiej zmienności. ---
    "Ryzyko i rozmiar · Stop pod STRUKTURĄ + bufor zmienności (≈1,5–2,5× ATR), nie na okrągłej liczbie ani ciasnym %: ciasny stop w krypto to pewna egzekucja na losowym knocie. Lepiej mniejszy rozmiar i sensowny stop niż duży rozmiar i stop, który rynek zdejmie szumem.",
    "Ryzyko i rozmiar · Alty to lewarowany beta-BTC — w zjeździe korelacja idzie do ~1, więc 4 longi na altach to jeden duży long na BTC. Sumuj ekspozycję beta do BTC i tnij ją, zamiast liczyć nazwy.",
    "Ryzyko i rozmiar · Krypto potrafi być jednocześnie silnie trendujące i brutalnie zmienne: mniejszy % ryzyka na transakcję niż na akcjach i szersze, zmiennościowe stopy — przeżycie serii zmienności jest ważniejsze niż złapanie każdego ruchu.",
    # --- Reżim: BTC dyktuje cały koszyk. ---
    "Reżim i trend · BTC dyktuje reżim całego koszyka: nie otwieraj longów na altach, gdy BTC łamie strukturę w dół. 'Altseason' istnieje tylko przy stabilnym/rosnącym BTC; rosnąca dominacja BTC = kapitał ucieka z altów.",
    "Reżim i trend · Momentum to w krypto udokumentowana premia (refleksywne przepływy: lewar, likwidacje, narracja), ale w konsolidacji trend-following jest rozjeżdżany na piłę. Bierz sygnały trendowe TYLKO z filtrem reżimu (cena vs SMA200 + nachylenie, siła trendu).",
    # --- Funding / OI / pozycjonowanie: dane, które realnie masz. ---
    "Funding i pozycjonowanie · Funding to jednocześnie KOSZT NOŚNY i sentyment: utrzymująco dodatni = longi płacą (carry przeciw Tobie). Ekstremalny funding + rosnące OI = zatłoczony lewar → paliwo na kaskadę likwidacji w stronę PRZECIWNĄ do tłumu. Na ekstremach czytaj kontrariańsko, nie jako trend.",
    "Funding i pozycjonowanie · Ta sama świeca znaczy co innego zależnie od OI: wzrost ceny na SPADAJĄCYM OI = zamykanie shortów (short squeeze, słaba kontynuacja); wzrost na ROSNĄCYM OI = świeże longi i realny popyt.",
    "Funding i pozycjonowanie · Long/short ratio na skrajności (tłum masowo po jednej stronie) to ostrzeżenie, nie potwierdzenie — rynek najchętniej idzie tam, gdzie zlikwiduje najwięcej lewara (polowanie na płynność stopów).",
    # --- Mikrostruktura: koszty i płynność 24/7. ---
    "Mikrostruktura i egzekucja · Round-trip (2× taker fee + spread + poślizg) to twardy ubytek ~0,3–0,6% na starcie każdej transakcji. Mniej, większych, dłużej trzymanych pozycji bije częsty scalping, który koszty zjadają zanim edge zadziała.",
    "Mikrostruktura i egzekucja · Graj WĄSKĄ listą najpłynniejszych par (BTC/ETH/SOL/majors). Śmieciowe alty = szeroki spread + nagłe dumpy; cienka płynność była największym przeciekiem już na akcjach.",
    "Mikrostruktura i egzekucja · 24/7 znosi lukę na otwarciu, ale płynność jest cienka nocą US i w weekend — knoty i polowania na stopy są wtedy częstsze. Zmniejsz rozmiar poza sesją US i nie zostawiaj ciasnych stopów na weekend.",
    # --- Sentyment: kontrariańsko na ekstremach. ---
    "Sentyment i narracja · Fear&Greed działa kontrariańsko na EKSTREMACH (ekstremalny strach = historycznie lepsze R/R longów; ekstremalna chciwość = podwyższone ryzyko lokalnego szczytu) — to filtr kontekstu, nie samodzielny trigger.",
    "Sentyment i narracja · Nie goń świeżego pumpa z FOMO: do czasu wejścia ruch zwykle się już wydarzył, a Ty dostarczasz płynność tym, co wsiadł wcześniej. Kupuj potwierdzony setup albo cofnięcie do struktury, nie euforię.",
    # --- Proces i meta: poprzeczka to BTC, a nie zero. ---
    "Proces i meta · Poprzeczka to TRZYMANIE BTC, nie 'czy jestem na plusie': jeśli aktywny handel nie bije buy&hold BTC w oknie ≥ kilkudziesięciu transakcji, poprawnym ruchem jest trzymać BTC i wyłączyć handel.",
    "Proces i meta · Nie oceniaj edge na małej próbie: potrzeba ~50+ zamknięć, zanim win-rate/payoff coś znaczą. Do tego czasu trzymaj proces i NIE kręć knobami pod ostatnie kilka transakcji — to dopasowanie do szumu.",
    "Proces i meta · Największy koszt małego konta to LLM (~$196 na akcjach przy ~zerowym wyniku): drogi model tylko do decyzji WYSOKIEJ wartości, nie na każdy cykl. Mechanika (stopy/cele/konfluencja) prowadzi domyślnie za $0; LLM to weto i edge, nie rutyna.",
    # --- Dowody (research 2020-2026): co REALNIE ma przewagę w krypto. ---
    "Reżim i trend · DOWÓD: time-series momentum / trend-following to najmocniejsza, udokumentowana przewaga w krypto (dekada walk-forward; 2020-25 ~32%/rok, Sharpe ~1.6). Rdzeń strategii: podążaj za trendem wyższego TF z filtrem reżimu, nie zgaduj dołków.",
    "Ryzyko i rozmiar · DOWÓD: asymetria robi wynik — TNIJ STRATY szybko (stop zawsze), POZWÓL ZYSKOM BIEC. Nie ścinaj zwycięzcy sztywnym małym take-profitem (to ujemny skos). Lockuj część na partialu, resztę prowadź trailingiem; twardy TP tylko na paraboliczny blow-off.",
    "Ryzyko i rozmiar · DOWÓD: sizing pod ZMIENNOŚĆ (volatility targeting) poprawia zwrot skorygowany o ryzyko i spłaszcza obsunięcia — stałe $-ryzyko do stopa, mniej jednostek na zmienny alt, więcej na spokojny. Ale vol patrzy wstecz: luka/news potrafi przebić budżet, więc i tak twardy stop.",
    "Mikrostruktura i egzekucja · DOWÓD: koszty transakcyjne REALNIE zjadają momentum — wiele teoretycznie zyskownych portfeli traci istotność po fee+spread. Wniosek: mniej, dłuższych, wyższej-konwikcji pozycji; NIE scalping. 'Dynamiczny' = responsywny na zmianę trendu, nie 'więcej transakcji'.",
    "Reżim i trend · DOWÓD: w krypto cross-sectional momentum (ranking/rotacja między nazwami) jest SŁABSZY niż time-series. Nie przesadzaj z rotacją w pogoni za relatywną siłą — trzymaj trend, który działa; rotuj tylko, gdy wyraźnie się łamie.",
]


def get_playbook(venue: str = "alpaca") -> list[str]:
    """Kopia listy zasad (żeby wołający jej nie zmutował). Dla venue 'crypto'
    dokleja zasady krypto -- tak, by LLM (gdy włączony) startował z tą wiedzą.
    Każda zasada jest w formacie 'Kategoria · treść'."""
    rules = list(SEED_PLAYBOOK)
    if venue == "crypto":
        rules += SEED_PLAYBOOK_CRYPTO
    return rules
