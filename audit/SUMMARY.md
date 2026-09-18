# Audyt GielDarek — 2026-09-18T19:33:25Z

**Wdrożenie:** kod 77e005f (zbud. 2026-09-18T18:42Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 67 zamknięć · trafność 32.8% · zrealizowany $-6.72
**7 dni:** 16 zamknięć · 50.0% · $-1.42   |   **30 dni:** 47 · 36.2% · $-13.56
**Edge:** śr. wygrana +$1.98 vs strata $-1.12 → na transakcję $-0.1 (payoff 1.77×)
**Trzymanie:** zyski ~3.6 dni · straty ~2.5 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 67 zamknięć, trafność 33% — pod kreską (−$6.72).
- (good) Trafność 7 dni 50% vs 30 dni 36% — rośnie.
- (bad) Ostatnie 7 dni: -1.42 $ z 16 zamknięć.
- (bad) Średnia wygrana +$1.98 vs strata −$1.12 (wygrana 1.77× większa) → na transakcję −$0.10. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.86 $, 4 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (8 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.86 (4 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.16 (2 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- NVDA: $-1.56 (6 zamk., 33%)

## Wejścia vs limit
- cap 6/dzień · max w dniu 57 · dni z limitem 8 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 48 · odrzuconych: 72

**Najczęstsze powody odrzucenia (top):**
- 58× — brak powodu
- 5× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-18T19:13:16.300004 SMH BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-09-18T19:13:11.380683 AAPL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-18T19:13:11.363620 META SELL conf=0.5 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-18T18:25:57.664422 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T17:55:52.983972 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T17:27:14.117915 SMH BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-09-18T17:27:09.656060 GOOGL BUY conf=0.62 trig=manual ✅WYKONANE
- 2026-09-18T17:27:03.821533 LLY SELL conf=0.55 trig=manual ✅WYKONANE
- 2026-09-18T17:25:53.142856 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T16:55:54.177102 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T16:26:01.044878 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T15:55:51.268642 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-18T15:25:56.727801 LLY BUY conf=0.6 trig=news_event ⛔ Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-18T14:55:57.815101 GOOGL SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-18T14:26:00.145059 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T13:56:20.939692 AAPL BUY conf=0.65 trig=price_move ✅WYKONANE
- 2026-09-18T13:56:15.783555 GOOGL BUY conf=0.62 trig=price_move ✅WYKONANE
- 2026-09-17T19:56:05.346726 GOOGL BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T19:56:05.320721 META BUY conf=0.65 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T19:56:00.240481 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
