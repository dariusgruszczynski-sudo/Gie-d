# GielDarek — backlog 100 usprawnień do wdrożenia (2026-11-19)

> Zlecenie: „przygotuj propozycje 100 usprawnień do wdrożenia we wszystkich warstwach".
> Uzupełnienie do `rewizja-zalozen-2026-11-19.md` (tamto = „dlaczego", to = „co zbudować").
> Priorytety: **P1** krytyczny · **P2** ważny · **P3** porządkowy. Każdy punkt jest
> celowo konkretny (do odhaczenia), nie ogólnikiem. Kolejność grup ≈ od rdzenia do dłu­gu.

## A. Funkcja celu / premisa
1. **[P1]** Zakoduj cel jako testowalną metrykę w scorecard: `beats_btc_by_pct` + `max_dd_pct` z progami → dashboard PASS/FAIL.
2. **[P1]** Policz równolegle baseline „hold BTC" i „DCA BTC" w tym samym oknie — stała linia odniesienia w API.
3. **[P1]** Kill-criterion jako alarm: po ≥N zamknięciach wynik < BTC → push „strategia nie bije benchmarku".
4. **[P2]** Metryka „% czasu w rynku" + „śr. liczba otwartych pozycji" w API/UI.
5. **[P2]** Zapisz w configu/README jawny wybór: „zarabiać" vs „projekt/walidacja" — determinuje resztę.

## B. Paraliż / bramki wejścia (najpilniejsze)
6. **[P1]** `entry_funnel`: co cykl loguj, ilu kandydatów odpadło na KTÓREJ bramce (HTF/BTC-core/konfluencja/ADX/MTF/płynność/cap).
7. **[P1]** Endpoint `/api/entry-funnel` + panel „dlaczego nie wchodzi" (lejek z liczbami).
8. **[P1]** Tryb „benchmark fallback": w risk-on bez sygnału trzymaj BTC zamiast gotówki (config-gated).
9. **[P1]** Alarm bezczynności: 0 wejść przez N dni przy wolnej gotówce → push.
10. **[P1]** Licznik fill-rate (chciał vs wszedł) w scorecard.
11. **[P2]** „Dry-entry" log: co cykl zapisz najlepszego kandydata i jego score, nawet gdy nie wszedł (widać, jak blisko progu).
12. **[P2]** Przełącznik „solo-gate" (diagnostyka): zostaw jedną bramkę, zobacz ile wejść by było.

## C. Sygnał / strategia
13. **[P1]** Skrypt ablacji bramek: walk-forward z każdą bramką wyłączoną po kolei → raport wkładu każdej.
14. **[P1]** Zakoduj najprostszą strategię odniesienia (BTC: cena vs SMA200) do porównania w backteście.
15. **[P2]** Zastąp „głosowanie" SMA/MACD/RSI jednym scoringiem trend+siła (ADX) — mniej skorelowanych wejść.
16. **[P2]** „Slow mode": osobny poll (np. 4h) i horyzont dniowy, zgodny z tezą trend-following z `krypto-strategia.md`.
17. **[P2]** Scal 3 filtry trendu BTC (HTF/BTC-core/MTF) w jeden `trend_regime`.
18. **[P2]** Regime-aware sizing (większa pozycja w mocnym trendzie, mniejsza w chopie) zamiast on/off.
19. **[P3]** Jeśli zostaje breakout — udowodnij walk-forward, że bije sam trend, inaczej usuń.

## D. Ryzyko / sizing
20. **[P1]** Portfelowy cap beta-do-BTC (suma skorelowanych pozycji), nie tylko liczba pozycji.
21. **[P1]** Wymuś policzone R przy KAŻDYM wejściu; brak R → brak wejścia.
22. **[P2]** Ablacja 5 mechanizmów wyjścia → zostaw te z dodatnim wkładem.
23. **[P2]** Dzienny/tygodniowy „risk budget" w R (nie %); stop po wyczerpaniu.
24. **[P2]** Korelacyjny sizing (knob już jest) — udowodnij walk-forward albo usuń.
25. **[P3]** Pokaż realną stratę w $ przy maks. stopie vol-skalowanym (sanity dużych pozycji).

## E. Egzekucja / broker
26. **[P1]** Warstwa `BrokerAdapter` z twardą normalizacją ilości/precyzji per-giełda (lekcja float-ULP).
27. **[P1]** Property-based testy egzekucji: pełne wyjście z resztówką, min-notional, zaokrąglenia.
28. **[P2]** Retry z backoff na przejściowe błędy brokera (403/429/5xx), z limitem i logiem.
29. **[P2]** Idempotencja zleceń (client_order_id), by retry nie dublował.
30. **[P2]** Symulacja poślizgu także w LIVE-paper (nie tylko backtest) — paper bliżej realu.
31. **[P1]** Prewencyjna walidacja „ledger == saldo brokera" PRZED zleceniem (nie tylko watchdog po cyklu).

## F. Venue / dane
32. **[P1]** Ogranicz uniwersum do głęboko płynnych (BTC/ETH + ewentualnie top-3) — koniec altów na cienkim venue.
33. **[P1]** Twardy próg płynności (dolarowy wolumen) jako WARUNEK wejścia, nie tylko sizing.
34. **[P2]** Walidacja jakości świec: odrzuć symbol z lukami/zerami w OHLC (śmieciowe dane = śmieciowe sygnały).
35. **[P2]** Abstrakcja `MarketDataProvider` pod przyszły Kraken (zmiana venue bez przepisywania silnika).
36. **[P3]** Cache + rate-limit feedów z metryką świeżości (ostatni fetch, ile stale).
37. **[P3]** Fallback źródła ceny (druga giełda/agregator) na awarię głównego feedu.

## G. Pomiar / scorecard / honesty
38. **[P1]** Honesty: `status="idle"` przy 0 trejdów — zamiast mylącej alfy „+16%".
39. **[P1]** Seria equity strategii vs BTC vs DCA w API (do wykresu).
40. **[P2]** Rozbij realized na „nowa era" vs „zaszłości" jawnie (dziś miesza przy porządkach typu PEPE).
41. **[P2]** Sharpe/Sortino/Calmar na ŻYWYM koncie (nie tylko backtest).
42. **[P1]** „Reguła mark-epoch" w kodzie: wymaga powodu (enum zmiana-strategii) + log audytu; blokuj reset po złym wyniku.
43. **[P1]** Dashboard: jeden werdykt-baner na górze (ZARABIA / NIE / BEZCZYNNY vs BTC).
44. **[P2]** Dzienny snapshot equity do DB (historia krzywej kapitału, nie tylko transakcje).

## H. Pętla uczenia / feature store
45. **[P2]** Eksport feature store do trwałego storage (wersjonowany parquet/CSV), nie tylko on-the-fly.
46. **[P2]** Etykiety MFE/MAE (max favorable/adverse excursion) per trejd — bogatsze niż sam pnl.
47. **[P2]** Walidacja OOS jako cron: co tydzień licz i dopisuj do dziennika automatycznie.
48. **[P3]** „Feature importance" (korelacja cechy z R) w panelu uczenia.
49. **[P3]** Wykrywanie dryfu cech (rozkład teraz vs trening) → alarm, gdy rynek się zmienił.
50. **[P2]** Twardy próg N zamknięć, zanim jakikolwiek wniosek uczenia jest pokazany (anty-szum).

## I. LLM / shadow
51. **[P2]** Shadow: zapisuj cenę forward w kilku horyzontach (1h/4h/24h), nie licz on-the-fly.
52. **[P2]** Cotygodniowy auto-raport shadow (trend `buy_beats_hold` w czasie) do dziennika.
53. **[P1]** Zakoduj próg + datę decyzji LLM: po oknie auto-rekomendacja GO/NO-GO, inaczej kasacja warstwy.
54. **[P2]** Koszt LLM jako % realized w honesty (nie absolut).
55. **[P3]** A/B shadow: różne prompty/modele, który (jeśli w ogóle) bije mechanikę.
56. **[P3]** Hard-cap tokenów per-dzień (nie tylko miesięczny) — gładszy rozkład, brak luki pod koniec miesiąca.

## J. Backtest / walk-forward
57. **[P1]** Walk-forward z oknami kroczącymi (rolling train/test), nie jeden split → raport stabilności.
58. **[P2]** Realistyczne koszty: fee + poślizg + spread per-symbol (poślizg już jest).
59. **[P2]** Monte-Carlo na kolejności trejdów → rozkład DD i wyniku (czy to nie szczęście).
60. **[P1]** Benchmark hold-BTC i DCA wbudowany w KAŻDY raport backtestu.
61. **[P3]** „Kapsuła danych": zamrożony zestaw do powtarzalnych backtestów (regresja strategii).
62. **[P1]** Raport „trejdów/mies." i „% czasu w rynku" w backteście — łapie paraliż PRZED produkcją.

## K. Autonomia / scheduling / nadzór
63. **[P1]** Self-check: scheduler nie odpalił cyklu przez X min → alarm (martwy silnik).
64. **[P2]** Health-endpoint z „ostatni cykl / ostatnie wejście / ostatni błąd" w jednym miejscu.
65. **[P1]** Watchdog bezczynności: 0 decyzji zapisanych przez N godz. przy risk-on → alarm.
66. **[P3]** Dzienny raport nadzoru także jako commit do dziennika (trwały ślad, nie tylko wiadomość).
67. **[P2]** Audit-snapshot częściej w weekendy (dziś hourly tylko pn-pt; krypto jest 24/7).

## L. UX / dashboard
68. **[P1]** Baner-werdykt na górze (jak #43) — pierwsza rzecz, którą widać.
69. **[P1]** Panel „lejek wejść" (#7) — czemu nie handluje, czarno na białym.
70. **[P1]** Wykres equity vs BTC vs DCA.
71. **[P2]** Kafelki „% czasu w rynku" i „dni od ostatniego wejścia".
72. **[P2]** Napraw rozjazd listy pozycji (zgłoszony) + audyt responsywności paneli (Playwright 360/768/1280).
73. **[P2]** Tryb „prosty" vs „ekspert": domyślnie 5 liczb, reszta pod rozwinięciem.
74. **[P3]** Spójna typografia kwot (monospace, bez łamania — zrobione dla metryk, rozciągnij na całość).

## M. Alarmy / powiadomienia
75. **[P1]** Push dla STANÓW, nie tylko trejdów: bezczynność, paraliż, rozjazd ksiąg, shadow-budżet, martwy silnik.
76. **[P2]** Dzienny digest push (1 wiadomość): żyje / zarabia vs BTC / co wymaga decyzji.
77. **[P2]** Alarm „drawdown > próg" na żywym koncie (nie tylko twardy halt).
78. **[P3]** Alarm „BTC odzyskał 100d SMA" → bot zaraz zacznie handlować (uprzedzenie właściciela).

## N. Architektura / kod / dług
79. **[P2]** Rozbij `trading_engine.py` (monolit) na moduły: entries / exits / gates / execution.
80. **[P1]** `GatePipeline` jako lista obiektów-bramek (nazwa + metryka) zamiast rozsianych ifów — zasila #6/#7.
81. **[P2]** Typy domenowe (Position/Candidate/Signal) zamiast dictów `market_data` — koniec cichych błędów kluczy.
82. **[P3]** Usuń martwy kod (akcje/extended, jeśli porzucone) — mniej powierzchni.
83. **[P2]** Czyste interfejsy `strategy` i `risk` (testowalne osobno).

## O. Konfiguracja / knoby (277, w tym 83 krypto)
84. **[P1]** Audyt wszystkich knobów: oznacz fizyka/strategia/martwy; usuń martwe.
85. **[P1]** Walidacja configu na starcie: niespójne kombinacje (np. wszystkie bramki on) → ostrzeżenie w logu/UI.
86. **[P2]** „Profile strategii" jako presety (konserwatywny/agresywny/baseline-BTC) zamiast grzebania w 83 knobach.
87. **[P3]** Każdy knob w UI z tooltipem „co robi + default + czy udowodnione walk-forward".
88. **[P2]** Snapshot aktywnego configu do audit-log przy każdej zmianie (kto/co/kiedy).

## P. Bezpieczeństwo / reconciliation / dane
89. **[P1]** Rekoncyliacja prewencyjna (sprawdzaj przed zleceniem) — nie tylko watchdog po cyklu.
90. **[P2]** Potwierdź działanie backupu DB (knob jest) + przetestuj RESTORE.
91. **[P3]** Rotacja/retencja snapshotów audytu (branch `audit-snapshots` rośnie bez końca).
92. **[P2]** Rozszerz skan sekretów (gitleaks) o logi/artefakty, nie tylko kod.
93. **[P3]** Zawęź zakres / rotuj read-only token audytu.

## Q. Testy / CI / jakość
94. **[P1]** Test „strategia w ogóle handluje": syntetyczna hossa BTC → silnik MUSI zrobić ≥1 wejście. **Złapałby dzisiejszy paraliż w CI.**
95. **[P1]** Snapshot-test honesty: 0 trejdów → `status=idle`, nie alfa.
96. **[P2]** Property-based testy egzekucji (ilości/precyzja/min-notional) — patrz #27.
97. **[P2]** Coverage na ścieżce wejść/wyjść (najważniejsza, najmniej testowana).
98. **[P3]** Test integracyjny pełnego cyklu per venue (jest dla krypto — rozszerz na przyszły Kraken).

## R. Proces / go-live
99. **[P1]** „Runbook go-live": checklista (kryteria spełnione, mikro-kwota $50, limity, rollback) PRZED realnym kapitałem.
100. **[P1]** Pierwszy krok nad wszystkim: **jeden decydujący eksperyment baseline (BTC-200d vs obecny silnik)** — jego wynik rozstrzyga kierunek całej reszty tej listy.

---

## Sekwencja, gdybym miał ją narzucić (nie rozpraszać się na 100 naraz)

1. **Najpierw prawda (P1, 1–2 dni):** #6/#7 lejek wejść, #38 honesty-idle, #43/#68 baner-werdykt, #94 test paraliżu. → Przestajemy zgadywać, czemu nie handluje.
2. **Potem rozstrzygnięcie (P1, 2–3 dni):** #14/#100 baseline BTC-200d + #60/#62 benchmark i „trejdów/mies." w backteście. → Wiemy, czy złożoność ma sens.
3. **Potem cięcie albo tuning (P1/P2):** #13 ablacja bramek, #84 audyt knobów, #8 benchmark-fallback. → Albo upraszczamy do działającego rdzenia, albo świadomie luzujemy, by handlował.
4. **Reszta** to higiena (egzekucja, dane, UX, dług) — ważna, ale dopiero gdy rdzeń ma sens.

**Zasada nadrzędna:** dopóki #100 nie da odpowiedzi, nie dokładamy funkcji — tylko mierzymy uczciwie i rozstrzygamy premisę.
