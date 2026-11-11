# Audyt GielDarek — 2026-11-11T13:17:07Z

**Wdrożenie:** kod ceee8db (zbud. 2026-11-11T09:32Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (11 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)” (151× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 9 · dni z limitem 11 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 0 · odrzuconych: 120

**Najczęstsze powody odrzucenia (top):**
- 110× — Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 9× — Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 1× — brak powodu

**Ostatnie 20 decyzji:**
- 2026-11-11T13:02:37.676493 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T12:47:32.844211 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T12:32:33.000179 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T12:17:32.780904 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T12:02:37.095239 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T11:47:32.798289 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T11:32:33.087855 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T11:17:32.972861 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T11:02:33.001327 PEPE/USD SELL conf=1.0 trig=price_move ⛔ Wyjście niewykonalne: Alpaca POST /v2/orders: 403 {"available":"963060308.407551403","balance":"963060308.407551403","code":40310000,"message":"insufficient balance for PEPE (requested: 963060308.407551408, available: 963060308.407551403)","symbol":"USD"}
- 2026-11-11T09:44:56.601330 — HOLD conf=0.7 trig=manual ⛔ ?
- 2026-11-11T08:45:38.949945 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T08:30:42.940495 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T08:15:39.090762 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T08:00:39.090202 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T07:45:38.764318 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T07:30:42.788903 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T07:15:39.090251 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T07:00:38.738153 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T06:45:38.898598 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-11T06:30:38.905387 — HOLD conf=0.0 trig=scheduled_daily ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $220,887 (głównie HYPE/USD: $214,910) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
