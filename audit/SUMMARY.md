# Audyt GielDarek — 2026-09-22T20:45:59Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 79 zamknięć · trafność 38.0% · zrealizowany $15.13
**7 dni:** 24 zamknięć · 62.5% · $22.52   |   **30 dni:** 49 · 42.9% · $1.17
**Edge:** śr. wygrana +$2.21 vs strata $-1.04 → na transakcję $0.19 (payoff 2.12×)
**Trzymanie:** zyski ~3.4 dni · straty ~2.3 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 79 zamknięć, trafność 38% — realnie zarabia (+$15.13).
- (good) Trafność 7 dni 62% vs 30 dni 43% — rośnie.
- (good) Ostatnie 7 dni: +22.52 $ z 24 zamknięć.
- (neu) Średnia wygrana +$2.21 vs strata −$1.04 (wygrana 2.12× większa) → na transakcję +$0.19. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-6.65 $, 7 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (45 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-6.65 (7 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.16 (3 zamk., 33%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- AAPL: $-1.24 (1 zamk., 0%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 45 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 53 · odrzuconych: 67

**Najczęstsze powody odrzucenia (top):**
- 41× — brak powodu
- 15× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 5× — size_pct <= 0, nic do zrobienia
- 3× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-22T19:38:24.347960 TLT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-22T19:38:19.401841 AVGO BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-22T19:12:30.143946 — HOLD conf=0.7 trig=manual ⛔ ?
- 2026-09-22T19:08:03.386278 NVDA BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-09-22T19:07:58.529485 SMH BUY conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-22T18:37:55.538893 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-22T18:14:44.893516 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-09-22T18:07:56.935776 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-22T17:38:04.209569 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-22T17:07:54.714892 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-22T16:37:56.074249 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-22T16:08:10.447844 NVDA BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-22T16:08:05.759300 SMH BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-22T16:08:00.676993 MSFT SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-22T15:37:57.397288 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-22T15:07:51.939686 — HOLD conf=0.0 trig=price_move ⛔ ?
- 2026-09-22T14:37:59.374318 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-22T14:08:05.436970 AAPL BUY conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-22T14:08:00.466047 SMH BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-22T13:38:26.580131 SMH BUY conf=0.6 trig=price_move ✅WYKONANE
