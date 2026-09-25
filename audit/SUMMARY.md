# Audyt GielDarek — 2026-09-25T21:28:25Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 90 zamknięć · trafność 35.6% · zrealizowany $11.88
**7 dni:** 23 zamknięć · 43.5% · $18.6   |   **30 dni:** 55 · 38.2% · $-1.0
**Edge:** śr. wygrana +$2.08 vs strata $-0.94 → na transakcję $0.13 (payoff 2.21×)
**Trzymanie:** zyski ~3.2 dni · straty ~2.2 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 90 zamknięć, trafność 36% — realnie zarabia (+$11.88).
- (good) Trafność 7 dni 44% vs 30 dni 38% — rośnie.
- (good) Ostatnie 7 dni: +18.60 $ z 23 zamknięć.
- (neu) Średnia wygrana +$2.08 vs strata −$0.94 (wygrana 2.21× większa) → na transakcję +$0.13. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-6.91 $, 8 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (48 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (17× z ostatnich 300 decyzji).

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
- ostatnie 120 decyzji · wykonanych: 66 · odrzuconych: 54

**Najczęstsze powody odrzucenia (top):**
- 36× — brak powodu
- 10× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 4× — size_pct <= 0, nic do zrobienia
- 2× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-25T19:38:05.886149 COST BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T19:38:00.604844 NVDA SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-25T19:07:57.190440 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-25T18:38:07.540453 META BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T18:08:06.006243 — HOLD conf=0.6 trig=news_event ⛔ ?
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
