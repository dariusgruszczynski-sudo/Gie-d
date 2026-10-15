# Audyt GielDarek — 2026-10-15T17:43:20Z

**Wdrożenie:** kod 88f7e2c (zbud. 2026-10-15T16:36Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (2 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (10× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 2 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 111 decyzji · wykonanych: 11 · odrzuconych: 100

**Najczęstsze powody odrzucenia (top):**
- 10× — Automat (alpaca) zapauzowany ręcznie
- 7× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 3× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 3× — brak powodu
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202773.538818389374 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203644.406551216752 exceeds max notional per order 200000"}
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~60 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~180 min

**Ostatnie 20 decyzji:**
- 2026-10-15T17:36:30.115670 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T17:06:30.058275 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T16:52:04.911480 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-15T16:18:25.724901 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T15:48:25.817361 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T15:18:25.947860 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T14:48:25.918156 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T14:33:23.709379 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204409.8976591034979 exceeds max notional per order 200000"}
- 2026-10-15T14:18:25.952941 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T14:18:23.758153 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204123.11312000927 exceeds max notional per order 200000"}
- 2026-10-15T14:03:23.716491 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 201255.267729066991 exceeds max notional per order 200000"}
- 2026-10-15T13:48:26.111815 — HOLD conf=0.0 trig=price_move ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T13:48:23.756273 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200580.480578257043 exceeds max notional per order 200000"}
- 2026-10-15T13:33:24.557303 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204917.66879193510912 exceeds max notional per order 200000"}
- 2026-10-15T13:33:23.848491 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 201130.43210616715062 exceeds max notional per order 200000"}
- 2026-10-15T13:18:23.859253 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204222.5211898596384 exceeds max notional per order 200000"}
- 2026-10-15T13:18:23.614473 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 201525.1825893909702 exceeds max notional per order 200000"}
- 2026-10-15T13:03:23.934304 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203644.406551216752 exceeds max notional per order 200000"}
- 2026-10-15T13:03:23.653929 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200745.80343020548026 exceeds max notional per order 200000"}
- 2026-10-15T12:48:23.861973 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204278.92261801992 exceeds max notional per order 200000"}
