# GielDarek krypto — roadmapa docelowa (jedna lista)

Cel: aplikacja monitorująca CAŁY rynek krypto na Alpace, łącząca przewagę algo +
LLM do maksymalizacji zysku, z realną **krzywą uczenia** (rośnie skuteczność w
czasie). Lista „czego brakuje do ideału" + 5 ekstra + 10 UX. Priorytety:
🔴 fundament · 🟠 podnosi sufit · 🟡 dług/higiena.

## A. Fundament pętli uczenia (bez tego nie ma „krzywej uczenia")
1. 🔴 **Feature store** — każda decyzja zapisuje PEŁNY wektor cech, który widziała (wszystkie wskaźniki, reżim, funding, kontekst), wersjonowany.
2. 🔴 **Etykietowanie wyników** — każdy zamknięty trejd dostaje wynik w R, trwale przypięty do cech z decyzji wejścia.
3. 🔴 **Atrybucja edge per-setup/cecha** — które sygnały/filtry realnie przewidują wygrane, a które dodają szum (dziś ~15 bramek „na wiarę").
4. 🔴 **Automatyczna adaptacja walidowana OOS** — przeważanie setupów z danych, promowane dopiero po walk-forward, nie ręcznym strojeniem knobów.
5. 🔴 **Harness eksperymentów / shadow (A-B)** — kandydaci-strategie biegną „na sucho" obok żywego; promujemy tylko zwycięzców OOS.

## B. Percepcja / sygnały (widzieć rynek lepiej)
6. 🟠 **Funding/OI per-moneta** (dziś tylko BTC) — kontekst pozycjonowania dla każdej pary.
7. 🟠 **Order-book / mikrostruktura + realny wolumen** — głębokość, spread, presja po stronie bid/ask.
8. 🟠 **Feed cross-exchange do SYGNAŁU** (np. z dużej giełdy) — bogatsze dane cenowo-wolumenowe, nawet gdy egzekucja zostaje na Alpace (obchodzi cienkość venue).
9. 🟡 **On-chain / sentyment / narracje** — wejścia, których liczby nie łapią (dla warstwy LLM).

## C. LLM jako realny silnik (nie uśpione weto)
10. 🟠 **Synteza nieustrukturyzowanego** — LLM czyta newsy/narracje/kontekst jako CZYNNIK zysku, nie tylko heartbeat co 8h.
11. 🔴 **Meta-rozumowanie LLM nad własnym track-rekordem** — proponuje korekty na podstawie atrybucji (pkt 3), ale PROPONUJE; wdrożenie dopiero po walidacji.
12. 🟠 **Teza per-trejd w feature store** — mamy string tezy; dopiąć go do cech + wyniku (surowiec do uczenia i post-mortemów).

## D. Egzekucja (cienki rynek Alpaki)
13. 🟠 **Model poślizgu/fill** — backtest i sizing uwzględniają, że WŁASNE zlecenie rusza płytką książkę.
14. 🟡 **Typy zleceń / sizing wg głębokości** — nie wrzucać na raz więcej, niż książka uniesie.

## E. Pomiar / uczciwość (czy w ogóle się uczymy?)
15. 🔴 **KPI „krzywa uczenia"** — krocząca expectancy/trafność cohort-po-cohort; jedna liczba pokazująca trend skuteczności.
16. 🔴 **Czysty baseline pomiaru** — rozwiązać problem pozycji straddlujących blowout (liczyć od pierwszego w pełni czystego wejścia albo reset historii).
17. 🟠 **Scorecard krypto w audit-snapshot** — publikować epoch-aware scorecard, żeby nadzór git-first widział czystą liczbę (dziś liczy z surowego logu, dziedziczy skażenie).
18. 🟡 **True-ATR (high/low)** zamiast vol z samych close — tylko jeśli atrybucja pokaże, że warto.

## F. Ryzyko (spójny model zamiast zupy knobów)
19. 🟠 **Portfelowy vol-targeting** — jeden model docelowej zmienności portfela zamiast ~15 nakładających się heurystyk.
20. 🟡 **Zamrożenie i przegląd 273 knobów** — wyłączyć niewalidowane bramki (mniej kodu = mniej miejsc na bug).

## G. Architektura / dług
21. 🟡 **Dokończyć rozbicie `run_cycle`** (pętla decyzji + auto-deploy).
22. 🟡 **Deduplikacja fetchy** — tylko po przeprojektowaniu kolejności (teraz net ujemny przez ścieżkę halt).
23. 🟡 **Pipeline warstwowy** zamiast monolitu heurystyk (Data → Feature store → Model → Decyzja → Egzekucja → Wynik → Uczenie).

## +5 EKSTRA (nowe, w tym duchu)
24. 🔴 **Watchdog rekoncyliacji** — ciągłe porównanie stanu broker vs wewnętrzny (pozycje/gotówka), auto-halt przy rozjeździe. Blowout był awarią rekoncyliacji — to by go złapało.
25. 🔴 **Portfelowy kill-switch** — jeden tripwire „coś jest nie tak → spłaszcz i alarmuj", ponad obecne halty progowe.
26. 🟠 **Przełącznik reżimowy strategii** — w risk-off trzymaj BTC/gotówkę, rotuj alty tylko w potwierdzonym up-reżimie (altseason-gate padł → potrzebny LEPSZY sygnał, nie trailing).
27. 🟠 **LLM post-mortem per zamknięty trejd** — krótkie „czemu wygrał/przegrał", tagowane → zasila atrybucję i czytelną naukę.
28. 🔴 **Walk-forward jako bramka CI** — każda zmiana strategii/configu MUSI przejść OOS walk-forward przed deployem (instytucjonalizacja dyscypliny, koniec zygzaków).

## +10 UX (w duchu: uczciwość, widoczność nauki, kontrola)
29. 🟠 **Panel „Krzywa uczenia"** — expectancy/trafność w czasie; widać, czy bot się poprawia.
30. 🟠 **„Dlaczego nie kupuje" na żywo** — która bramka blokuje wejścia TERAZ (reżim/chop/cooldown); zamienia „stoi bezczynnie" w zrozumiałe.
31. 🟠 **Żywy widok skanera** — co bot widzi teraz: uniwersum, score, powód wejścia/odrzucenia per moneta (rozszerzyć Monety o skip-reasons).
32. 🟡 **Przełącznik „obecna strategia vs życiowe"** w Werdykcie/Monetach — od epoki vs od początku (jawna uczciwość).
33. 🟠 **Karta trejdu: teza → wynik → czy teza się sprawdziła** — pełnoprawny widok (mamy kawałki, scalić).
34. 🟠 **Dashboard eksperymentów** — shadow-strategie vs żywa, obok siebie.
35. 🟠 **Kokpit ryzyka** — ekspozycja, mapa korelacji, drawdown, jak blisko każdego progu haltu.
36. 🟡 **Push/alerty o zdarzeniach** — nowe wejście + teza, stop, zmiana reżimu, halt (proaktywnie, nie trzeba patrzeć).
37. 🟡 **Widok atrybucji** — które sygnały teraz zarabiają, które krwawią (z silnika z pkt 3).
38. 🔴 **Nagłówek-uczciwość (zawsze widoczny)** — „bijemy BTC? tak/nie · na ilu trejdach · od kiedy" — jedna prawda na wierzchu.

---

## Kolejność budowy (fundament najpierw)
1. **Czysty baseline (16) + feature store (1) + etykiety wyników (2)** — bez tego reszta uczy się szumu.
2. **Watchdog rekoncyliacji (24) + kill-switch (25) + walk-forward jako bramka CI (28)** — żeby nigdy więcej blowoutu i zygzaków.
3. **Atrybucja (3) + KPI krzywej uczenia (15, 29)** — zacząć MIERZYĆ naukę.
4. **Bogatsze sygnały (6-8) + LLM synteza/meta (10-11)** — podnosić sufit, gdy fundament stoi.
5. **Automatyczna adaptacja OOS (4) + shadow (5, 34)** — dopiero na końcu, na sprawdzonym fundamencie.

Zasada nadrzędna: **najpierw mierz uczciwie, potem optymalizuj; nigdy nie strój na próbce < ~50 trejdów / < 3 tyg.**
