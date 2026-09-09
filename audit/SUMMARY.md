# Audyt GielDarek — 2026-09-09T10:28:37Z

**Wdrożenie:** kod a9eb9e7 (zbud. 2026-09-08T14:05Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 47 zamknięć · trafność 27.7% · zrealizowany $-0.07
**7 dni:** 5 zamknięć · 20.0% · $-7.02   |   **30 dni:** 48 · 27.1% · $-0.17
**Edge:** śr. wygrana +$2.83 vs strata $-1.09 → na transakcję $-0.0 (payoff 2.6×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.5 dni

## Wnioski
- (bad) Trafność 7 dni 20% vs 30 dni 27% — spada.
- (bad) Ostatnie 7 dni: -7.02 $ z 5 zamknięć.
- (good) Średnia wygrana +$2.83 vs strata −$1.09 (wygrana 2.6× większa) → na transakcję +$0.00. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: JAZZ (-4.31 $, 1 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.69 (baza 0.60 + 3 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (19× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- META: $-1.85 (2 zamk., 50%)
- OKTA: $-1.65 (1 zamk., 0%)
- V: $-1.54 (1 zamk., 0%)
- AAPL: $-1.24 (1 zamk., 0%)
- NDSN: $-1.08 (1 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true
