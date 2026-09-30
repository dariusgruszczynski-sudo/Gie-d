# Audyt GielDarek — 2026-09-30T22:57:08Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 104 zamknięć · trafność 31.7% · zrealizowany $5.84
**7 dni:** 18 zamknięć · 11.1% · $-6.18   |   **30 dni:** 62 · 33.9% · $-1.11
**Edge:** śr. wygrana +$2.02 vs strata $-0.86 → na transakcję $0.06 (payoff 2.35×)
**Trzymanie:** zyski ~3.1 dni · straty ~2.6 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 104 zamknięć, trafność 32% — realnie zarabia (+$5.84).
- (bad) Trafność 7 dni 11% vs 30 dni 34% — spada.
- (bad) Ostatnie 7 dni: -6.18 $ z 18 zamknięć.
- (neu) Średnia wygrana +$2.02 vs strata −$0.86 (wygrana 2.35× większa) → na transakcję +$0.06. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (good) Czas trzymania zysków (~3 dni) i strat (~3 dni) podobny — bez „siedzenia na zysku”.
- (neu) Największy przeciek: MSFT (-7.11 $, 10 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (51 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)” (15× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-7.11 (10 zamk., 0%)
- AAPL: $-4.4 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.66 (4 zamk., 25%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- AMZN: $-2.3 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 51 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 68 · odrzuconych: 52

**Najczęstsze powody odrzucenia (top):**
- 39× — brak powodu
- 9× — size_pct <= 0, nic do zrobienia
- 2× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-30T19:38:10.298660 NFLX BUY conf=0.62 trig=news_event ⛔ Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-30T19:08:03.956299 GOOGL BUY conf=0.6 trig=news_event ✅WYKONANE
- 2026-09-30T19:07:59.279639 AMZN SELL conf=0.5 trig=news_event ✅WYKONANE
- 2026-09-30T19:07:54.364187 COST SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-30T18:38:04.877039 LLY BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-30T18:37:59.674963 META SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-30T18:07:51.936454 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-30T17:37:50.271175 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-30T17:07:52.375682 NFLX BUY conf=0.62 trig=news_event ⛔ Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-30T16:37:52.035728 AMZN BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-30T16:08:03.901154 QQQ BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-30T16:07:59.031103 META BUY conf=0.68 trig=news_event ✅WYKONANE
- 2026-09-30T15:37:48.143692 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-30T15:07:56.427196 AVGO BUY conf=0.55 trig=news_event ⛔ Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 2026-09-30T15:07:56.409715 GOOGL BUY conf=0.5 trig=news_event ⛔ size_pct <= 0, nic do zrobienia
- 2026-09-30T14:37:50.908047 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-30T14:07:55.870350 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-30T13:38:18.742215 GOOGL BUY conf=0.6 trig=scheduled_daily ✅WYKONANE
- 2026-09-30T13:38:12.513296 MSFT BUY conf=0.62 trig=scheduled_daily ✅WYKONANE
- 2026-09-29T19:37:58.880255 SMH BUY conf=0.62 trig=news_event ✅WYKONANE
