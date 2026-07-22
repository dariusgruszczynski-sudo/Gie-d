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


def get_playbook() -> list[str]:
    """Kopia listy zasad (żeby wołający jej nie zmutował)."""
    return list(SEED_PLAYBOOK)
