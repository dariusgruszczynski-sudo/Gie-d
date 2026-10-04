# GielDarek krypto (paper) — kryteria wejścia na żywo + dziennik nauki

Cel: zebrać **uczciwe dowody** na papierze (sztuczny kapitał, 24/7, silnik
mechaniczny bez LLM), żeby decyzja o **realnej gotówce** była z danych, nie z emocji.
Start paper: **2026-10-04**.

## Twarde kryteria GO-LIVE (wszystkie muszą być spełnione)

Wchodzimy na żywo **tylko** gdy po oknie obserwacji **ŁĄCZNIE**:

1. **Próbka wystarczająca:** ≥ **50 zamkniętych** transakcji krypto **i** ≥ **3 tygodnie** handlu.
2. **Bije „trzymanie BTC":** skumulowany zwrot % strategii **>** buy-and-hold BTC
   w tym samym oknie. (To jest krypto-odpowiednik „bicia indeksu" — najważniejsze.)
3. **Dodatni edge:** expectancy/transakcję **> 0** (po fee) **i** trafność **powyżej
   progu opłacalności** dla osiągniętego payoffu.
4. **Obsunięcie do zniesienia:** max drawdown ≤ **25%**.
5. **Nie z 1–2 strzałów:** wynik nie jest dźwignięty przez kilka transakcji
   (sprawdzamy koncentrację — tak jak przy akcjach QQQ/SMH niosły cały tydzień).
6. **Koszt AI ≈ $0** (mechaniczny silnik — potwierdzamy, że tak zostaje).

**Nawet gdy wszystko zielone — wchodzimy MAŁO:** start na żywo ~$200–300, nie całość.
Skalujemy dopiero, gdy żywe wyniki potwierdzą paper (patrz analiza progów z 2026-10-01).

## Czerwone flagi — NIE wchodzimy (choćby reszta kusiła)
- Poniżej „trzymania BTC" w oknie. · Ujemny expectancy. · Drawdown > 30%.
- Próbka < 50 transakcji / < 3 tyg. · Wynik trzyma się na 1–2 szczęśliwych trejdach.

## Jak mierzymy (źródło prawdy)
Dane **wprost z brancha `audit-snapshots`** (zrzut co godzinę): `trades.json`
(filtr: venue=crypto / para z „/"), liczone average-cost walk — trafność, realized,
expectancy; benchmark = zwrot BTC w oknie. Niezależne od wielkości konta (paper $100k
czy realne $1k — te same %).

---

## Dziennik wniosków (tydzień po tygodniu)

> Dopisywany co tydzień przez nadzór. Najnowszy na górze.

### Tydzień 0 — start (2026-10-04)
- Paper włączony, konto $100k (sztuczne), silnik mechaniczny, LLM off.
- Zero transakcji jeszcze — zbieramy próbkę. Pierwszy realny wniosek po ~7 dniach.
