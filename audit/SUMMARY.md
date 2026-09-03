# Audyt GielDarek — 2026-09-03T10:26:59Z

**Wdrożenie:** kod 6b2e00a (zbud. 2026-09-02T16:15Z) · duże zakłady (conviction): true · sufit ryzyka 6.0%

**Od zmiany strategii (tylko akcje):** 44 zamknięć · trafność 27.3% · zrealizowany $1.58
**7 dni:** 9 zamknięć · 11.1% · $-11.3   |   **30 dni:** 52 · 30.8% · $10.34
**Edge:** śr. wygrana +$2.98 vs strata $-1.07 → na transakcję $0.04 (payoff 2.79×)
**Trzymanie:** zyski ~4.5 dni · straty ~2.3 dni

## Wnioski
- (bad) Trafność 7 dni 11% vs 30 dni 31% — spada.
- (bad) Ostatnie 7 dni: -11.30 $ z 9 zamknięć.
- (good) Średnia wygrana +$2.98 vs strata −$1.07 (wygrana 2.79× większa) → na transakcję +$0.04. Zarabia mimo <50% trafności — edge dodatni.
- (bad) ⚠ Zyski trzymane dłużej (~4 dni) niż straty (~2 dni) — automat zwleka z realizacją zysku.
- (neu) Największy przeciek: JAZZ (-4.31 $, 1 zamk.) — kandydat do wyrzucenia z listy.
- (neu) Limit wejść bywa osiągany (5 dni) — podniesienie może dołożyć wejść.
- (neu) Najczęstszy powód pominięcia wejścia: „Zbyt niska pewność: 0.60 < próg 0.67 (baza 0.55 + 4 pozycji × 0.03) — wejście pominięte, kolejne wejścia wymagają mocniejszego sygnału” (17× z ostatnich 300 decyzji).

## Przecieki per symbol (najgorsze)
- JAZZ: $-4.31 (1 zamk., 0%)
- CRWD: $-3.72 (1 zamk., 0%)
- META: $-2.97 (1 zamk., 0%)
- ESTC: $-2.48 (2 zamk., 0%)
- AMZN: $-2.22 (1 zamk., 0%)
- GLD: $-2.21 (1 zamk., 0%)
- OKTA: $-1.65 (1 zamk., 0%)
- NDSN: $-1.08 (1 zamk., 0%)
- ROST: $-1.0 (1 zamk., 0%)
- LITE: $-0.8 (2 zamk., 0%)

## Wejścia vs limit
- cap 8/dzień · max w dniu 57 · dni z limitem 5 · hamuje: true
