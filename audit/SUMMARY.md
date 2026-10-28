# Audyt GielDarek — 2026-10-28T18:46:54Z

**Wdrożenie:** kod ae787c0 (zbud. 2026-10-27T20:39Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (38× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 11 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 14 · odrzuconych: 106

**Najczęstsze powody odrzucenia (top):**
- 65× — brak powodu
- 11× — Automat (alpaca) zapauzowany ręcznie
- 5× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1350 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1365 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1380 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1410 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1425 min

**Ostatnie 20 decyzji:**
- 2026-10-28T18:41:47.876721 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T18:41:17.050112 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T18:26:47.288538 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T18:11:49.244958 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T18:11:16.767327 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T17:56:41.524998 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T17:42:01.134000 PEPE/USD SELL conf=0.55 trig=news_event ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-10-28T17:41:16.689485 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T17:26:47.916151 PEPE/USD SELL conf=0.55 trig=news_event ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-10-28T17:11:46.338511 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T17:11:16.348530 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T16:56:44.824844 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T16:41:51.141162 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T16:41:16.457194 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T16:26:44.451365 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T16:12:10.974858 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T16:11:16.542311 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-28T15:56:44.798691 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T15:41:46.563923 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T15:41:16.437797 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
