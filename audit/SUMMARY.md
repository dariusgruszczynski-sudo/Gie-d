# Audyt GielDarek — 2026-10-04T23:55:54Z

**Wdrożenie:** kod 0ce5409 (zbud. 2026-10-04T23:52Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

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
- (neu) Limit wejść bywa osiągany (53 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)” (17× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 53 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 52 · odrzuconych: 68

**Najczęstsze powody odrzucenia (top):**
- 23× — brak powodu
- 17× — Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 14× — Automat (alpaca) zapauzowany ręcznie
- 10× — size_pct <= 0, nic do zrobienia
- 2× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-10-04T23:34:55.131908 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T23:19:55.181642 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T23:04:55.300007 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T22:49:55.204133 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T22:34:55.302221 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T22:04:55.195533 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T21:49:55.230580 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T21:34:55.204571 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T21:19:55.252801 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T21:04:55.218845 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T20:49:55.144776 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T20:34:55.171521 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T20:19:55.380967 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T19:49:55.539653 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T19:19:55.338045 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T19:04:55.253955 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T18:49:55.959901 — HOLD conf=0.0 trig=news_event ⛔ Spadek od szczytu konta przekroczony: -88.5% (limit 45.0%, szczyt $99,448.83)
- 2026-10-04T18:17:49.914870 ETH/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-04T18:17:44.993227 LINK/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-10-04T18:17:41.651857 DOGE/USD BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
