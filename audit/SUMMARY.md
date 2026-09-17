# Audyt GielDarek — 2026-09-17T17:35:54Z

**Wdrożenie:** kod 889cebd (zbud. 2026-09-15T18:25Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 62 zamknięć · trafność 32.3% · zrealizowany $-6.29
**7 dni:** 14 zamknięć · 42.9% · $-8.53   |   **30 dni:** 43 · 34.9% · $-14.89
**Edge:** śr. wygrana +$2.16 vs strata $-1.18 → na transakcję $-0.1 (payoff 1.83×)
**Trzymanie:** zyski ~3.6 dni · straty ~2.6 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 62 zamknięć, trafność 32% — pod kreską (−$6.29).
- (good) Trafność 7 dni 43% vs 30 dni 35% — rośnie.
- (bad) Ostatnie 7 dni: -8.53 $ z 14 zamknięć.
- (bad) Średnia wygrana +$2.16 vs strata −$1.18 (wygrana 1.83× większa) → na transakcję −$0.10. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.33 $, 3 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (7 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.33 (3 zamk., 0%)
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
- ostatnie 120 decyzji · wykonanych: 39 · odrzuconych: 81

**Najczęstsze powody odrzucenia (top):**
- 63× — brak powodu
- 5× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2× — Zbyt niska pewność: 0.62 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.63 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
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
- 2026-09-17T13:56:21.434657 META BUY conf=0.65 trig=scheduled_daily ✅WYKONANE
- 2026-09-17T13:56:16.481714 V SELL conf=0.55 trig=scheduled_daily ✅WYKONANE
- 2026-09-16T19:56:03.737199 GOOGL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-16T19:55:58.561081 GLD SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-16T19:25:53.461941 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-16T18:55:55.803882 META SELL conf=0.75 trig=news_event ✅WYKONANE
- 2026-09-16T18:25:56.166741 AVGO SELL conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-16T17:55:56.829376 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T17:27:37.694801 — HOLD conf=0.6 trig=manual ⛔ ?
