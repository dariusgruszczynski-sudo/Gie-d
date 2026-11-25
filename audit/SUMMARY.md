# Audyt GielDarek — 2026-11-25T19:11:08Z

**Wdrożenie:** kod e04b5c2 (zbud. 2026-11-25T18:09Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (4 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Spadek od szczytu konta przekroczony: -100.0% (limit 55.0%, szczyt $840,728.19)” (17× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 5 · dni z limitem 4 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 62 decyzji · wykonanych: 19 · odrzuconych: 43

**Najczęstsze powody odrzucenia (top):**
- 17× — Spadek od szczytu konta przekroczony: -100.0% (limit 55.0%, szczyt $840,728.19)
- 15× — brak powodu
- 2× — Dzienny limit strat przekroczony: -65.0% (limit 30.0%)
- 1× — Filtr spreadu: MOODENG/EUR ma spread 1.97% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 1× — Filtr spreadu: MOODENG/EUR ma spread 4.04% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 1× — Filtr spreadu: PROS/EUR ma spread 1.24% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 1× — Rozjazd rekoncyliacji: baza vs broker różni się o $-14,564 (głównie ETH/USD: $-13,201) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)
- 1× — Rozjazd rekoncyliacji: baza vs broker różni się o $35 (głównie NIGHT/EUR: $12) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)

**Ostatnie 20 decyzji:**
- 2026-11-25T18:54:49.541408 BLUR/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-25T18:25:04.614569 LINK/EUR BUY conf=0.6 trig=price_move ✅WYKONANE
- 2026-11-25T18:25:00.012856 XTZ/EUR BUY conf=0.6 trig=price_move ✅WYKONANE
- 2026-11-25T10:55:52.449868 MOODENG/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-25T10:40:53.068492 MOODENG/EUR BUY conf=0.6 trig=news_event ⛔ Filtr spreadu: MOODENG/EUR ma spread 1.97% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 2026-11-25T10:25:53.487813 MOODENG/EUR BUY conf=0.6 trig=news_event ⛔ Filtr spreadu: MOODENG/EUR ma spread 4.04% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 2026-11-25T07:40:52.081845 PROS/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-25T07:25:58.180120 PROS/EUR BUY conf=0.6 trig=news_event ⛔ Filtr spreadu: PROS/EUR ma spread 1.24% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 2026-11-24T19:41:54.265599 — HOLD conf=0.0 trig=manual ⛔ ?
- 2026-11-24T17:24:15.881472 LINK/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-24T17:24:15.562839 NIGHT/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-24T13:18:34.998208 ALGO/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-24T13:03:40.297784 ATOM/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-24T11:33:40.238401 JUP/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-24T10:03:35.195512 QNT/EUR SELL conf=1.0 trig=price_move ✅WYKONANE
- 2026-11-24T06:18:49.176115 ATOM/EUR BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-11-24T05:53:07.101694 — HOLD conf=0.0 trig=manual ⛔ ?
- 2026-11-24T05:45:38.869386 ATOM/EUR BUY conf=0.6 trig=news_event ⛔ Zlecenie niewykonane: Rozmiar ATOM/EUR = €3.81 < min. zlecenia Krakena (~€4.24) po limitach koncentracji/płynności — pomijam (za mały kawałek na to konto)
- 2026-11-24T01:45:43.820938 ATOM/EUR BUY conf=0.6 trig=news_event ⛔ Zlecenie niewykonane: Rozmiar ATOM/EUR = €3.81 < min. zlecenia Krakena (~€4.18) po limitach koncentracji/płynności — pomijam (za mały kawałek na to konto)
- 2026-11-24T01:30:38.584519 ATOM/EUR BUY conf=0.6 trig=news_event ⛔ Zlecenie niewykonane: Rozmiar ATOM/EUR = €3.81 < min. zlecenia Krakena (~€4.15) po limitach koncentracji/płynności — pomijam (za mały kawałek na to konto)
