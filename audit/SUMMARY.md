# Audyt GielDarek — 2026-09-22T17:36:38Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 77 zamknięć · trafność 37.7% · zrealizowany $14.85
**7 dni:** 22 zamknięć · 63.6% · $22.24   |   **30 dni:** 47 · 42.6% · $0.89
**Edge:** śr. wygrana +$2.26 vs strata $-1.06 → na transakcję $0.19 (payoff 2.13×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.4 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 77 zamknięć, trafność 38% — realnie zarabia (+$14.85).
- (good) Trafność 7 dni 64% vs 30 dni 43% — rośnie.
- (good) Ostatnie 7 dni: +22.24 $ z 22 zamknięć.
- (neu) Średnia wygrana +$2.26 vs strata −$1.06 (wygrana 2.13× większa) → na transakcję +$0.19. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-6.36 $, 6 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (45 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-6.36 (6 zamk., 0%)
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
- 38× — brak powodu
- 15× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 5× — size_pct <= 0, nic do zrobienia
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
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
- 2026-09-22T13:38:22.044646 MSFT BUY conf=0.62 trig=price_move ✅WYKONANE
- 2026-09-22T13:38:17.112863 NVDA BUY conf=0.65 trig=price_move ✅WYKONANE
- 2026-09-21T19:46:18.935552 META BUY conf=0.62 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:46:18.918317 QQQ BUY conf=0.65 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:46:18.881037 SMH BUY conf=0.68 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:17:45.411290 SMH BUY conf=0.62 trig=manual ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:17:05.655566 META SELL conf=1.0 trig=manual ✅WYKONANE
- 2026-09-21T19:16:12.612986 META SELL conf=0.72 trig=news_event ✅WYKONANE
- 2026-09-21T18:46:12.668243 QQQ BUY conf=0.68 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
