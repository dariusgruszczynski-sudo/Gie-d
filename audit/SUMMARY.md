# Audyt GielDarek — 2026-10-02T11:38:22Z

**Wdrożenie:** kod 29deae9 (zbud. 2026-10-01T20:08Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 112 zamknięć · trafność 30.4% · zrealizowany $8.37
**7 dni:** 23 zamknięć · 8.7% · $-3.54   |   **30 dni:** 70 · 31.4% · $1.42
**Edge:** śr. wygrana +$2.13 vs strata $-0.82 → na transakcję $0.07 (payoff 2.6×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 112 zamknięć, trafność 30% — realnie zarabia (+$8.37).
- (bad) Trafność 7 dni 9% vs 30 dni 31% — spada.
- (bad) Ostatnie 7 dni: -3.54 $ z 23 zamknięć.
- (neu) Średnia wygrana +$2.13 vs strata −$0.82 (wygrana 2.6× większa) → na transakcję +$0.07. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-7.26 $, 11 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (52 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „size_pct <= 0, nic do zrobienia” (16× z ostatnich 300 decyzji).

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
- cap 0/dzień · max w dniu 57 · dni z limitem 52 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 68 · odrzuconych: 52

**Najczęstsze powody odrzucenia (top):**
- 36× — brak powodu
- 11× — size_pct <= 0, nic do zrobienia
- 2× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Automat (alpaca) zapauzowany ręcznie
- 1× — Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-10-01T19:07:31.591585 — HOLD conf=0.0 trig=news_event ⛔ Automat (alpaca) zapauzowany ręcznie
- 2026-10-01T18:52:03.724443 QQQ SELL conf=1.0 trig=manual ✅WYKONANE
- 2026-10-01T18:51:47.277251 MSFT SELL conf=1.0 trig=manual ✅WYKONANE
- 2026-10-01T18:51:35.938142 SMH SELL conf=1.0 trig=manual ✅WYKONANE
- 2026-10-01T18:37:50.364629 META SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-10-01T18:07:55.883388 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-01T17:37:53.036951 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-10-01T17:07:50.975377 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-01T16:37:50.426439 QQQ SELL conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-10-01T16:07:52.033370 NVDA BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-10-01T15:37:55.077035 META SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-10-01T15:07:57.240314 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-10-01T14:37:49.669314 SPY SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-10-01T14:08:09.103250 MSFT BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-10-01T14:08:04.551706 SMH BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-10-01T14:07:59.635634 LLY SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-10-01T14:07:54.258721 GOOGL SELL conf=0.65 trig=news_event ✅WYKONANE
- 2026-10-01T13:38:09.962787 — HOLD conf=0.6 trig=price_move ⛔ ?
- 2026-09-30T19:38:10.298660 NFLX BUY conf=0.62 trig=news_event ⛔ Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-30T19:08:03.956299 GOOGL BUY conf=0.6 trig=news_event ✅WYKONANE
