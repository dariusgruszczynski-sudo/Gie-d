# Audyt GielDarek — 2026-10-20T10:42:51Z

**Wdrożenie:** kod 792ffc6 (zbud. 2026-10-19T19:36Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (6 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (39× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 6 · dni z limitem 6 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 21 · odrzuconych: 99

**Najczęstsze powody odrzucenia (top):**
- 37× — Automat (alpaca) zapauzowany ręcznie
- 11× — brak powodu
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~120 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~135 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~150 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~165 min
- 1× — Cooldown po stop-lossie: ETH/USD zablokowany do odkupu jeszcze ~180 min
- 1× — Cooldown po stop-lossie: LTC/USD zablokowany do odkupu jeszcze ~121 min

**Ostatnie 20 decyzji:**
- 2026-10-19T20:06:31.127994 AVAX/USD SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-10-19T19:19:29.842864 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T18:49:30.186189 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T18:19:30.282264 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T17:49:30.122182 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T17:19:30.175248 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T16:49:30.058704 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T16:19:33.001682 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T15:49:30.319886 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T15:19:30.113026 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T14:49:30.097901 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T14:19:30.221353 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T13:49:30.098043 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-19T13:34:30.126106 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-19T06:34:28.887244 — HOLD conf=0.0 trig=scheduled_daily ⛔ ?
- 2026-10-19T00:04:47.284983 AVAX/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-19T00:04:45.550547 ETH/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-19T00:04:43.832887 DOGE/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-19T00:04:42.138533 SOL/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-19T00:04:38.002610 LTC/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
