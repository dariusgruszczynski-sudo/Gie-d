# Audyt GielDarek — 2026-10-14T10:54:52Z

**Wdrożenie:** kod 4ada3a3 (zbud. 2026-10-14T08:47Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

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
- (neu) Najczęstszy powód pominięcia wejścia: „Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane” (37× z ostatnich 300 decyzji).

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
- 11× — Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 5× — brak powodu
- 3× — Auto-degradacja DOGE/USD: ujemna historia (0W/5L, P&L -1406.74) — nowe wejście zablokowane
- 3× — Auto-degradacja LTC/USD: ujemna historia (0W/5L, P&L -2333.86) — nowe wejście zablokowane
- 2× — Auto-degradacja AVAX/USD: ujemna historia (1W/4L, P&L -2392.28) — nowe wejście zablokowane
- 2× — Auto-degradacja ETH/USD: ujemna historia (1W/4L, P&L -600.04) — nowe wejście zablokowane
- 2× — Auto-degradacja LINK/USD: ujemna historia (0W/5L, P&L -1476.39) — nowe wejście zablokowane

**Ostatnie 20 decyzji:**
- 2026-10-14T10:47:27.846900 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T10:32:27.706903 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T10:17:27.907910 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T10:02:27.637768 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T09:32:27.717122 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T09:17:27.937253 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T09:02:27.759276 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T08:42:13.206095 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T08:27:13.016326 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T07:57:12.922162 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-14T07:42:13.680405 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -174.6% (limit 30.0%)
- 2026-10-13T19:42:15.192279 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T19:12:18.552823 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T18:42:15.050743 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T17:49:39.908988 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T17:19:39.902558 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T16:49:40.000074 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T16:19:39.811275 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T15:49:39.771008 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-13T15:19:39.812043 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
