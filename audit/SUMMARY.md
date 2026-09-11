# Audyt GielDarek — 2026-09-11T14:58:23Z

**Wdrożenie:** kod 3f87a0a (zbud. 2026-09-11T14:56Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 51 zamknięć · trafność 27.5% · zrealizowany $-5.3
**7 dni:** 6 zamknięć · 33.3% · $-5.34   |   **30 dni:** 48 · 27.1% · $-6.21
**Edge:** śr. wygrana +$2.8 vs strata $-1.2 → na transakcję $-0.1 (payoff 2.33×)
**Trzymanie:** zyski ~4.6 dni · straty ~2.8 dni

## Wnioski
- (bad) Wynik zamkniętych transakcji od 10.08: 51 zamknięć, trafność 27% — pod kreską (−$5.30).
- (good) Trafność 7 dni 33% vs 30 dni 27% — rośnie.
- (bad) Ostatnie 7 dni: -5.34 $ z 6 zamknięć.
- (bad) Średnia wygrana +$2.80 vs strata −$1.20 (wygrana 2.33× większa) → na transakcję −$0.10. Wygrane za małe wobec strat — to psuje wynik.
- (bad) ⚠ Zyski trzymane dłużej (~5 dni) niż straty (~3 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: MSFT (-5.33 $, 3 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (4 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (24× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- MSFT: $-5.33 (3 zamk., 0%)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- NVDA: $-2.4 (5 zamk., 20%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- V: $-1.54 (1 zamk., 0%)
- AAPL: $-1.24 (1 zamk., 0%)

## Wejścia vs limit
- cap 12/dzień · max w dniu 57 · dni z limitem 4 · hamuje: true

## Opus-kontroler (co REALNIE zmienił)
- włączony: false · ostatni przebieg: 2026-09-11 · baza wiedzy: 29 wpisów
- nadpisania knobów: BRAK (Opus nic nie zmienił od domyślnych)
- próg pewności — baza (env): 0.52 · progresja +0.02/pozycję do sufitu 0.9
