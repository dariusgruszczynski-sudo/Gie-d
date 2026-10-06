# Audyt GielDarek — 2026-10-06T18:52:42Z

**Wdrożenie:** kod e13a01d (zbud. 2026-10-06T18:26Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 12 zamknięć · 8.3% · $-0.56   |   **30 dni:** 67 · 32.8% · $8.33
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (bad) Trafność 7 dni 8% vs 30 dni 33% — spada.
- (bad) Ostatnie 7 dni: -0.56 $ z 12 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (55 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Dzienny limit strat przekroczony: -99.6% (limit 20.0%)” (35× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 55 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 26 · odrzuconych: 94

**Najczęstsze powody odrzucenia (top):**
- 35× — Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 34× — Automat (alpaca) zapauzowany ręcznie
- 17× — Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 6× — brak powodu
- 2× — size_pct <= 0, nic do zrobienia

**Ostatnie 20 decyzji:**
- 2026-10-06T18:42:26.426227 DOGE/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-06T18:42:24.648213 ETH/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-06T18:42:22.547150 LINK/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-06T18:42:12.171483 DOGE/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T18:42:11.234113 LTC/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T18:42:10.141080 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T18:42:08.477888 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T18:42:07.539424 BTC/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T18:36:40.438718 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-06T17:24:38.912762 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T16:54:38.791741 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T16:24:39.016429 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T15:54:39.092868 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T15:24:39.133459 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T14:54:42.655431 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T14:24:39.523732 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T13:54:39.608607 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T19:54:38.846172 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T19:24:38.931457 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T18:54:39.901487 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
