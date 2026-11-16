# Audyt GielDarek — 2026-11-16T22:50:20Z

**Wdrożenie:** kod 6b25598 (zbud. 2026-11-15T20:49Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)” (147× z ostatnich 300 decyzji).

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
- 73× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 45× — Automat (alpaca) zapauzowany ręcznie
- 1× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-11-16T20:50:11.575725 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T20:20:10.836851 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T19:50:10.848952 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T19:20:17.159614 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T18:50:11.607122 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T18:20:10.921456 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T17:50:10.867278 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T17:20:10.607928 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T16:50:11.338999 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T16:20:10.986937 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T15:50:11.088959 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T15:20:12.131847 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-16T14:50:10.477085 — HOLD conf=0.0 trig=price_move ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T20:43:30.416914 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T20:13:30.081751 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T19:43:30.318620 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T19:13:29.981825 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T18:43:30.403365 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T18:13:30.659283 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-11-13T17:43:30.395990 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
