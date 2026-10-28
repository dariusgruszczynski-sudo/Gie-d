# Audyt GielDarek — 2026-10-28T11:53:04Z

**Wdrożenie:** kod ae787c0 (zbud. 2026-10-27T20:39Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (58× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 11 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 26 · odrzuconych: 94

**Najczęstsze powody odrzucenia (top):**
- 61× — brak powodu
- 5× — Automat (alpaca) zapauzowany ręcznie
- 2× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1350 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1365 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1380 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1410 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1425 min

**Ostatnie 20 decyzji:**
- 2026-10-28T11:41:38.897493 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T11:26:36.343059 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T11:11:41.249522 PEPE/USD SELL conf=0.55 trig=news_event ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-10-28T10:56:43.103976 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T10:41:32.781975 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T10:26:38.319080 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T10:11:41.868225 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T09:56:38.155557 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T09:41:38.276258 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T09:26:44.271286 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T09:11:34.480366 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T08:56:42.820168 PEPE/USD SELL conf=0.65 trig=news_event ⛔ Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-10-28T08:41:41.445085 — HOLD conf=0.7 trig=news_event ⛔ ?
- 2026-10-28T08:26:43.078139 PEPE/USD SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-10-28T08:11:39.800946 PAXG/USD SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-10-28T07:56:40.862962 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T07:41:40.160217 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T07:26:38.453924 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T07:11:38.882659 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T06:56:39.909978 — HOLD conf=0.0 trig=news_event ⛔ ?
