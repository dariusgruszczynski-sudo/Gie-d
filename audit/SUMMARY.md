# Audyt GielDarek — 2026-09-17T10:42:41Z

**Wdrożenie:** kod 889cebd (zbud. 2026-09-15T18:25Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 58 zamknięć · trafność 29.3% · zrealizowany $-6.89
**7 dni:** 10 zamknięć · 30.0% · $-9.13   |   **30 dni:** 40 · 30.0% · $-18.04
**Edge:** śr. wygrana +$2.46 vs strata $-1.19 → na transakcję $-0.12 (payoff 2.07×)
**Trzymanie:** zyski ~4.0 dni · straty ~2.6 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 58 zamknięć, trafność 29% — pod kreską (−$6.89).
- (neu) Trafność 7 dni 30% vs 30 dni 30% — stabilna.
- (bad) Ostatnie 7 dni: -9.13 $ z 10 zamknięć.
- (bad) Średnia wygrana +$2.46 vs strata −$1.19 (wygrana 2.07× większa) → na transakcję −$0.12. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.33 $, 3 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (6 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.33 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.16 (2 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- NVDA: $-2.4 (5 zamk., 20%)
- GLD: $-2.37 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- V: $-1.54 (1 zamk., 0%)

## Wejścia vs limit
- cap 6/dzień · max w dniu 57 · dni z limitem 6 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 31 · odrzuconych: 89

**Najczęstsze powody odrzucenia (top):**
- 63× — brak powodu
- 9× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2× — Zbyt niska pewność: 0.62 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.63 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-16T19:56:03.737199 GOOGL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-16T19:55:58.561081 GLD SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-16T19:25:53.461941 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-16T18:55:55.803882 META SELL conf=0.75 trig=news_event ✅WYKONANE
- 2026-09-16T18:25:56.166741 AVGO SELL conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-16T17:55:56.829376 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T17:27:37.694801 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-09-16T17:25:52.524184 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T16:55:54.998963 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T16:25:59.135106 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T15:55:59.205962 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T15:25:58.288300 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T15:17:09.114921 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-09-16T14:56:01.003773 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-16T14:25:58.903946 META SELL conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-16T13:56:13.455629 — HOLD conf=0.6 trig=scheduled_daily ⛔ ?
- 2026-09-15T19:55:53.324116 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-15T19:25:54.727274 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-15T18:56:11.016366 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-15T18:17:47.920529 — HOLD conf=0.0 trig=news_event ⛔ ?
