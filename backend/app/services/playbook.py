"""Trwała baza wiedzy ("playbook") -- zestaw zasad zachowania destylowany z
praktyki doświadczonych traderów i systemowych botów. W ODRÓŻNIENIU od
`lessons_json` (które Claude sam dopisuje z własnej historii i które rotują),
playbook jest STAŁY: zawsze doklejany do kontekstu decyzji jako baza, na której
Claude buduje własne, świeższe lekcje. To jest ta "baza zachowań zbudowana na
podstawie historii innych traderów i aplikacji", od której startujemy.

Zasady są celowo krótkie, konkretne i wykonalne -- nie ogólniki. Karmione do
Claude przez trading_engine.build_performance_context -> your_performance.playbook.
"""

SEED_PLAYBOOK: list[str] = [
    # Ryzyko i rozmiar -- fundament przetrwania na małym koncie.
    "Tnij straty szybko, pozwól zyskom rosnąć — asymetria (mały stop, duży bieg) jest ważniejsza niż trafność.",
    "Ryzykuj mały % konta na pojedynczą transakcję; nigdy nie stawiaj konta na jedną nazwę.",
    "Nie uśredniaj w dół stratnej pozycji — dokładasz do błędu; dokładaj tylko do tego, co już działa.",
    "Po stop-lossie nie odkupuj tej samej nazwy z zemsty — czekaj na wyraźnie NOWY, mocniejszy sygnał.",
    # Trend, reżim, timing.
    "Handluj ZGODNIE z trendem; nie łap spadających noży i nie graj przeciw tape.",
    "Silny trend potrafi być 'wykupiony' długo — wysokie RSI w realnym trendzie to norma, nie sygnał wyjścia.",
    "Dostosuj agresję do reżimu: w risk-off / wysokim VIX zmniejsz rozmiar albo siedź w gotówce. Gotówka to pełnoprawna pozycja.",
    "Kupuj siłę względną (nazwy mocniejsze od rynku), unikaj słabości względnej w słabym tape.",
    # Przewaga informacyjna -- to, czego kalkulator nie policzy.
    "Świeży, materialny katalizator z newsów bije sam setup techniczny — reaguj szybko na to, co WŁAŚNIE się opublikowało.",
    "Uwaga na luki po earnings: stop-loss NIE chroni przed przeskokiem ceny — nie otwieraj świeżej pozycji tuż przed raportem.",
    "Odróżniaj sygnał od szumu: jeden wyraźny powód wejścia + katalizator wystarczy; nie potrzebujesz konfluencji wszystkiego.",
    # Koszty, płynność, dyscyplina -- co zabija małe konta.
    "Płynność ma znaczenie: unikaj cienkich nazw z szerokim spreadem — koszty round-tripu zjadają małe konto.",
    "Overtrading zabija: seria drobnych, wysoko-prawdopodobnych zysków SKŁADA się w wynik, ale handel dla samego handlu to koszt.",
    "Wiele nazw tech to często JEDNA korelacyjna transakcja — dywersyfikuj czynnik ryzyka, nie tylko tickery.",
    "Trzymaj tezę per pozycja: wychodź, gdy teza się ŁAMIE, a nie na przypadkowym szumie. Nie mikrozarządzaj wyjściami — od tego są mechaniczne stopy.",
    # Meta -- jak się uczyć.
    "Preferuj tickery z dodatnią własną historią (per_symbol_stats), odpuszczaj te z powtarzalnymi stratami.",
    "Bądź uczciwy co do pewności — zawyżona pewność, byle wejść, tylko marnuje cykl i kapitał.",
]


# Krypto (venue 24/7) -- doklejane do playbooka TYLKO dla nogi krypto. Koduje
# naszą strategię + TWARDE lekcje z 4 miesięcy akcji (patrz docs/), żeby gdy
# właściciel włączy LLM (Sonnet), model startował Z TĄ wiedzą, nie na zimno.
SEED_PLAYBOOK_CRYPTO: list[str] = [
    "Poprzeczka to TRZYMANIE BTC, nie 'czy zarobiłem': jeśli aktywny handel nie bije buy&hold BTC w oknie — lepiej po prostu trzymać BTC.",
    "Płynność > egzotyka: graj WĄSKĄ listą najpłynniejszych par (BTC/ETH/SOL/majors). Śmieciowe alty = szeroki spread + dumpy; to był największy przeciek na akcjach.",
    "Fee ~0,1–0,25%/stronę + spread to STAŁY koszt: mniej, większych, dłużej trzymanych pozycji bije częsty scalping, który zżerają koszty.",
    "Krypto bywa silnie trendujące ORAZ brutalnie zmienne: szersze stopy (pod zmienność), mniejszy % ryzyka/transakcję niż na akcjach.",
    "Korelacja: większość altów to lewarowany BTC — 5 altów to często JEDNA transakcja na BTC. Nie udawaj dywersyfikacji; licz ryzyko na czynnik, nie na ticker.",
    "Nie goń świeżego pumpa z FOMO: do czasu wejścia ruch zwykle już się wydarzył. Czekaj na potwierdzony setup, nie na nagłówek.",
    "Ekstremalny funding / masowo zatłoczone longi/shorty bywają sygnałem KONTRARIAŃSKIM (nadchodzą likwidacje) — nie dokładaj do tłumu na szczycie.",
    "24/7 = brak luki na otwarciu, ale cieńsza płynność nocą/w weekend i nagłe knoty. Większa ostrożność z rozmiarem poza godzinami US.",
    "Największym kosztem przy małym koncie był LLM (~$196 na akcjach): wołaj drogi model tylko do decyzji WYSOKIEJ wartości, nie na każdy cykl. Gotówka to pełnoprawna pozycja.",
]


def get_playbook(venue: str = "alpaca") -> list[str]:
    """Kopia listy zasad (żeby wołający jej nie zmutował). Dla venue 'crypto'
    dokleja zasady krypto -- tak, by LLM (gdy włączony) startował z tą wiedzą."""
    rules = list(SEED_PLAYBOOK)
    if venue == "crypto":
        rules += SEED_PLAYBOOK_CRYPTO
    return rules
