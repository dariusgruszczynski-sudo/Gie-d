# Audyt GielDarek — 2026-08-28T17:56:26Z

**Wdrożenie:** kod f514c50 (zbud. 2026-08-24T17:06Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 39 zamknięć · trafność 30.8% · zrealizowany $11.57
**7 dni:** 9 zamknięć · 33.3% · $-2.39   |   **30 dni:** 62 · 27.4% · $14.21
**Edge:** śr. wygrana +$2.98 vs strata $-0.9 → na transakcję $0.3 (payoff 3.31×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.1 dni

## Wnioski
- (good) Trafność 7 dni 33% vs 30 dni 27% — rośnie.
- (bad) Ostatnie 7 dni: -2.39 $ z 9 zamknięć.
- (good) Średnia wygrana +$2.98 vs strata −$0.90 (wygrana 3.31× większa) → na transakcję +$0.30. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: JAZZ (-4.31 $, 1 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.62 < próg 0.70 (baza 0.55 + 5 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (20× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- JAZZ: $-4.31 (1 zamk., 0%)
- META: $-2.97 (1 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- NDSN: $-1.08 (1 zamk., 0%)
- ROST: $-1.0 (1 zamk., 0%)
- LITE: $-0.8 (2 zamk., 0%)
- DIS: $-0.76 (2 zamk., 0%)
- UGI: $-0.75 (1 zamk., 0%)
- TGT: $-0.68 (1 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true
