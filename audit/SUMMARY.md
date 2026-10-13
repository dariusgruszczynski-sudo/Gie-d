# Audyt GielDarek — 2026-10-13T19:50:09Z

**Wdrożenie:** kod 37384b8 (zbud. 2026-10-13T18:11Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

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
- (neu) Limit wejść bywa osiągany (60 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (38× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 60 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 26 · odrzuconych: 94

**Najczęstsze powody odrzucenia (top):**
- 25× — Automat (alpaca) zapauzowany ręcznie
- 5× — Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 5× — brak powodu
- 4× — Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 4× — Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 4× — Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 4× — Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 4× — Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane

**Ostatnie 20 decyzji:**
- 2026-10-13T19:42:15.192279 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T19:12:18.552823 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T18:42:15.050743 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T17:49:39.908988 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T17:19:39.902558 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T16:49:40.000074 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T16:19:39.811275 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T15:49:39.771008 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T15:19:39.812043 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T14:49:39.770477 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T14:19:39.778635 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T13:49:39.927271 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T11:19:37.844989 SOL/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-13T04:19:42.926104 SOL/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-13T04:19:42.918484 DOGE/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~150 min
- 2026-10-13T04:19:40.979617 LINK/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-13T04:04:41.176781 LTC/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~90 min
- 2026-10-13T04:04:41.172702 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~90 min
- 2026-10-13T04:04:41.168596 DOGE/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~165 min
- 2026-10-13T04:04:41.164521 SOL/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~15 min
