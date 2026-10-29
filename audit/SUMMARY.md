# Audyt GielDarek — 2026-10-29T12:00:21Z

**Wdrożenie:** kod 17ba8e2 (zbud. 2026-10-29T08:55Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Automat (alpaca) zapauzowany ręcznie” (33× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 11 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 9 · odrzuconych: 111

**Najczęstsze powody odrzucenia (top):**
- 66× — brak powodu
- 13× — Automat (alpaca) zapauzowany ręcznie
- 12× — Automat (crypto) zapauzowany ręcznie
- 5× — Zlecenie niewykonane: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1350 min
- 1× — Cooldown po stop-lossie: AVAX/USD zablokowany do odkupu jeszcze ~1365 min
- 1× — Cooldown po stop-lossie: LINK/USD zablokowany do odkupu jeszcze ~1200 min
- 1× — Cooldown po stop-lossie: LINK/USD zablokowany do odkupu jeszcze ~1215 min

**Ostatnie 20 decyzji:**
- 2026-10-29T11:55:43.904016 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T11:40:47.749435 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T11:25:43.781298 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T11:10:43.995930 — HOLD conf=0.0 trig=price_move ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T10:55:44.013127 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T10:40:43.840956 — HOLD conf=0.0 trig=price_move ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T10:25:47.606774 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T10:10:44.825687 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T09:55:43.815040 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T09:40:44.018770 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T09:25:43.981881 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-29T09:10:48.039997 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (crypto) zapauzowany ręcznie
- 2026-10-28T22:27:01.802325 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T22:12:02.582205 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T21:57:10.396125 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T21:42:12.458835 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T21:27:12.764541 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T21:12:13.235462 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-28T20:57:10.342555 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-28T20:42:22.906118 — HOLD conf=0.6 trig=price_move ⛔ ?
