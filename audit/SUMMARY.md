# Audyt GielDarek — 2026-09-15T15:56:55Z

**Wdrożenie:** kod b8200bd (zbud. 2026-09-15T15:35Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 54 zamknięć · trafność 27.8% · zrealizowany $-7.21
**7 dni:** 8 zamknięć · 37.5% · $-6.02   |   **30 dni:** 41 · 29.3% · $-9.82
**Edge:** śr. wygrana +$2.74 vs strata $-1.24 → na transakcję $-0.13 (payoff 2.21×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.7 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 54 zamknięć, trafność 28% — pod kreską (−$7.21).
- (good) Trafność 7 dni 38% vs 30 dni 29% — rośnie.
- (bad) Ostatnie 7 dni: -6.02 $ z 8 zamknięć.
- (bad) Średnia wygrana +$2.74 vs strata −$1.24 (wygrana 2.21× większa) → na transakcję −$0.13. Wygrane za małe wobec strat — to psuje wynik.
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
- ostatnie 120 decyzji · wykonanych: 28 · odrzuconych: 92

**Najczęstsze powody odrzucenia (top):**
- 51× — brak powodu
- 16× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 8× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Zbyt niska pewność: 0.68 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — Zbyt niska pewność: 0.62 < próg 0.72 (baza 0.60 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — Zbyt niska pewność: 0.63 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.62 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-15T15:32:31.750185 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-15T15:27:28.730245 SPY BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:27:23.221357 TLT BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:27:18.442088 V BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:27:13.609825 SMH BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:27:08.855574 NVDA BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:27:04.207537 QQQ BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:26:59.142316 MSFT BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:26:54.297650 META BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:26:48.850888 AAPL BUY conf=0.52 trig=manual ✅WYKONANE
- 2026-09-15T15:26:48.821029 — HOLD conf=0.0 trig=manual ⛔ ?
- 2026-09-15T14:27:13.447097 GLD BUY conf=0.5 trig=news_event ✅WYKONANE
- 2026-09-15T14:27:07.371968 LLY BUY conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-15T14:27:00.532388 NFLX SELL conf=0.55 trig=news_event ✅WYKONANE
- 2026-09-15T13:57:16.148388 — HOLD conf=0.6 trig=price_move ⛔ ?
- 2026-09-14T19:56:45.888897 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-14T19:26:51.401153 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T18:56:53.957271 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T18:26:56.496724 — HOLD conf=0.6 trig=news_event ⛔ ?
- 2026-09-14T17:56:55.248048 — HOLD conf=0.6 trig=news_event ⛔ ?
