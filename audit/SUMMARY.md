# Audyt GielDarek — 2026-10-18T10:08:47Z

**Wdrożenie:** kod e9952d4 (zbud. 2026-10-18T08:16Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (4 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (27× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 4 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 5 · odrzuconych: 115

**Najczęstsze powody odrzucenia (top):**
- 25× — Automat (alpaca) zapauzowany ręcznie
- 9× — brak powodu
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202773.538818389374 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203644.406551216752 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200553.48909222464508 exceeds max notional per order 200000"}
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200580.480578257043 exceeds max notional per order 200000"}
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200605.78509641241605 exceeds max notional per order 200000"}

**Ostatnie 20 decyzji:**
- 2026-10-18T08:30:03.081280 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-18T06:06:28.984572 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-17T23:36:28.161643 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 205900.463677628016 exceeds max notional per order 200000"}
- 2026-10-17T23:21:28.058688 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 206286.10844267394144 exceeds max notional per order 200000"}
- 2026-10-17T23:06:28.278293 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 206111.969033229072 exceeds max notional per order 200000"}
- 2026-10-17T22:51:28.201438 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 206101.3937654490192 exceeds max notional per order 200000"}
- 2026-10-17T22:36:28.144973 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 205583.205644226432 exceeds max notional per order 200000"}
- 2026-10-17T22:21:28.160216 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 205281.45800356892544 exceeds max notional per order 200000"}
- 2026-10-17T22:06:28.219965 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 204755.51468597429952 exceeds max notional per order 200000"}
- 2026-10-17T21:51:28.112058 LTC/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203737.46890768121664 exceeds max notional per order 200000"}
- 2026-10-17T17:06:34.762066 SOL/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-17T17:06:28.022036 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-17T16:51:27.943045 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200553.48909222464508 exceeds max notional per order 200000"}
- 2026-10-17T16:36:28.056712 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200605.78509641241605 exceeds max notional per order 200000"}
- 2026-10-17T16:21:28.021000 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 201358.17276956550807 exceeds max notional per order 200000"}
- 2026-10-17T16:06:28.088210 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 201002.2225475132605 exceeds max notional per order 200000"}
- 2026-10-17T15:51:28.018987 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200917.874153662017 exceeds max notional per order 200000"}
- 2026-10-17T15:36:28.047991 LINK/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 201342.99005867228424 exceeds max notional per order 200000"}
- 2026-10-17T13:21:35.525318 ETH/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-17T13:21:28.045539 AVAX/USD SELL conf=1.0 trig=price_move ✅WYKONANE
