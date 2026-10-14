# Audyt GielDarek — 2026-10-14T21:35:02Z

**Wdrożenie:** kod 678e050 (zbud. 2026-10-14T18:48Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (1 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}” (7× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 1 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 15 decyzji · wykonanych: 4 · odrzuconych: 11

**Najczęstsze powody odrzucenia (top):**
- 7× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2× — Automat (alpaca) zapauzowany ręcznie
- 2× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-10-14T19:48:25.903014 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T19:18:25.810681 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-14T18:52:24.353274 ETH/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-14T18:52:22.593246 DOGE/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-14T18:52:20.791221 SOL/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-14T18:52:18.639688 BTC/USD BUY conf=0.6 trig=manual ✅WYKONANE
- 2026-10-14T18:52:18.630999 — HOLD conf=0.7 trig=manual ⛔ ?
- 2026-10-14T18:42:22.471585 LINK/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:22.360493 AVAX/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:22.245716 LTC/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:22.130127 ETH/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:22.016256 SOL/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:21.904047 DOGE/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:21.597720 BTC/USD BUY conf=0.6 trig=manual ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 2026-10-14T18:42:21.582908 — HOLD conf=0.0 trig=manual ⛔ ?
