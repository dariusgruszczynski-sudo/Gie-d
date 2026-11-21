# Audyt GielDarek — 2026-11-21T22:10:21Z

**Wdrożenie:** kod 39a881e (zbud. 2026-11-21T22:02Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (12 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}” (99× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 12 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 3 · odrzuconych: 117

**Najczęstsze powody odrzucenia (top):**
- 86× — Automat (alpaca) zapauzowany ręcznie
- 23× — Automat (crypto) zapauzowany ręcznie
- 6× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-11-21T21:04:35.547983 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T20:49:32.119720 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T20:34:32.136281 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T20:19:32.223122 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T20:04:35.546009 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T19:49:32.024456 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T19:34:32.298857 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T19:19:32.107654 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T19:04:32.251091 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T18:49:35.903177 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T18:23:30.819089 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T18:08:32.918570 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T17:53:34.214713 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T17:18:34.020149 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T16:58:31.462661 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T16:43:31.543550 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T16:28:31.227242 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T16:13:35.044613 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T15:58:31.392713 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T15:43:31.487545 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
