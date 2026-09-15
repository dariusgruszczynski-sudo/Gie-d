# Audyt GielDarek — 2026-09-15T16:47:38Z

**Wdrożenie:** kod 0a154f4 (zbud. 2026-09-15T16:47Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 55 zamknięć · trafność 27.3% · zrealizowany $-7.39
**7 dni:** 9 zamknięć · 33.3% · $-6.19   |   **30 dni:** 42 · 28.6% · $-9.99
**Edge:** śr. wygrana +$2.74 vs strata $-1.21 → na transakcję $-0.13 (payoff 2.26×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.6 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 55 zamknięć, trafność 27% — pod kreską (−$7.39).
- (neu) Trafność 7 dni 33% vs 30 dni 29% — stabilna.
- (bad) Ostatnie 7 dni: -6.19 $ z 9 zamknięć.
- (bad) Średnia wygrana +$2.74 vs strata −$1.21 (wygrana 2.26× większa) → na transakcję −$0.13. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.33 $, 3 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (6 dni) — podniesienie może dołożyć wejść.
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
- cap 6/dzień · max w dniu 57 · dni z limitem 6 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 29 · odrzuconych: 91

**Najczęstsze powody odrzucenia (top):**
- 51× — brak powodu
- 14× — Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 7× — Zbyt niska pewność: 0.65 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.62 < próg 0.72 (baza 0.60 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 3× — Zbyt niska pewność: 0.63 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.60 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2× — Zbyt niska pewność: 0.62 < próg 0.66 (baza 0.60 + 2 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-15T16:30:22.268142 AVGO BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:22.251001 AMZN BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:22.229845 JPM BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:22.202367 COST BUY conf=0.52 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-15T16:30:17.139039 GLD BUY conf=0.53 trig=news_event ✅WYKONANE
- 2026-09-15T16:30:10.972582 META SELL conf=0.55 trig=news_event ✅WYKONANE
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
