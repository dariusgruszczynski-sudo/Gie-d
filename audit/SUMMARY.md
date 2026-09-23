# Audyt GielDarek — 2026-09-23T20:46:20Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 86 zamknięć · trafność 36.0% · zrealizowany $12.02
**7 dni:** 28 zamknięć · 50.0% · $18.91   |   **30 dni:** 54 · 38.9% · $-5.11
**Edge:** śr. wygrana +$2.14 vs strata $-0.99 → na transakcję $0.14 (payoff 2.16×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.2 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 86 zamknięć, trafność 36% — realnie zarabia (+$12.02).
- (good) Trafność 7 dni 50% vs 30 dni 39% — rośnie.
- (good) Ostatnie 7 dni: +18.91 $ z 28 zamknięć.
- (neu) Średnia wygrana +$2.14 vs strata −$0.99 (wygrana 2.16× większa) → na transakcję +$0.14. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-6.65 $, 7 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (46 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-6.65 (7 zamk., 0%)
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
- cap 0/dzień · max w dniu 57 · dni z limitem 46 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 65 · odrzuconych: 55

**Najczęstsze powody odrzucenia (top):**
- 32× — brak powodu
- 15× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — size_pct <= 0, nic do zrobienia
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-23T19:38:12.534898 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-23T19:07:54.525044 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-23T18:37:57.048801 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-23T18:07:59.143192 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-23T17:37:56.334825 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-23T17:08:05.228512 META SELL conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-23T16:38:03.216181 SMH SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-23T16:08:04.497884 MSFT BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-23T16:07:58.950687 NVDA SELL conf=0.65 trig=news_event ✅WYKONANE
- 2026-09-23T15:37:56.023965 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-23T15:07:56.407184 NVDA SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-23T14:38:02.665150 SPY BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-23T14:37:57.265110 NVDA SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-23T14:34:07.793959 AAPL BUY conf=0.62 trig=manual ✅WYKONANE
- 2026-09-23T14:34:02.706032 SMH BUY conf=0.68 trig=manual ✅WYKONANE
- 2026-09-23T14:33:56.452875 GOOGL SELL conf=0.65 trig=manual ✅WYKONANE
- 2026-09-23T14:08:06.444144 SMH BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-23T13:38:26.304061 META BUY conf=0.62 trig=price_move ✅WYKONANE
- 2026-09-23T13:38:21.010401 AVGO SELL conf=0.55 trig=price_move ✅WYKONANE
- 2026-09-22T19:38:24.347960 TLT SELL conf=0.55 trig=news_event ✅WYKONANE
