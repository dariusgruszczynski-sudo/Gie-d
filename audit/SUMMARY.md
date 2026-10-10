# Audyt GielDarek — 2026-10-10T11:38:52Z

**Wdrożenie:** kod 41266a3 (zbud. 2026-10-08T06:03Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 64 · 31.2% · $6.13
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (good) Ostatnie 7 dni: +0.00 $ z 0 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (57 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane” (67× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 57 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 1 · odrzuconych: 119

**Najczęstsze powody odrzucenia (top):**
- 35× — Automat (alpaca) zapauzowany ręcznie
- 25× — Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 16× — Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 13× — Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 10× — Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 10× — Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 8× — Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-10-10T09:48:34.624883 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T09:33:31.462042 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T09:18:31.483583 LINK/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T09:03:31.604668 LINK/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T06:48:31.407396 LINK/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T06:33:31.509630 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T06:18:31.370038 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T06:03:31.280963 LINK/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T05:48:31.667639 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-10T05:48:31.663584 ETH/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2026-10-10T05:48:31.657573 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T05:48:31.650313 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-10T05:33:31.588811 LINK/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 2026-10-10T05:18:31.397246 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-10T05:18:31.391169 ETH/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2026-10-10T05:03:31.615408 ETH/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2026-10-10T03:48:31.509293 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-10T03:33:31.450057 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-10T03:18:31.373706 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-10T03:03:31.601921 DOGE/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
