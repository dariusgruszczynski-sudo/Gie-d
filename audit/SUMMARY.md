# Audyt GielDarek — 2026-11-21T18:33:40Z

**Wdrożenie:** kod 04ea19e (zbud. 2026-11-21T17:38Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

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
- 16× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 13× — Automat (crypto) zapauzowany ręcznie
- 2× — brak powodu

**Ostatnie 20 decyzji:**
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
- 2026-11-21T15:28:31.354275 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T15:13:31.451247 — HOLD conf=0.0 trig=news_event ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T14:58:34.974960 — HOLD conf=0.0 trig=price_move ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-11-21T13:46:43.982183 ETH/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-21T13:46:40.604394 UNI/USD BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-20T20:34:25.854767 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-20T20:04:26.241428 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-20T19:34:26.072009 — HOLD conf=0.0 trig=price_move ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-20T18:34:30.745512 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-20T18:24:08.867060 — HOLD conf=0.0 trig=manual ⛔ ?
