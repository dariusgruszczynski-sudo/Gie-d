# Audyt GielDarek — 2026-10-16T20:57:39Z

**Wdrożenie:** kod 88f7e2c (zbud. 2026-10-15T16:36Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (3 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (27× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 3 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 8 · odrzuconych: 112

**Najczęstsze powody odrzucenia (top):**
- 27× — Automat (alpaca) zapauzowany ręcznie
- 5× — brak powodu
- 3× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203954.416332306783 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 202773.538818389374 exceeds max notional per order 200000"}
- 2× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"code":40310000,"message":"order notional 203644.406551216752 exceeds max notional per order 200000"}
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~60 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~180 min
- 1× — Cooldown po stop-lossie: SOL/USD zablokowany do odkupu jeszcze ~60 min

**Ostatnie 20 decyzji:**
- 2026-10-16T19:36:30.113985 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T19:06:30.177665 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T18:36:30.066228 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T18:21:30.851481 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-16T18:06:30.254717 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T17:36:30.444203 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T17:06:30.123020 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T16:36:30.010041 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T16:06:30.081685 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T15:36:30.361302 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T15:06:30.118678 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T14:36:33.573672 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T14:06:30.066471 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T13:36:30.291225 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-16T10:06:28.800793 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-16T00:06:32.637506 AVAX/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-15T20:31:21.532744 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-15T19:49:57.436737 — HOLD conf=0.6 trig=manual ⛔ ?
- 2026-10-15T19:36:30.316834 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-15T19:06:30.115880 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
