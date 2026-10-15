# Audyt GielDarek — 2026-10-15T10:36:50Z

**Wdrożenie:** kod 678e050 (zbud. 2026-10-14T18:48Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (2 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}” (7× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 2 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 74 decyzji · wykonanych: 11 · odrzuconych: 63

**Najczęstsze powody odrzucenia (top):**
- 7× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 250000 exceeds max notional per order 200000"}
- 3× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 2× — Automat (alpaca) zapauzowany ręcznie
- 2× — brak powodu
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~60 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~180 min
- 1× — Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~60 min
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202287.247186109976 exceeds max notional per order 200000"}

**Ostatnie 20 decyzji:**
- 2026-10-15T10:33:23.859258 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204398.7756528605184 exceeds max notional per order 200000"}
- 2026-10-15T10:33:23.620683 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202436.1452429844 exceeds max notional per order 200000"}
- 2026-10-15T10:18:23.661325 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202891.6265697811149 exceeds max notional per order 200000"}
- 2026-10-15T10:03:23.594475 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203785.719544604296 exceeds max notional per order 200000"}
- 2026-10-15T09:48:23.632835 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203515.8046842803168 exceeds max notional per order 200000"}
- 2026-10-15T09:33:23.597359 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 2026-10-15T09:03:23.606255 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204484.12424569259218 exceeds max notional per order 200000"}
- 2026-10-15T08:48:23.886029 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 205741.834660927224 exceeds max notional per order 200000"}
- 2026-10-15T08:48:23.644003 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204808.02207808136722 exceeds max notional per order 200000"}
- 2026-10-15T08:33:23.857389 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 205512.70385902608 exceeds max notional per order 200000"}
- 2026-10-15T08:33:23.617626 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204835.01356411376514 exceeds max notional per order 200000"}
- 2026-10-15T08:18:23.915620 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204440.01919720272432 exceeds max notional per order 200000"}
- 2026-10-15T08:18:23.672230 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203549.5440418208142 exceeds max notional per order 200000"}
- 2026-10-15T08:03:23.888060 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204452.70951853878768 exceeds max notional per order 200000"}
- 2026-10-15T08:03:23.645735 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 2026-10-15T07:48:23.922590 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204204.8957435595504 exceeds max notional per order 200000"}
- 2026-10-15T07:48:23.654997 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203617.022756901809 exceeds max notional per order 200000"}
- 2026-10-15T07:33:23.881577 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204257.7720824598144 exceeds max notional per order 200000"}
- 2026-10-15T07:33:23.636253 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203372.41241473320285 exceeds max notional per order 200000"}
- 2026-10-15T07:18:23.874183 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203909.49326357007552 exceeds max notional per order 200000"}
