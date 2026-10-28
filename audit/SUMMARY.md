# Audyt GielDarek — 2026-10-28T23:07:08Z

**Wdrożenie:** kod 0c9eb76 (zbud. 2026-10-28T20:25Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (39× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 11 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 10 · odrzuconych: 110

**Najczęstsze powody odrzucenia (top):**
- 69× — brak powodu
- 13× — Automat (alpaca) zapauzowany ręcznie
- 5× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1350 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1365 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1380 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1410 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1425 min

**Ostatnie 20 decyzji:**
- 2026-10-28T22:27:01.802325 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T22:12:02.582205 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T21:57:10.396125 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T21:42:12.458835 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T21:27:12.764541 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T21:12:13.235462 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T20:57:10.342555 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T20:42:22.906118 — HOLD conf=0.6 trig=price_move ⛔ ?
- 2026-10-28T20:11:42.984327 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T19:56:58.200249 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T19:41:47.857881 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T19:41:16.687159 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T19:26:47.047797 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T19:11:49.993493 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T19:11:17.287874 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T18:56:53.876251 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T18:41:47.876721 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T18:41:17.050112 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T18:26:47.288538 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T18:11:49.244958 — HOLD conf=0.6 trig=news_event ⛔ ?
