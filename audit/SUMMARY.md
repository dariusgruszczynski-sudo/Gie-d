# Audyt GielDarek — 2026-11-19T14:57:47Z

**Wdrożenie:** kod eddcf73 (zbud. 2026-11-19T14:53Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)” (121× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 11 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 1 · odrzuconych: 119

**Najczęstsze powody odrzucenia (top):**
- 65× — Automat (alpaca) zapauzowany ręcznie
- 54× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}

**Ostatnie 20 decyzji:**
- 2026-11-18T20:50:11.290387 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T20:20:11.060040 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T19:50:10.485316 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T19:20:11.162728 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T18:50:10.939664 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T18:20:11.626828 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T17:50:10.757251 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T17:20:11.801241 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T16:50:11.999033 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T16:20:13.242179 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T15:50:11.270253 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T15:20:11.687609 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-18T14:50:11.017562 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T20:50:11.302725 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T20:20:11.812112 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T19:50:17.215724 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T19:20:10.909434 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T18:50:11.160132 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T18:20:10.941664 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-17T17:50:10.863267 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
