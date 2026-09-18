# Audyt GielDarek — 2026-09-18T10:18:06Z

**Wdrożenie:** kod 889cebd (zbud. 2026-09-15T18:25Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 65 zamknięć · trafność 33.8% · zrealizowany $-6.47
**7 dni:** 17 zamknięć · 47.1% · $-8.71   |   **30 dni:** 45 · 37.8% · $-13.31
**Edge:** śr. wygrana +$1.98 vs strata $-1.16 → na transakcję $-0.1 (payoff 1.71×)
**Trzymanie:** zyski ~3.6 dni · straty ~2.6 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 65 zamknięć, trafność 34% — pod kreską (−$6.47).
- (good) Trafność 7 dni 47% vs 30 dni 38% — rośnie.
- (bad) Ostatnie 7 dni: -8.71 $ z 17 zamknięć.
- (bad) Średnia wygrana +$1.98 vs strata −$1.16 (wygrana 1.71× większa) → na transakcję −$0.10. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
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
- ostatnie 120 decyzji · wykonanych: 41 · odrzuconych: 79

**Najczęstsze powody odrzucenia (top):**
- 59× — brak powodu
- 5× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 5× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.65 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
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
- 2026-09-17T15:55:58.171532 META SELL conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-17T15:25:54.436053 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-17T14:55:53.971674 GOOGL BUY conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-17T14:26:01.639032 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-17T13:56:30.056108 NVDA SELL conf=0.55 trig=scheduled_daily ✅WYKONANE
- 2026-09-17T13:56:25.741571 GOOGL BUY conf=0.62 trig=scheduled_daily ✅WYKONANE
