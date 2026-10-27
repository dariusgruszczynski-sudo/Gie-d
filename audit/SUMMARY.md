# Audyt GielDarek — 2026-10-27T18:38:58Z

**Wdrożenie:** kod 6ce61eb (zbud. 2026-10-26T20:40Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (10 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (106× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 6 · dni z limitem 10 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 6 · odrzuconych: 114

**Najczęstsze powody odrzucenia (top):**
- 87× — brak powodu
- 17× — Automat (alpaca) zapauzowany ręcznie
- 1× — Cooldown po stop-lossie: BTC/USD zablokowany do odkupu jeszcze ~42 min
- 1× — Cooldown po stop-lossie: BTC/USD zablokowany do odkupu jeszcze ~72 min
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~12 min
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~27 min
- 1× — Cooldown po stop-lossie: DOGE/USD zablokowany do odkupu jeszcze ~42 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~1395 min

**Ostatnie 20 decyzji:**
- 2026-10-27T18:26:16.810652 HYPE/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-27T18:26:16.427937 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T18:11:14.969187 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-27T18:10:40.349269 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-27T17:56:09.790692 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-27T17:41:10.289240 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T17:40:40.421262 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-27T17:26:08.942489 ETH/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~1395 min
- 2026-10-27T17:26:08.491528 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T17:11:16.356878 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T17:10:40.697596 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-27T16:56:08.770925 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T16:41:17.164977 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-27T16:40:40.500263 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-27T16:40:40.425745 ETH/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-27T16:26:10.131059 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T16:11:11.769600 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-27T16:10:41.183503 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-27T15:56:11.860817 LINK/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: LINK/USD zablokowany do odkupu jeszcze ~27 min
- 2026-10-27T15:56:11.834928 BTC/USD BUY conf=0.6 trig=news_event ⛔ Cooldown po stop-lossie: BTC/USD zablokowany do odkupu jeszcze ~42 min
