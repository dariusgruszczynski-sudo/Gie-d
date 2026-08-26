# Audyt GielDarek — 2026-08-26T06:33:38Z

**Wdrożenie:** kod f514c50 (zbud. 2026-08-24T17:06Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 34 zamknięć · trafność 32.4% · zrealizowany $17.18
**7 dni:** 14 zamknięć · 42.9% · $10.35   |   **30 dni:** 73 · 30.1% · $20.23
**Edge:** śr. wygrana +$2.88 vs strata $-0.63 → na transakcję $0.5 (payoff 4.57×)
**Trzymanie:** zyski ~4.9 dni · straty ~2.0 dni

## Wnioski
- (good) Trafność 7 dni 43% vs 30 dni 30% — rośnie.
- (good) Ostatnie 7 dni: +10.35 $ z 14 zamknięć.
- (good) Średnia wygrana +$2.88 vs strata −$0.63 (wygrana 4.57× większa) → na transakcję +$0.50. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~5 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: AMZN (-2.22 $, 1 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.60 < próg 0.67 (baza 0.55 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (26× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- AMZN: $-2.22 (1 zamk., 0%)
- NDSN: $-1.08 (1 zamk., 0%)
- ROST: $-1.0 (1 zamk., 0%)
- LITE: $-0.8 (2 zamk., 0%)
- DIS: $-0.76 (2 zamk., 0%)
- UGI: $-0.75 (1 zamk., 0%)
- TGT: $-0.68 (1 zamk., 0%)
- MSFT: $-0.59 (2 zamk., 0%)
- CVX: $-0.57 (1 zamk., 0%)
- WBD: $-0.42 (1 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true
