# Audyt GielDarek — 2026-11-23T23:10:57Z

**Wdrożenie:** kod cbb43e0 (zbud. 2026-11-23T21:00Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (2 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Spadek od szczytu konta przekroczony: -100.0% (limit 55.0%, szczyt $840,728.19)” (17× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 4 · dni z limitem 2 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 41 decyzji · wykonanych: 7 · odrzuconych: 34

**Najczęstsze powody odrzucenia (top):**
- 17× — Spadek od szczytu konta przekroczony: -100.0% (limit 55.0%, szczyt $840,728.19)
- 13× — brak powodu
- 2× — Dzienny limit strat przekroczony: -65.0% (limit 30.0%)
- 1× — Rozjazd rekoncyliacji: baza vs broker różni się o $-14,564 (głównie ETH/USD: $-13,201) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 1× — Rozjazd rekoncyliacji: baza vs broker różni się o $35 (głównie NIGHT/EUR: $12) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)

**Ostatnie 20 decyzji:**
- 2026-11-23T21:15:35.441546 VVV/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-23T20:51:51.849216 — HOLD conf=0.6 trig=manual ⛔ Rozjazd rekoncyliacji: baza vs broker różni się o $35 (głównie NIGHT/EUR: $12) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 2026-11-23T20:43:29.338585 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -65.0% (limit 30.0%)
- 2026-11-23T20:40:10.572754 — HOLD conf=0.0 trig=manual ⛔ Dzienny limit strat przekroczony: -65.0% (limit 30.0%)
- 2026-11-23T17:17:25.658122 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T16:47:34.950928 TRX/EUR BUY conf=0.6 trig=news_event ⛔ ?
- 2026-11-23T16:32:37.731942 TRX/EUR BUY conf=0.6 trig=news_event ⛔ ?
- 2026-11-23T16:17:34.103094 TRX/EUR BUY conf=0.6 trig=news_event ⛔ ?
- 2026-11-23T15:32:25.182766 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T15:17:25.370854 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T15:02:25.434444 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T14:47:25.191917 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T14:32:30.706430 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T14:17:25.228217 QNT/EUR SELL conf=1.0 trig=price_move ⛔ ?
- 2026-11-23T14:02:34.262839 HYPE/EUR BUY conf=0.6 trig=news_event ⛔ ?
- 2026-11-23T13:47:40.015324 TRX/EUR BUY conf=0.6 trig=news_event ⛔ ?
- 2026-11-23T11:47:39.976247 ALGO/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-23T09:17:41.485703 TAO/EUR BUY conf=0.6 trig=news_event ⛔ ?
- 2026-11-23T09:17:39.091963 QNT/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-23T08:32:34.070527 JUP/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
