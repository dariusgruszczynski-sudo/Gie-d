# Audyt kodu GielDarek — użyteczność, czyszczenie, poprawa

Data: 2026-10-24. Zakres: `backend/app` (~14.8k linii). Metoda: audyt
**strukturalny + weryfikacja konkretów** (odwołania, martwy kod, duplikaty,
ryzyka, złożoność) — nie literalne „linijka po linijce" (dla 14.8k linii nie
dałoby wartości; grepy trzeba *czytać* — o mały włos nie skasowałem żywego
`defensive_symbols`, które działa przez property `defensive_symbol_list`).

## Zrobione
- ✅ Usunięte martwe pole configu `extended_regime_benchmark` (0 odwołań).
- ✅ Wydzielone z molocha `run_cycle` (zero zmiany zachowania, +testy):
  `_build_market_data()`, `_assemble_headlines()`, `_reconcile_account_total()`.
  Ciało `run_cycle` ~50 linii mniej; czyste, testowalne seamy.
- ✅ Logowanie dla cichych `except` w ścieżce ryzyka (`_crypto_loss_streak_today`,
  `_yesterday_realized_usd`) — cichy błąd odczytu P&L maskował breaker #5 i
  cool-off #14.

## Przeanalizowane i ŚWIADOMIE NIEzrobione (z uzasadnieniem)
- **Deduplikacja fetchy (#2 niżej) — NIE opłaca się jako prosty refaktor.** Żeby
  wyjścia współdzieliły serię z `_build_market_data`, trzeba zbudować market_data
  PRZED wyjściami. Ale wyjścia (i cały cykl) zwracają wcześnie przy halcie/zamkniętym
  rynku — więc przesunięcie budowy market_data w górę pobierałoby ~20 serii świec
  na KAŻDYM pollu w halcie/poza sesją (teraz: 0). To zamiana oszczędności na
  aktywnej ścieżce za MARNOTRAWSTWO na częstej ścieżce halt/zamknięte. Net ujemny
  na paper. Zostawić, chyba że cykl przestanie wcześnie wychodzić.
- **Cięcie warstwy LLM (#3) — decyzja KIERUNKOWA, nie mechaniczna.** ~1035 linii
  jest ŻYWYCH dla nogi akcji (`crypto_llm_enabled=False` dotyczy tylko krypto) i
  dla heartbeatu krypto. Usunięcie to utrata zdolności, nie sprzątanie — wymaga
  decyzji „czy akcje/krypto zostają z LLM, czy nie". Nie ruszać bez tej decyzji.

## 🧹 Do czyszczenia (pozostałe)
- **~29 cichych połknięć wyjątków** (`except Exception → pass/continue/return`
  bez logu), z 152 bloków `except` w `app`. Wzorzec „best-effort, nie wywalaj
  cyklu" jest OK, ale ciche połknięcia ukrywają błędy. Rekomendacja: każdy
  `except` w ścieżce handlu loguje `warning(exc_info=True)`.
- **Altseason-gate** (Tor 2) — odrzucony backtestem, zostaje jako udokumentowany
  negatywny wynik, domyślnie OFF, tylko backtest. Świadomie, nie bałagan.
- Config (273 pola) — **nie martwy**, ale rozrośnięty (patrz niżej).

## 🔧 Do poprawy (rankowane wg wartości)
1. **`run_cycle` wciąż ~420 linii** (+ `_process_decision` 303,
   `check_take_profit_stop_loss` 273). Dalej rozbić na testowalne kroki
   (`_run_exits`, `_run_entries`, `_persist_decision`). Największy dług
   strukturalny repo. (Zaczęte: `_build_market_data` wyjęte.)
2. **Wielokrotny fetch tej samej historii per moneta/cykl** — 7 miejsc
   `get_klines` w silniku (wyjścia 1h, market_data 1h znów, MTF 4h, skaner 1d).
   Dla ~20 monet × cykl to redundancja API (kumuluje się ze skanerem). Pobrać raz
   per symbol/cykl i współdzielić. Uwaga: wyjścia biegną PRZED budową market_data,
   więc dedup wymaga przestawienia kolejności — robić ostrożnie.
3. **Rozrost knobów (273 pola, ~15 nakładających się bramek wejścia).**
   Walk-forward pokazał brak spójnej przewagi zwrotu — złożoność wyprzedza dowód.
   Rekomendacja: ZAMROZIĆ dokładanie; po zebraniu żywej próbki rozważyć
   WYŁĄCZENIE najsłabszych bramek (mniej kodu = mniej miejsc na bug).

## 🎯 Użyteczność — co służy celowi (nauka + zarabianie)
- **Wysoka wartość, zostaje:** rdzeń (skaner → bramki → wyjścia → sizing),
  obserwowalność skanera, backtest + walk-forward. To oczy i miara.
- **Kandydat do odchudzenia:** warstwa LLM — `claude_advisor` (467) +
  `opus_controller` (262) + `self_review` (176) + `shadow_analysis` (130) ≈
  **1035 linii** przy `crypto_llm_enabled=False`. W krypto uśpiona (żyje heartbeat
  co 8h + stosowanie knob-overrides). Jeśli krypto zostaje mechaniczne i $0-LLM,
  ta warstwa nie zarabia na swoją złożoność — rozważyć cięcie.

## Werdykt
Kod jest **czystszy, niż się obawialiśmy** (mało realnej martwoty). Dwa realne
problemy: **moloch `run_cycle`** (dług strukturalny) i **systemowy rozrost
knobów** (nieprzełożony na przewagę). Największy ruch inżynierski: dalej rozbijać
`run_cycle` + zdeduplikować fetche. Największy ruch strategiczny: **przestać
dodawać, zacząć odejmować** — po danych z żywej próbki.
