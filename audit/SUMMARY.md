# Audyt GielDarek — 2026-10-06T22:58:09Z

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
- (neu) Limit wejść bywa osiągany (55 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (36× z ostatnich 300 decyzji).

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
- ostatnie 120 decyzji · wykonanych: 36 · odrzuconych: 84

**Najczęstsze powody odrzucenia (top):**
- 35× — Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 29× — Automat (alpaca) zapauzowany ręcznie
- 17× — Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 3× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-10-06T22:41:45.710003 LTC/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-06T22:41:43.537882 LINK/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-06T22:41:31.813584 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T22:26:37.801615 DOGE/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-06T21:26:33.116046 LTC/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T21:26:31.779506 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T21:11:39.662601 LINK/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-06T21:11:31.946052 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T20:11:46.193986 LTC/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-06T20:11:44.077250 ETH/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-06T19:56:43.705836 LINK/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-06T19:56:34.467048 DOGE/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T19:56:34.135475 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T19:56:33.394260 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T19:56:31.820309 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T19:26:42.424786 SOL/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-06T19:26:34.816969 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-06T19:26:31.918221 SOL/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-06T19:14:25.666381 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-06T18:42:26.426227 DOGE/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
