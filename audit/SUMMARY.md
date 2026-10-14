# Audyt GielDarek — 2026-10-14T17:57:00Z

**Wdrożenie:** kod 4ada3a3 (zbud. 2026-10-14T08:47Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 59 · 32.2% · $14.49
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (good) Ostatnie 7 dni: +0.00 $ z 0 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (60 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane” (36× z ostatnich 300 decyzji).

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
- ostatnie 120 decyzji · wykonanych: 25 · odrzuconych: 95

**Najczęstsze powody odrzucenia (top):**
- 30× — Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 25× — Automat (alpaca) zapauzowany ręcznie
- 2× — Cooldown po stop-lossie: LINK/USD zablokowany do odkupu jeszcze ~60 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~105 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~135 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~15 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~150 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~165 min

**Ostatnie 20 decyzji:**
- 2026-10-14T17:47:29.886120 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T17:17:29.859888 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T16:47:29.774253 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T16:17:30.059546 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T15:47:30.031542 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T15:17:29.912813 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T15:17:28.803463 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-14T15:17:27.475721 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-14T15:17:05.373667 — HOLD conf=0.7 trig=manual ⛔ ?
- 2026-10-14T15:02:27.695313 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T14:47:29.879913 — HOLD conf=0.0 trig=scheduled_daily ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T14:47:27.807009 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T14:32:27.868772 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T14:17:30.407472 — HOLD conf=0.0 trig=scheduled_daily ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T14:17:27.819577 — HOLD conf=0.0 trig=price_move ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T14:02:27.630779 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T13:47:30.086610 — HOLD conf=0.0 trig=price_move ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T13:47:27.814179 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T13:32:27.692557 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T13:17:27.802072 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
