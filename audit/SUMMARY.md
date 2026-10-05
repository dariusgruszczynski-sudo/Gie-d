# Audyt GielDarek — 2026-10-05T11:08:52Z

**Wdrożenie:** kod f3c1ae8 (zbud. 2026-10-05T04:38Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 22 zamknięć · 9.1% · $-3.5   |   **30 dni:** 67 · 32.8% · $8.33
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (bad) Trafność 7 dni 9% vs 30 dni 33% — spada.
- (bad) Ostatnie 7 dni: -3.50 $ z 22 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (54 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Dzienny limit strat przekroczony: -99.6% (limit 20.0%)” (33× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-7.26 (11 zamk., 0%)
- AAPL: $-4.4 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.66 (4 zamk., 25%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- AMZN: $-2.3 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- GOOGL: $-2.25 (6 zamk., 33%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 54 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 35 · odrzuconych: 85

**Najczęstsze powody odrzucenia (top):**
- 33× — Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 17× — Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 14× — Automat (alpaca) zapauzowany ręcznie
- 13× — brak powodu
- 4× — size_pct <= 0, nic do zrobienia
- 2× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-10-05T10:53:59.865321 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:39:00.033581 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:24:00.032392 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:08:59.996271 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T09:53:59.838110 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T09:23:59.971304 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T09:08:59.921861 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T08:53:59.795839 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T08:39:00.197576 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T08:23:59.906014 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T07:53:59.907126 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T07:39:00.234185 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T07:23:59.885416 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T07:09:00.033154 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T06:39:00.129777 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T06:23:59.810938 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T05:38:59.931714 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T05:23:59.764749 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T04:33:37.733538 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T04:18:37.736848 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
