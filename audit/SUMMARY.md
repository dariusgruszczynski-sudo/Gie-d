# Audyt GielDarek — 2026-10-12T09:34:29Z

**Wdrożenie:** kod 800d3ce (zbud. 2026-10-11T17:05Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 61 · 32.8% · $13.67
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (good) Ostatnie 7 dni: +0.00 $ z 0 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (58 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane” (65× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-7.26 (11 zamk., 0%)
- AAPL: $-4.4 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.66 (4 zamk., 25%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- AMZN: $-2.3 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- GOOGL: $-2.25 (6 zamk., 33%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 58 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 3 · odrzuconych: 117

**Najczęstsze powody odrzucenia (top):**
- 19× — Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 19× — Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 19× — Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 19× — Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 19× — Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 18× — Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 4× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-10-12T06:35:28.250490 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-11T23:35:28.222242 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-11T17:10:15.844444 SOL/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-11T17:10:14.085285 LINK/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-11T17:10:11.646187 AVAX/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-11T17:10:11.590359 — HOLD conf=0.0 trig=manual ⛔ ?
- 2026-10-11T17:03:59.381518 LTC/USD BUY conf=0.6 trig=manual ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-11T17:03:59.378010 DOGE/USD BUY conf=0.6 trig=manual ⛔ Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 2026-10-11T17:03:59.374530 ETH/USD BUY conf=0.6 trig=manual ⛔ Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2026-10-11T17:03:59.370915 SOL/USD BUY conf=0.6 trig=manual ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-11T17:03:59.367387 LINK/USD BUY conf=0.6 trig=manual ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-11T17:03:59.363606 AVAX/USD BUY conf=0.6 trig=manual ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-11T17:03:59.314404 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-11T17:03:31.339693 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-11T17:03:31.333967 DOGE/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 2026-10-11T17:03:31.330776 ETH/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2026-10-11T17:03:31.327510 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-11T17:03:31.324047 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-11T17:03:31.320453 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-11T16:48:30.949248 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
