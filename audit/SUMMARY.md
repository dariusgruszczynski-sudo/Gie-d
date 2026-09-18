# Audyt GielDarek — 2026-09-18T16:08:23Z

**Wdrożenie:** kod 889cebd (zbud. 2026-09-15T18:25Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 66 zamknięć · trafność 33.3% · zrealizowany $-6.72
**7 dni:** 15 zamknięć · 53.3% · $-1.42   |   **30 dni:** 46 · 37.0% · $-13.56
**Edge:** śr. wygrana +$1.98 vs strata $-1.14 → na transakcję $-0.1 (payoff 1.74×)
**Trzymanie:** zyski ~3.6 dni · straty ~2.5 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 66 zamknięć, trafność 33% — pod kreską (−$6.72).
- (good) Trafność 7 dni 53% vs 30 dni 37% — rośnie.
- (bad) Ostatnie 7 dni: -1.42 $ z 15 zamknięć.
- (bad) Średnia wygrana +$1.98 vs strata −$1.14 (wygrana 1.74× większa) → na transakcję −$0.10. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.86 $, 4 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (7 dni) — podniesienie może dołożyć wejść.
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
- cap 6/dzień · max w dniu 57 · dni z limitem 7 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 43 · odrzuconych: 77

**Najczęstsze powody odrzucenia (top):**
- 59× — brak powodu
- 5× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-18T15:55:51.268642 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-18T15:25:56.727801 LLY BUY conf=0.6 trig=news_event ⛔ Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-18T14:55:57.815101 GOOGL SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-18T14:26:00.145059 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T13:56:20.939692 AAPL BUY conf=0.65 trig=price_move ✅WYKONANE
- 2026-09-18T13:56:15.783555 GOOGL BUY conf=0.62 trig=price_move ✅WYKONANE
- 2026-09-17T19:56:05.346726 GOOGL BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T19:56:05.320721 META BUY conf=0.65 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T19:56:00.240481 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-17T19:25:56.327782 AVGO BUY conf=0.55 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T19:25:56.313077 META BUY conf=0.62 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T18:55:57.286176 GOOGL SELL conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-17T18:26:00.609283 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-17T17:56:06.633463 AAPL BUY conf=0.62 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-17T17:56:01.602722 GOOGL SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-17T17:26:00.855130 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-17T16:56:04.146219 AAPL BUY conf=0.63 trig=news_event ✅WYKONANE
- 2026-09-17T16:55:59.043178 GOOGL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-17T16:26:01.418620 META SELL conf=0.75 trig=news_event ✅WYKONANE
- 2026-09-17T15:56:03.438301 GOOGL BUY conf=0.62 trig=news_event ✅WYKONANE
