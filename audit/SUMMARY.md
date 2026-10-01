# Audyt GielDarek — 2026-10-01T18:48:31Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 109 zamknięć · trafność 30.3% · zrealizowany $2.84
**7 dni:** 20 zamknięć · 5.0% · $-9.07   |   **30 dni:** 67 · 31.3% · $-4.11
**Edge:** śr. wygrana +$2.02 vs strata $-0.84 → na transakcję $0.03 (payoff 2.4×)
**Trzymanie:** zyski ~3.1 dni · straty ~2.8 dni

## Wnioski
- (neu) Wynik zamkniętych transakcji od 10.08: 109 zamknięć, trafność 30% — praktycznie na zero (+$2.84) — drepcze w miejscu.
- (bad) Trafność 7 dni 5% vs 30 dni 31% — spada.
- (bad) Ostatnie 7 dni: -9.07 $ z 20 zamknięć.
- (neu) Średnia wygrana +$2.02 vs strata −$0.84 (wygrana 2.4× większa) → na transakcję +$0.03. Edge ledwo dodatni — w granicach szumu małej próbki, nie licz na to jak na pewny zysk.
- (good) Czas trzymania zysków (~3 dni) i strat (~3 dni) podobny — bez „siedzenia na zysku”.
- (neu) Największy przeciek: MSFT (-7.11 $, 10 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (52 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „size_pct <= 0, nic do zrobienia” (16× z ostatnich 300 decyzji).

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
- 37× — brak powodu
- 11× — size_pct <= 0, nic do zrobienia
- 2× — Auto-degradacja AVGO: ujemna historia (1W/4L, P&L -3.73) — nowe wejście zablokowane
- 1× — Zbyt niska pewność: 0.62 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.87 (baza 0.60 + 9 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
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
- 2026-09-30T19:07:59.279639 AMZN SELL conf=0.5 trig=news_event ✅WYKONANE
- 2026-09-30T19:07:54.364187 COST SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-30T18:38:04.877039 LLY BUY conf=0.62 trig=news_event ✅WYKONANE
- 2026-09-30T18:37:59.674963 META SELL conf=0.55 trig=news_event ✅WYKONANE
