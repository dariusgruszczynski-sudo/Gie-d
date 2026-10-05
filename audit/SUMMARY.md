# Audyt GielDarek — 2026-10-05T18:19:21Z

**Wdrożenie:** kod 5464860 (zbud. 2026-10-05T18:17Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 16 zamknięć · 12.5% · $-2.3   |   **30 dni:** 67 · 32.8% · $8.33
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (bad) Trafność 7 dni 12% vs 30 dni 33% — spada.
- (bad) Ostatnie 7 dni: -2.30 $ z 16 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (54 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Dzienny limit strat przekroczony: -99.6% (limit 20.0%)” (35× z ostatnich 300 decyzji).

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
- ostatnie 120 decyzji · wykonanych: 30 · odrzuconych: 90

**Najczęstsze powody odrzucenia (top):**
- 35× — Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 23× — Automat (alpaca) zapauzowany ręcznie
- 17× — Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 9× — brak powodu
- 3× — size_pct <= 0, nic do zrobienia
- 1× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-10-05T17:56:29.779676 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T17:26:30.037894 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T16:56:29.680009 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T16:26:30.016487 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T15:56:30.088822 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T15:26:30.043082 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T14:56:29.883294 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T14:26:29.858799 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T13:56:29.838507 — HOLD conf=0.0 trig=scheduled_daily ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-05T11:24:00.023066 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T11:09:00.231016 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:53:59.865321 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:39:00.033581 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:24:00.032392 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T10:08:59.996271 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T09:53:59.838110 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T09:23:59.971304 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T09:08:59.921861 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T08:53:59.795839 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
- 2026-10-05T08:39:00.197576 — HOLD conf=0.0 trig=news_event ⛔ Dzienny limit strat przekroczony: -99.6% (limit 20.0%)
