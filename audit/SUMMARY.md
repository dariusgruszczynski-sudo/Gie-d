# Audyt GielDarek — 2026-09-01T10:51:25Z

**Wdrożenie:** kod f514c50 (zbud. 2026-08-24T17:06Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 42 zamknięć · trafność 28.6% · zrealizowany $6.95
**7 dni:** 10 zamknięć · 20.0% · $-10.18   |   **30 dni:** 54 · 29.6% · $14.59
**Edge:** śr. wygrana +$2.98 vs strata $-0.96 → na transakcję $0.17 (payoff 3.1×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.1 dni

## Wnioski
- (bad) Trafność 7 dni 20% vs 30 dni 30% — spada.
- (bad) Ostatnie 7 dni: -10.18 $ z 10 zamknięć.
- (good) Średnia wygrana +$2.98 vs strata −$0.96 (wygrana 3.1× większa) → na transakcję +$0.17. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: JAZZ (-4.31 $, 1 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.60 < próg 0.67 (baza 0.55 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (21× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- JAZZ: $-4.31 (1 zamk., 0%)
- META: $-2.97 (1 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- NDSN: $-1.08 (1 zamk., 0%)
- ROST: $-1.0 (1 zamk., 0%)
- LITE: $-0.8 (2 zamk., 0%)
- DIS: $-0.76 (2 zamk., 0%)
- UGI: $-0.75 (1 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true
