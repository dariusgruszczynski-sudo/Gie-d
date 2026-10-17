# Audyt GielDarek — 2026-10-17T20:46:38Z

**Wdrożenie:** kod 88f7e2c (zbud. 2026-10-15T16:36Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

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
- ostatnie 120 decyzji · wykonanych: 6 · odrzuconych: 114

**Najczęstsze powody odrzucenia (top):**
- 25× — Automat (alpaca) zapauzowany ręcznie
- 7× — brak powodu
- 3× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202773.538818389374 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203644.406551216752 exceeds max notional per order 200000"}
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200553.48909222464508 exceeds max notional per order 200000"}
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200580.480578257043 exceeds max notional per order 200000"}
- 1× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 200605.78509641241605 exceeds max notional per order 200000"}

**Ostatnie 20 decyzji:**
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
- 2026-10-17T08:06:28.884125 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-17T01:51:29.157138 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-16T19:36:30.113985 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T19:06:30.177665 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T18:36:30.066228 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T18:21:30.851481 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-16T18:06:30.254717 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T17:36:30.444203 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T17:06:30.123020 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T16:36:30.010041 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
