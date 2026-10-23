# Audyt GielDarek — 2026-10-23T10:45:36Z

**Wdrożenie:** kod 792ffc6 (zbud. 2026-10-19T19:36Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (7 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (78× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 6 · dni z limitem 7 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 25 · odrzuconych: 95

**Najczęstsze powody odrzucenia (top):**
- 55× — Automat (alpaca) zapauzowany ręcznie
- 8× — brak powodu
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~495 min
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~510 min
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~525 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~120 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~135 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~150 min

**Ostatnie 20 decyzji:**
- 2026-10-23T08:51:33.853299 DOGE/USD BUY conf=0.6 trig=scheduled_daily ⛔ Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~495 min
- 2026-10-23T08:36:33.587128 DOGE/USD BUY conf=0.6 trig=scheduled_daily ⛔ Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~510 min
- 2026-10-23T08:21:33.408066 DOGE/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~525 min
- 2026-10-23T05:21:33.762368 AVAX/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-22T19:36:31.753592 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T19:06:31.893038 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T18:36:31.871768 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T18:06:31.634602 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T17:36:32.031885 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T17:06:31.798145 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T17:06:30.760303 DOGE/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-22T16:51:29.740409 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-22T16:36:31.930916 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T16:06:31.977866 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T15:36:31.870022 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T15:36:30.158093 LINK/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-22T15:06:31.811101 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T14:36:32.029297 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T14:06:31.779796 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-22T13:36:31.769498 — HOLD conf=0.0 trig=price_move ⛔ Automat (alpaca) zapauzowany ręcznie
