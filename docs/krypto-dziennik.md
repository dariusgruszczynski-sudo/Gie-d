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

### Wpis — 2026-10-08 (poluzowanie bramek wejścia — „bot ma się uczyć")
Nadzór pokazał: od wdrożenia 10 mechanizmów bot NIE zawarł ani jednej nowej
transakcji (konto płaskie, 100% gotówki) — nowe bramki (reżim HTF + wybicie +
ADX) w płaskim rynku są zbyt restrykcyjne. Na paperze cel to ZBIERAĆ DANE do
nauki, więc właściciel kazał poluzować. Zmiany (wyraźna prośba):
- `crypto_regime_filter_ma_period 200→100` (risk-on łapie szybciej),
- `crypto_breakout_lookback 20→10` (więcej wybić się kwalifikuje),
- `crypto_min_adx 20→12` (wpuszcza słabsze trendy).
UCZCIWIE: luźniej = WIĘCEJ wejść, ale NIŻSZA jakość/trejd (bliżej churnu z
backtestu). To świadomy kompromis pod naukę, nie pod „bić BTC". Reżim/stopy/
breaker dalej działają; wszystko reversible. Obserwujemy, czy wejścia ruszyły.

### Wpis — 2026-10-08 (strojenie ekspozycji: 1,5%×5 → 3,0%×4, decyzja z backtestu)
Backtest + sweep na 8 latach realnych danych (Yahoo, z runnera GitHub) pokazał,
że przy 10 mechanizmach bramki trzymają bota w gotówce → **1,5%×5 było
niedoinwestowane i przegrywało z trzymaniem BTC** (alpha ujemna). Frontiera
ryzyko/trejd × pozycje:
- 1,5%×5 (poprzednie): ~+550%, DD ~30%, **przegrywa z BTC**.
- 3,0%×4 (**wybrane, „agresywnie"**): +2713%, CAGR 51,8%, **Calmar 1,42**,
  alpha **+1363pp** vs BTC, DD ~37% (BTC: 77%).
Zmiana knoba `crypto_risk_per_trade_pct 1.5→3.0`, `crypto_max_concurrent_positions
5→4` (wyraźna zgoda właściciela). UCZCIWIE: backtest bez prowizji/slippage,
dzienny, 8-letni; 3% ryzyka/trejd to agresywnie (większe pojedyncze straty,
grubsze wahania na żywo). Bezpiecznik account-wide (30/40/55%) dalej chroni.
Obserwujemy żywy paper — werdykt dopiero na ≥50 zamknięciach / ~3 tyg.

### Wpis — 2026-10-07 (10/10 mechanizmów — dołożone wejścia #8/#9/#10)
Na prośbę właściciela („wszystko") dołożone 3 pozostałe (strona WEJŚĆ), po
doprowadzeniu świec OHLC do ścieżki wejścia (dotąd closes-only):
8. **Wejście na WYBICIE (Donchian 20)** — kup tylko gdy cena bije szczyt poprzednich 20 świec.
9. **Filtr siły trendu (ADX14 ≥ 20)** — wchodź tylko gdy trend realnie istnieje; pomija boki.
10. **Piramidowanie** — dokładka do WYGRYWAJĄCEGO (+8%) na nowym wybiciu, sufit 25% konta,
    nigdy do straty; zwolnione z limitu równoległych pozycji (dokładka ≠ nowy slot).
Nowe wskaźniki ADX (Wilder) i Donchian w `technical_indicators`; H/L pobierane z 200-świec.
⚠️ To strona WEJŚĆ — napięcie z lekcją „nie filtruj wejść restrykcyjnie". Wdrożone
świadomie na życzenie, każdy za knobem (wyłączalny), ale WARTO zwalidować backtestem na
prodzie, zanim uznamy je za poprawę. Testy 392/392, ruff czysty. 10/10 config-gated.

### Wpis — 2026-10-07 (10 mechanizmów podnoszących P(zysk), wdrożone 6/10)
Na prośbę właściciela („wszystkie") dołożone mechanizmy podnoszące
prawdopodobieństwo zysku, każdy za osobnym knobem (można wyłączyć przez `.env`;
akcje nietknięte — knoby bazowe off). **Wdrożone teraz (6):**
1. **Filtr reżimu HTF** — longi tylko gdy BTC nad SMA200 na D1; w chopie/bessie gotówka.
2. **Re-entry cooldown** — po KAŻDYM pełnym wyjściu blokada ponownego wejścia (180 min) — anty-churn.
3. **Trailing skalowany zmiennością** — podłoga trailingu = max(bazowy, 1.5×vol%); mniej wyrzutów na szumie.
4. **Cap ekspozycji** — brak nowych wejść przy ≥60% konta w grze (krypto skorelowane → „wszystko czerwone").
5. **Breaker serii strat** — 4 straty z rzędu dziś → pauza nowych wejść do rolki doby UTC.
7. **Pauza na przegrzaniu** — F&G ≥93 lub funding ≥0.15% → wstrzymanie nowych longów (twardziej niż de-risk).

**Czeka na backtest na prodzie (3):** #8 Donchian breakout, #9 ADX-gate, #10 piramidowanie —
wymagają świec OHLC w ścieżce wejścia (dziś tylko closes) i nie wrzucamy ich na ślepo.
#6 vol-targeting sizingu ~pokryte przez `volatility_adjusted_size`.
Uczciwie: 6 mechanizmów naraz = konfundowanie (nie odróżnimy per-mechanizm na małej
próbie). Dlatego config-gated — obserwujemy, czy churn/„wszystko czerwone" znika; w razie
czego wyłączamy pojedynczo. Testy 389/389, ruff czysty.

### Wpis interwencyjny — 2026-10-07 (diagnoza + fix trend-exitu)
Dane (venue=crypto, okno 2026-10-04 → 10-07, zrzut 14:22Z): **32 zamknięcia,
realized −$9 376, trafność 12% (4/28), expectancy −$293/trade**, śr. wygrana
**+0,34%** vs strata **−1,73%** (payoff 0.03×), mediana trzymania **3,9h**,
każda para na minusie. BTC w oknie ≈ **−1%** → aktywny handel **grubo przegrywa**
z trzymaniem BTC. Silnik żył (nie-halt, nie-paused), konto $87,8k, drawdown ~12%.

**Diagnoza (read-only):** winowajca to **trend-exit (SMA50 na 1h, bez bufora i
potwierdzenia)**. Sprawdzany co 15 min, pali się na pojedynczy tick pod średnią;
w płaskim rynku cena bez przerwy przecina SMA50 → zwycięzcy ścinani przy ~0%,
straty jadą do ~−1,7%, churn 32×/3 dni. To klasyczna porażka trend-followingu na
rynku **bocznym**, wzmocniona zbyt czułym exitem (jedno z „5 ulepszeń", dec6c2e).
Mechanika „pozwól zyskom biec" (breakeven 8% / ratchet 15% / hard-TP 40%) nigdy
nie dochodziła do głosu — trend-exit zamykał wcześniej.

**Fix (za zgodą właściciela „wdrażaj daleko"):** HARTOWANIE trend-exitu, zgodnie
z udokumentowaną lekcją „nie dokładać filtrów WEJŚĆ" — ruszamy tylko WYJŚCIE:
- bufor `crypto_trend_exit_buffer_pct=3%` (wyjście dopiero 3% pod średnią, nie tick),
- potwierdzenie `crypto_trend_exit_confirm_bars=2` (2 świece zamknięte pod średnią).
Reszta strategii bez zmian; knoby bazowe neutralne (akcje nietknięte). Próbka 3 dni
jest za mała na strojenie pod wynik, ale to usunięcie strukturalnie twitchy exitu,
nie curve-fit. Obserwujemy, czy payoff i trafność wracają do sensownych wartości.

### Tydzień 0 — start (2026-10-04)
- Paper włączony, konto $100k (sztuczne), silnik mechaniczny, LLM off.
- Zero transakcji jeszcze — zbieramy próbkę. Pierwszy realny wniosek po ~7 dniach.
