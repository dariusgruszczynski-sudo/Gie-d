# Audyt GielDarek — 2026-09-29T20:46:30Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 101 zamknięć · trafność 32.7% · zrealizowany $6.58
**7 dni:** 22 zamknięć · 13.6% · $-8.54   |   **30 dni:** 61 · 34.4% · $-2.85
**Edge:** śr. wygrana +$2.02 vs strata $-0.88 → na transakcję $0.06 (payoff 2.3×)
**Trzymanie:** zyski ~3.1 dni · straty ~2.7 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 101 zamknięć, trafność 33% — realnie zarabia (+$6.58).
- (bad) Trafność 7 dni 14% vs 30 dni 34% — spada.
- (bad) Ostatnie 7 dni: -8.54 $ z 22 zamknięć.
- (neu) Średnia wygrana +$2.02 vs strata −$0.88 (wygrana 2.3× większa) → na transakcję +$0.06. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (good) Czas trzymania zysków (~3 dni) i strat (~3 dni) podobny — bez „siedzenia na zysku”.
- (neu) Największy przeciek: MSFT (-7.11 $, 10 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (50 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)” (15× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-7.11 (10 zamk., 0%)
- AAPL: $-4.4 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.66 (4 zamk., 25%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 50 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 65 · odrzuconych: 55

**Najczęstsze powody odrzucenia (top):**
- 36× — brak powodu
- 8× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 8× — size_pct <= 0, nic do zrobienia
- 1× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-29T19:37:58.880255 SMH BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-29T19:37:53.774583 AAPL SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-29T19:07:55.348060 AVGO BUY conf=0.62 trig=news_event ⛔ Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 2026-09-29T18:37:51.157454 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-29T18:07:53.373267 GOOGL SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-29T17:37:52.462001 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-29T17:07:57.966912 NVDA BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-29T16:37:59.378207 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-29T16:08:02.038638 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-29T15:37:54.718704 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-29T15:08:03.452709 SMH BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-29T15:07:58.296326 AAPL SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-29T14:37:56.847480 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-29T14:08:09.727564 NFLX BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-29T13:38:13.422836 GOOGL BUY conf=0.62 trig=scheduled_daily ✅WYKONANE
- 2026-09-28T19:38:19.321370 QQQ SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T19:08:06.498893 NVDA SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-28T18:37:54.446256 NVDA BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-28T18:08:02.199587 NFLX BUY conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-28T18:08:02.192395 GLD SELL conf=0.3 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
