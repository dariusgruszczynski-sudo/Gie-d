# Audyt GielDarek — 2026-09-15T10:44:52Z

**Wdrożenie:** kod 1a4f280 (zbud. 2026-09-14T16:56Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 53 zamknięć · trafność 28.3% · zrealizowany $-6.11
**7 dni:** 8 zamknięć · 37.5% · $-6.15   |   **30 dni:** 40 · 30.0% · $-8.72
**Edge:** śr. wygrana +$2.74 vs strata $-1.24 → na transakcję $-0.12 (payoff 2.21×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.8 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 53 zamknięć, trafność 28% — pod kreską (−$6.11).
- (good) Trafność 7 dni 38% vs 30 dni 30% — rośnie.
- (bad) Ostatnie 7 dni: -6.15 $ z 8 zamknięć.
- (bad) Średnia wygrana +$2.74 vs strata −$1.24 (wygrana 2.21× większa) → na transakcję −$0.12. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.33 $, 3 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (4 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.33 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.16 (2 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- NVDA: $-2.4 (5 zamk., 20%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- V: $-1.54 (1 zamk., 0%)

## Wejścia vs limit
- cap 12/dzień · max w dniu 57 · dni z limitem 4 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.52 · progresja +0.02/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 19 · odrzuconych: 101

**Najczęstsze powody odrzucenia (top):**
- 48× — brak powodu
- 19× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 9× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 5× — Zbyt niska pewność: 0.68 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Zbyt niska pewność: 0.62 < próg 0.72 (baza 0.60 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — Zbyt niska pewność: 0.63 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — Zbyt niska pewność: 0.65 < próg 0.72 (baza 0.60 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-14T19:56:45.888897 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-14T19:26:51.401153 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T18:56:53.957271 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T18:26:56.496724 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T17:56:55.248048 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T17:27:11.913239 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T16:32:55.508398 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T16:02:57.474750 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T15:33:19.339377 NFLX BUY conf=0.53 trig=scheduled_daily ✅WYKONANE
- 2026-09-14T15:33:13.795114 GOOGL BUY conf=0.58 trig=scheduled_daily ✅WYKONANE
- 2026-09-14T14:26:53.738287 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-14T13:57:20.643706 META SELL conf=0.55 trig=price_move ✅WYKONANE
- 2026-09-14T13:57:14.800011 AVGO SELL conf=0.6 trig=price_move ✅WYKONANE
- 2026-09-11T19:56:56.028861 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-11T19:26:54.829560 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-11T18:56:47.718464 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-11T18:26:57.994249 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-11T17:56:50.945875 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-11T17:26:45.535036 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-11T16:57:38.362840 — HOLD conf=0.0 trig=news_event ⛔ ?
