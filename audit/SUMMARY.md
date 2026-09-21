# Audyt GielDarek — 2026-09-21T15:42:55Z

**Wdrożenie:** kod 3a0b17f (zbud. 2026-09-19T11:44Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 69 zamknięć · trafność 34.8% · zrealizowany $5.16
**7 dni:** 16 zamknięć · 56.2% · $11.27   |   **30 dni:** 39 · 38.5% · $-8.8
**Edge:** śr. wygrana +$2.31 vs strata $-1.12 → na transakcję $0.07 (payoff 2.06×)
**Trzymanie:** zyski ~3.7 dni · straty ~2.5 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 69 zamknięć, trafność 35% — realnie zarabia (+$5.16).
- (good) Trafność 7 dni 56% vs 30 dni 38% — rośnie.
- (good) Ostatnie 7 dni: +11.27 $ z 16 zamknięć.
- (neu) Średnia wygrana +$2.31 vs strata −$1.12 (wygrana 2.06× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.86 $, 4 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (8 dni) — podniesienie może dołożyć wejść.
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
- AAPL: $-1.24 (1 zamk., 0%)

## Wejścia vs limit
- cap 6/dzień · max w dniu 57 · dni z limitem 8 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 50 · odrzuconych: 70

**Najczęstsze powody odrzucenia (top):**
- 53× — brak powodu
- 5× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 5× — size_pct <= 0, nic do zrobienia
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-21T15:16:33.222382 LLY BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-21T15:16:28.847961 SMH BUY conf=0.7 trig=news_event ✅WYKONANE
- 2026-09-21T15:16:22.956635 META BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-21T15:15:48.777743 SMH SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-09-21T15:15:45.257070 NVDA SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-09-21T14:46:14.681947 MSFT BUY conf=0.6 trig=news_event ⛔ Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-21T14:16:17.449914 GOOGL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-21T13:46:44.832175 V BUY conf=0.3 trig=price_move ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-21T13:46:44.818101 MSFT BUY conf=0.6 trig=price_move ⛔ Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-21T13:46:40.022976 SMH BUY conf=0.62 trig=price_move ✅WYKONANE
- 2026-09-21T13:46:39.998296 GOOGL BUY conf=0.5 trig=price_move ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-18T19:42:52.715428 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T19:36:58.026923 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-09-18T19:36:50.586852 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-09-18T19:13:16.300004 SMH BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-09-18T19:13:11.380683 AAPL BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-18T19:13:11.363620 META SELL conf=0.5 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-18T18:25:57.664422 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T17:55:52.983972 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-18T17:27:14.117915 SMH BUY conf=0.6 trig=manual ✅WYKONANE
