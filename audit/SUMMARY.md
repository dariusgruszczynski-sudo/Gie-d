# Audyt GielDarek — 2026-09-25T17:54:24Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 89 zamknięć · trafność 36.0% · zrealizowany $11.92
**7 dni:** 22 zamknięć · 45.5% · $18.64   |   **30 dni:** 55 · 38.2% · $-5.27
**Edge:** śr. wygrana +$2.08 vs strata $-0.96 → na transakcję $0.13 (payoff 2.17×)
**Trzymanie:** zyski ~3.2 dni · straty ~2.2 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 89 zamknięć, trafność 36% — realnie zarabia (+$11.92).
- (good) Trafność 7 dni 46% vs 30 dni 38% — rośnie.
- (good) Ostatnie 7 dni: +18.64 $ z 22 zamknięć.
- (neu) Średnia wygrana +$2.08 vs strata −$0.96 (wygrana 2.17× większa) → na transakcję +$0.13. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-6.91 $, 8 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (48 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (18× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-6.91 (8 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.66 (4 zamk., 25%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- AAPL: $-1.24 (1 zamk., 0%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 48 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 64 · odrzuconych: 56

**Najczęstsze powody odrzucenia (top):**
- 37× — brak powodu
- 10× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 4× — size_pct <= 0, nic do zrobienia
- 3× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-25T17:38:19.014707 NVDA BUY conf=0.63 trig=news_event ✅WYKONANE
- 2026-09-25T17:38:13.584613 MSFT BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T17:08:02.952920 MSFT BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T16:38:01.861637 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-25T16:08:09.214505 SMH BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T16:08:03.719481 QQQ BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-25T15:38:00.326248 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-25T15:08:07.394811 COST BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T15:08:01.295845 SMH BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T14:37:54.942145 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-25T14:07:59.060123 LLY BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-25T13:38:18.254456 COST BUY conf=0.62 trig=price_move ✅WYKONANE
- 2026-09-24T19:38:09.337934 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-24T19:08:03.202296 AAPL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-24T19:07:58.058238 QQQ BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-24T18:38:00.672493 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-24T18:07:56.718199 SMH SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-24T17:37:53.981997 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-24T17:07:57.770991 SMH BUY conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-24T16:37:55.146013 — HOLD conf=0.6 trig=news_event ⛔ ?
