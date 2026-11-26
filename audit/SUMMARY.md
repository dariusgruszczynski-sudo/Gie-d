# Audyt GielDarek — 2026-11-26T16:05:28Z

**Wdrożenie:** kod e04b5c2 (zbud. 2026-11-25T18:09Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 0 zamknięć · trafność —% · zrealizowany $0.0
**7 dni:** 0 zamknięć · —% · $0.0   |   **30 dni:** 0 · —% · $0.0
**Edge:** śr. wygrana +$— vs strata $— → na transakcję $— (payoff —×)
**Trzymanie:** zyski ~— dni · straty ~— dni

## Wnioski
- (neu) Za mało zamkniętych transakcji (0) na mocne wnioski — bot dopiero zbiera próbkę.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)” (61× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)

## Wejścia vs limit
- cap 0/dzień · max w dniu 5 · dni z limitem 5 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 28 · odrzuconych: 92

**Najczęstsze powody odrzucenia (top):**
- 61× — Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 15× — brak powodu
- 5× — Spadek od szczytu konta przekroczony: -100.0% (limit 55.0%, szczyt $840,728.19)
- 2× — Dzienny limit strat przekroczony: -65.0% (limit 30.0%)
- 1× — Filtr spreadu: MOODENG/EUR ma spread 1.97% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 1× — Filtr spreadu: MOODENG/EUR ma spread 4.04% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 1× — Filtr spreadu: PROS/EUR ma spread 1.24% > próg 0.80% — zbyt cienki rynek, sam spread zjadłby przewagę; wejście pominięte (wyjścia/stopy działają bez zmian)
- 1× — Rozjazd rekoncyliacji: baza vs broker różni się o $-14,564 (głównie ETH/USD: $-13,201) — handel wstrzymany (księgi nie zgadzają się z brokerem; NIE blacklista monet; rozwiąż desync: reset papierowego konta albo re-sync ledgera, potem Wznów)

**Ostatnie 20 decyzji:**
- 2026-11-26T14:55:00.562128 WIF/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T14:55:00.537296 STBL/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T14:39:50.126748 DOGE/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T14:39:50.102764 MANA/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T14:39:50.071893 WIF/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T14:24:50.370588 MANA/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T14:24:50.348468 WIF/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T13:55:05.702554 QNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:55:00.672383 QNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:55:00.647273 MNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:55:00.622270 SKY/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:39:49.592652 MNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:39:49.571103 QNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:39:49.544470 JUP/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:39:49.251656 ALGO/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:24:49.135401 QNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:24:49.113407 MNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:24:49.090027 ALGO/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:10:00.505410 MANA/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-11-26T12:10:00.440756 MNT/EUR BUY conf=0.6 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (5) — nowe BUY wstrzymane do jutra (anty-churn)
