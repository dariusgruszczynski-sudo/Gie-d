# Audyt GielDarek — 2026-09-16T17:35:59Z

**Wdrożenie:** kod 889cebd (zbud. 2026-09-15T18:25Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 56 zamknięć · trafność 28.6% · zrealizowany $-6.98
**7 dni:** 8 zamknięć · 25.0% · $-9.23   |   **30 dni:** 38 · 28.9% · $-18.13
**Edge:** śr. wygrana +$2.59 vs strata $-1.21 → na transakcję $-0.13 (payoff 2.14×)
**Trzymanie:** zyski ~4.2 dni · straty ~2.6 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 56 zamknięć, trafność 29% — pod kreską (−$6.98).
- (neu) Trafność 7 dni 25% vs 30 dni 29% — stabilna.
- (bad) Ostatnie 7 dni: -9.23 $ z 8 zamknięć.
- (bad) Średnia wygrana +$2.59 vs strata −$1.21 (wygrana 2.14× większa) → na transakcję −$0.13. Wygrane za małe wobec strat — to psuje wynik.
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
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- V: $-1.54 (1 zamk., 0%)

## Wejścia vs limit
- cap 6/dzień · max w dniu 57 · dni z limitem 6 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 29 · odrzuconych: 91

**Najczęstsze powody odrzucenia (top):**
- 64× — brak powodu
- 9× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.62 < próg 0.72 (baza 0.60 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.62 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.63 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
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
- 2026-09-15T17:47:53.052161 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-15T17:18:09.695750 AVGO SELL conf=0.5 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-15T16:30:22.268142 AVGO BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:22.251001 AMZN BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:22.229845 JPM BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:22.202367 COST BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
