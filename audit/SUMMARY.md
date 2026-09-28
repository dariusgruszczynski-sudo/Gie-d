# Audyt GielDarek — 2026-09-28T20:46:40Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 98 zamknięć · trafność 33.7% · zrealizowany $9.86
**7 dni:** 23 zamknięć · 17.4% · $-5.49   |   **30 dni:** 58 · 36.2% · $0.43
**Edge:** śr. wygrana +$2.02 vs strata $-0.87 → na transakcję $0.1 (payoff 2.32×)
**Trzymanie:** zyski ~3.1 dni · straty ~2.4 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 98 zamknięć, trafność 34% — realnie zarabia (+$9.86).
- (bad) Trafność 7 dni 17% vs 30 dni 36% — spada.
- (bad) Ostatnie 7 dni: -5.49 $ z 23 zamknięć.
- (neu) Średnia wygrana +$2.02 vs strata −$0.87 (wygrana 2.32× większa) → na transakcję +$0.10. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.11 $, 10 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (49 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)” (15× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-7.11 (10 zamk., 0%)
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
- cap 0/dzień · max w dniu 57 · dni z limitem 49 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 70 · odrzuconych: 50

**Najczęstsze powody odrzucenia (top):**
- 31× — brak powodu
- 10× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 6× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-28T19:38:19.321370 QQQ SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T19:08:06.498893 NVDA SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T18:37:54.446256 NVDA BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-28T18:08:02.199587 NFLX BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-28T18:08:02.192395 GLD SELL conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-28T17:37:57.005100 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T17:08:02.473970 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-28T16:38:10.215502 SMH BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-28T16:38:05.870876 COST BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-28T16:38:05.835594 NVDA BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-28T16:38:00.462080 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T16:08:02.925518 SMH SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T15:37:47.272024 NVDA BUY conf=0.0 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-28T15:08:08.382230 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-28T14:38:27.392957 META SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T14:07:58.375110 META SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T13:38:18.736323 META SELL conf=0.55 trig=price_move ✅WYKONANE
- 2026-09-25T19:38:05.886149 COST BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-25T19:38:00.604844 NVDA SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-25T19:07:57.190440 — HOLD conf=0.6 trig=news_event ⛔ ?
