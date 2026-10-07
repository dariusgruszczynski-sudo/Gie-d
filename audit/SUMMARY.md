# Audyt GielDarek — 2026-10-07T12:22:49Z

**Wdrożenie:** kod a8228c3 (zbud. 2026-10-06T18:56Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 11 zamknięć · 9.1% · $1.79   |   **30 dni:** 67 · 32.8% · $8.33
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (bad) Trafność 7 dni 9% vs 30 dni 33% — spada.
- (good) Ostatnie 7 dni: +1.79 $ z 11 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (56 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane” (40× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 56 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 10 · odrzuconych: 110

**Najczęstsze powody odrzucenia (top):**
- 35× — Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 29× — Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 23× — Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 18× — Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 5× — Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane

**Ostatnie 20 decyzji:**
- 2026-10-07T12:11:37.790055 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T12:11:37.786451 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-07T12:11:37.782718 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-07T11:56:39.484789 AVAX/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-07T11:56:39.480463 LTC/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T11:56:39.477204 SOL/USD BUY conf=0.6 trig=scheduled_daily ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-07T11:41:37.627690 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-07T11:41:37.624089 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T11:41:37.620208 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-07T11:26:38.688774 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-07T11:26:38.685468 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T11:26:38.681815 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-07T11:11:39.329651 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2026-10-07T11:11:39.326269 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T11:11:39.322544 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-07T11:11:31.520738 AVAX/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-07T10:56:44.046290 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T10:56:44.042313 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 2026-10-07T10:41:38.211999 LTC/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2026-10-07T10:41:38.207050 SOL/USD BUY conf=0.6 trig=news_event ⛔ Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
