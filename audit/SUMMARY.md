# Audyt GielDarek — 2026-09-22T10:39:32Z

**Wdrożenie:** kod 3b3f16e (zbud. 2026-09-21T20:07Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 75 zamknięć · trafność 38.7% · zrealizowany $15.35
**7 dni:** 22 zamknięć · 63.6% · $21.46   |   **30 dni:** 45 · 44.4% · $1.39
**Edge:** śr. wygrana +$2.26 vs strata $-1.1 → na transakcję $0.2 (payoff 2.05×)
**Trzymanie:** zyski ~3.3 dni · straty ~2.5 dni

## Wnioski
- (good) Wynik zamkniętych transakcji od 10.08: 75 zamknięć, trafność 39% — realnie zarabia (+$15.35).
- (good) Trafność 7 dni 64% vs 30 dni 44% — rośnie.
- (good) Ostatnie 7 dni: +21.46 $ z 22 zamknięć.
- (good) Średnia wygrana +$2.26 vs strata −$1.10 (wygrana 2.05× większa) → na transakcję +$0.20. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~3 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.86 $, 4 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (44 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.86 (4 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- AVGO: $-3.16 (3 zamk., 33%)
- ESTC: $-2.48 (2 zamk., 0%)
- GLD: $-2.37 (2 zamk., 0%)
- V: $-2.29 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- AAPL: $-1.24 (1 zamk., 0%)

## Wejścia vs limit
- cap 0/dzień · max w dniu 57 · dni z limitem 44 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.6 · progresja +0.03/pozycję do sufitu 0.9

## Dziennik decyzji — dlaczego (NIE) handluje
- ostatnie 120 decyzji · wykonanych: 53 · odrzuconych: 67

**Najczęstsze powody odrzucenia (top):**
- 38× — brak powodu
- 15× — Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 5× — size_pct <= 0, nic do zrobienia
- 4× — Limit nowych wejść na dziś osiągnięty (12) — nowe BUY wstrzymane do jutra (anty-churn)
- 3× — Zbyt niska pewność: 0.60 < próg 0.81 (baza 0.60 + 7 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 1× — Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału

**Ostatnie 20 decyzji:**
- 2026-09-21T19:46:18.935552 META BUY conf=0.62 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:46:18.918317 QQQ BUY conf=0.65 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:46:18.881037 SMH BUY conf=0.68 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:17:45.411290 SMH BUY conf=0.62 trig=manual ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T19:17:05.655566 META SELL conf=1.0 trig=manual ✅WYKONANE
- 2026-09-21T19:16:12.612986 META SELL conf=0.72 trig=news_event ✅WYKONANE
- 2026-09-21T18:46:12.668243 QQQ BUY conf=0.68 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T18:46:12.649166 SMH BUY conf=0.65 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T18:16:12.333059 GLD BUY conf=0.55 trig=news_event ⛔ Zbyt niska pewność: 0.55 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-21T18:16:12.319196 SMH BUY conf=0.62 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T17:46:13.716357 SMH BUY conf=0.65 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T17:46:13.701556 MSFT BUY conf=0.62 trig=news_event ⛔ Zbyt niska pewność: 0.62 < próg 0.78 (baza 0.60 + 6 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału
- 2026-09-21T17:16:13.784043 — HOLD conf=0.0 trig=news_event ⛔ ?
- 2026-09-21T16:46:09.507617 — HOLD conf=0.6 trig=price_move ⛔ ?
- 2026-09-21T16:16:16.122902 SMH BUY conf=0.62 trig=news_event ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T16:03:54.213960 SMH BUY conf=0.62 trig=manual ⛔ Limit nowych wejść na dziś osiągnięty (6) — nowe BUY wstrzymane do jutra (anty-churn)
- 2026-09-21T16:03:48.077139 AVGO SELL conf=0.55 trig=manual ✅WYKONANE
- 2026-09-21T16:02:25.315003 LLY SELL conf=0.55 trig=manual ✅WYKONANE
- 2026-09-21T16:02:19.977105 META SELL conf=0.65 trig=manual ✅WYKONANE
- 2026-09-21T16:01:37.091876 QQQ SELL conf=1.0 trig=manual ✅WYKONANE
