# Audyt GielDarek — 2026-10-12T21:42:12Z

**Wdrożenie:** kod f8b5065 (zbud. 2026-10-12T18:19Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

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
- (neu) Limit wejść bywa osiągany (59 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane” (56× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 59 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 9 · odrzuconych: 111

**Najczęstsze powody odrzucenia (top):**
- 15× — Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 15× — Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 15× — Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 15× — Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane
- 15× — Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 15× — Auto-degradacja SOL/USD: ujemna historia (2W/4L, P&L -1150.07) — nowe wejście zablokowane
- 13× — Automat (alpaca) zapauzowany ręcznie
- 5× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-10-12T19:49:39.710712 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T19:19:39.682285 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T18:49:39.947765 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T18:08:29.407726 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T17:38:38.424278 ETH/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-12T17:38:38.418969 SOL/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~45 min
- 2026-10-12T17:38:38.412982 AVAX/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~15 min
- 2026-10-12T17:38:38.404507 LINK/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: LINK/USD zablokowany do odkupu jeszcze ~60 min
- 2026-10-12T17:38:36.439626 LTC/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-12T17:38:29.257058 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T17:38:27.728152 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-12T17:23:27.311651 SOL/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-12T17:08:29.264389 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T16:53:35.593126 DOGE/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-12T16:53:27.351818 AVAX/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-12T16:38:29.570457 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T16:08:29.349309 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T15:38:29.362997 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T15:08:29.334882 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-12T14:38:29.430388 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
