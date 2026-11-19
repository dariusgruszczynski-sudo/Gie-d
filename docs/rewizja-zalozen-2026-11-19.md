# GielDarek — rewizja założeń od zera + 50 wniosków (2026-11-19)

> Zlecenie właściciela: „apka w ogóle nie handluje — przemyśl założenia i funkcje
> od podstaw, na każdym kroku kwestionuj sens, przygotuj 50 wniosków do poprawy."
> Buduje na `meta-analiza-2026-11.md` (13 warstw), ale z NOWYM, twardym dowodem.

## 0. Jedno zdanie prawdy (aktualizacja)

**Zbudowaliśmy maszynę, która najpierw robiła ZA DUŻO złych rzeczy (blowout −39%),
a po załataniu wpadła w drugie ekstremum: nie robi NIC — tydzień+ zera wejść przy
24/7 i pełnej gotówce.** Oba stany to ten sam korzeń: **brak jednej, spójnej tezy,
zastąpiony 277 knobami i 22 bramkami, które razem albo puszczają wszystko, albo nic.**
„+16% vs BTC" przy zerze transakcji to nie sukces — to artefakt: siedzenie w gotówce,
gdy BTC spada. Każdy stop na zwykłym holdzie robi to taniej i bez 83 krypto-knobów.

## 1. Centralna sprzeczność

- **Rozrzutność → paraliż, ten sam defekt.** Dokładaliśmy bramki po blowoucie. Teraz
  6–7 z nich działa naraz przez AND (HTF regime ∧ BTC-core ∧ MTF 4h ∧ konfluencja≥2 ∧
  ADX≥20 ∧ płynność ∧ cap). Mnożąc prawdopodobieństwa przejścia, wynik to ~0 wejść.
- **Filtr HTF (BTC < 100d SMA = blok wszystkiego)** znaczy dosłownie: „handluj longami
  tylko w hossie BTC". To nie alfa — to **beta na BTC z opóźnieniem**. W bessie = gotówka.
- **Pętla uczenia jest martwa z definicji:** R30/krzywa uczenia wymaga ≥50 zamknięć;
  przy 0 wejść nigdy ich nie uzbiera. Reguła „nie tuninguj na <50 trejdów" + „0 trejdów"
  = trwały impas: nigdy nie będzie danych do decyzji.
- **Budujemy piętra bez fundamentu:** dodaliśmy R-multiple, shadow, feature store —
  a rdzeń („czy to w ogóle handluje i bije BTC?") pozostaje nierozwiązany.

---

## 2. Rozbiór warstwa po warstwie — na każdym kroku: „po co to jest?"

**Premisa.** Czy aktywny trading krypto bije hold BTC po koszcie i ryzyku? Własne
dokumenty mówią: akcje — edge nieodróżnialny od szumu; krypto — news/LLM bez
powtarzalnej przewagi. Nie mamy dowodu na TAK. Brak dowodu = to projekt inżynierski,
nie maszyna do zarabiania. To trzeba przyznać, bo determinuje wszystkie inne decyzje.

**Sygnał.** SMA+MACD+RSI to trzy widoki tej samej ceny — skorelowane, nie niezależne
„potwierdzenia". „Konfluencja ≥2/3" na skorelowanych sygnałach to iluzja pewności.
Trzy nakładające się filtry trendu BTC (HTF regime, BTC-core, MTF confirm) mierzą
w kółko to samo.

**Ryzyko.** Dobre po blowoucie (anty-lewar, cap 20%, płynność). Ale 5 nakładających
się wyjść (stop vol-skalowany, trend-exit, trailing, time-exit, partial) — nie wiadomo,
które realnie dodaje, bo nikt nie zrobił ablacji. Korelacja altów do BTC ~0.8: „5 pozycji"
to jeden zakład na BTC, nie dywersyfikacja.

**Pomiar.** Scorecard od epoki — dobre. Ale `mark-epoch` może stać się ucieczką od złych
danych. „Bije BTC" przy 0 trejdów to kłamstwo benchmarku. Brak metryki „% czasu w rynku",
która jest tu NAJWAŻNIEJSZA (100% w gotówce).

**Egzekucja / venue.** Alpaca paper ≠ realny rynek (brak order booka, poślizgu, fundingu).
Edge z paper może zniknąć na żywo. Skaner odrzuca 16/36 par jako niepłynne — strukturalne
ograniczenie cienkiego venue, nie bug. Bug float-ULP (403) pokazał kruchość warstwy zleceń.

---

## 3. 50 wniosków do poprawy (priorytet: P1 krytyczny · P2 ważny · P3 porządkowy)

### A. Premisa / po co to w ogóle istnieje
1. **[P1]** Zdefiniuj JEDNĄ, mierzalną funkcję celu (np. „bić BTC o ≥X% rocznie przy DD≤Y%"). Dziś „sukces" jest płynny, więc wszystko można nazwać sukcesem.
2. **[P1]** Ustal twardy baseline = DCA/hold BTC. Zapisz **kill-criterion**: jeśli po oknie bot nie bije tego po koszcie i ryzyku — kasujemy aktywny trading.
3. **[P1]** Rozstrzygnij: to ma ZARABIAĆ czy UCZYĆ/walidować? Dziś miesza oba i nie robi żadnego dobrze. Dwie różne odpowiedzi = dwie różne apki.
4. **[P2]** Rozważ, że najlepszą wersją może być NIE-trading-bot: monitor + alarmy + regułowe DCA BTC/ETH z trailing na całości. Prostsze, audytowalne, prawdopodobnie lepsze.
5. **[P1]** Napisz „anty-tezę": co MUSIAŁOBY być prawdą, żeby aktywny trading bił hold. Jeśli nie da się tego obronić danymi — to hobby, nie edge (i to jest OK, ale nazwij to).

### B. Problem „nie handluje" (paraliż) — najpilniejsze
6. **[P1]** Policz, ile bramek działa naraz. 6–7 filtrów przez AND = matematycznie ~0 wejść. Zrób ablację: wyłączaj po jednej i patrz na liczbę wejść w walk-forward.
7. **[P1]** Nazwij filtr HTF wprost: „long tylko w hossie BTC" = beta, nie alfa. Albo usuń, albo świadomie zaakceptuj, że to jest cała strategia (i wtedy po co reszta?).
8. **[P1]** Dodaj metrykę **fill-rate**: ile cykli CHCIAŁO wejść vs ile weszło. Bez niej nie wiesz, że bot jest sparaliżowany, aż właściciel krzyknie „bez jaj".
9. **[P1]** Alarm push, gdy 0 wejść przez N dni przy wolnej gotówce — to stan AWARYJNY, nie „spokój".
10. **[P1]** W risk-on, gdy nic nie spełnia konfluencji: domyślnie **trzymaj BTC** (benchmark), nie gotówkę. Bezczynna gotówka w hossie to gwarantowana strata do benchmarku.
11. **[P2]** Rozdziel „nie wchodzę, bo bessa" (OK) od „nie wchodzę, bo 7 bramek" (bug produktu). Dziś wygląda tak samo: puste konto.
12. **[P2]** Ustal MINIMALNĄ aktywność jako sanity-check: jeśli przez miesiąc 0 trejdów, strategia jest z definicji nietestowalna — trzeba poluzować, by zbierać dane, albo przyznać porażkę.

### C. Złożoność — 277 knobów (83 krypto) to przeuczenie, nie strategia
13. **[P1]** 277 knobów = 277 stopni swobody dopasowanych do przeszłości. To nie elastyczność, to maszyna do przeuczenia. Tnij agresywnie.
14. **[P1]** Skonsoliduj 22 bramki/heurystyki w JEDEN model pozycji (vol-target + trend). To był R18 z roadmapy — nigdy nie zrobiony, bo wygodniej dodać 16. knob niż usunąć 15.
15. **[P2]** Usuń każdy knob, którego nikt nigdy nie zmienił od defaultu (Opus-overrides były puste → sygnał, że większość knobów to teatr).
16. **[P2]** Reguła twarda: **nowy knob tylko, gdy usuwa inny.** Budżet złożoności stały.
17. **[P2]** Każdy knob musi mieć uzasadnienie walk-forward albo leci. „Dodane, bo brzmiało mądrze" = dług.
18. **[P3]** Oddziel knoby „fizyki" (precyzja, limity giełdy) od knobów „strategii". Pierwsze zostają, drugie idą pod nóż.

### D. Sygnał / strategia
19. **[P1]** Zrób **test ablacyjny** każdej bramki osobno na walk-forward. Prawie na pewno większość to szum albo szkoda. Zostaw tylko te z udowodnionym dodatnim wkładem.
20. **[P2]** Konfluencja SMA/MACD/RSI: to jeden sygnał w trzech przebraniach. Zastąp jednym czystym (np. trend + jego siła), nie „głosowaniem" skorelowanych.
21. **[P1]** Timeframe jest niespójny z tezą: `krypto-strategia.md` mówi „MNIEJ, dłuższych, wyższej konwikcji", a silnik pollinguje co 30 min i ma mikro-wyjścia. Trend-following żyje na dniach/tygodniach. Dopasuj poll i horyzont do tezy.
22. **[P2]** Zredukuj 3 filtry trendu BTC (HTF/BTC-core/MTF) do jednego. Trzy pomiary tego samego to nie potrójna pewność, to potrójna blokada.
23. **[P3]** Jeśli zostaje breakout — udowodnij, że bije sam trend. Inaczej kasuj.

### E. Ryzyko
24. **[P2]** Zrób ablację 5 mechanizmów wyjścia. Zostaw 1–2 z realnym wkładem; reszta to złożoność bez dowodu.
25. **[P1]** Mierz ryzyko PORTFELA, nie per-trade: przy korelacji altów do BTC ~0.8, „5 pozycji" to jeden lewarowany zakład na BTC. Cap na łączną beta-do-BTC, nie na liczbę pozycji.
26. **[P2]** Trzymaj R-multiple (R30) jako jedyną miarę ryzyka — i wymuś, by KAŻDE wejście miało zdefiniowane R przed zleceniem.
27. **[P3]** Stop vol-skalowany 4–18% na krypto bywa tak szeroki, że „ochrona" jest iluzoryczna przy dużej pozycji. Sprawdź realną stratę w $ przy maks. stopie.

### F. Pomiar / uczciwość (UI nie może kłamać)
28. **[P1]** Przy 0 wejść honesty MA pokazywać „n/d — nie handluje", a NIE „+16% alfa". Zielony wynik bez trejdów to kłamstwo, które usypia czujność.
29. **[P1]** Dodaj **„% czasu w rynku"** jako metrykę pierwszej linii. 100% w gotówce to najważniejsza prawda o tym bocie dziś.
30. **[P2]** Benchmark = „kapitał w BTC wg własnego reżimu ryzyka", nie naiwny hold. Uczciwe porównanie jabłek do jabłek.
31. **[P1]** Reguła na `mark-epoch`: epokę zmienia się TYLKO przy zmianie strategii, NIGDY po złym wyniku. Inaczej scorecard staje się narzędziem do ukrywania porażek.
32. **[P2]** Jeden wielki werdykt na górze dashboardu: „ZARABIA / NIE / BEZCZYNNY od X dni vs BTC Y%". Reszta metryk pod spodem.

### G. LLM / shadow
33. **[P1]** Shadow (teraz on) to jedyny uczciwy test LLM — dobrze. Ale ustal PRÓG i DATĘ: jeśli po oknie BUY-e Claude nie biją jego HOLD-ów, **skasuj warstwę LLM całkowicie**, nie „zostaw na potem".
34. **[P2]** Koszt LLM licz jako % zysku, nie absolutnie. $9/mies. na koncie, które nie zarabia, to nieskończony % kosztu.
35. **[P3]** LLM analizuje te same dane co mechanika — „edge LLM" to hipoteza, którą własne docs podważyły (news w cenie w sekundy). Nie buduj na niej nic, dopóki shadow nie udowodni.

### H. Venue / egzekucja / dane
36. **[P1]** Paper Alpaca ≠ realny rynek (brak order booka, poślizgu, fundingu). Każdy „edge" z paper traktuj jako NIEPOTWIERDZONY, dopóki nie przejdzie na realnej księdze.
37. **[P2]** Jedyny uczciwy test egzekucji to realny Kraken (legalny PL) z mikro-kwotą ~$50. Brak tam paper — więc albo mikro-real, albo nigdy nie wiesz.
38. **[P1]** Handluj TYLKO głęboko płynne (BTC/ETH, może kilka), nie alty na cienkim venue. Skaner odrzuca 16/36 jako niepłynne — to strukturalne, powtórka HYPE czeka w altach.
39. **[P2]** Warstwa „broker adapter" z twardą normalizacją ilości/precyzji per-giełda (lekcja z float-ULP 403). Jedno miejsce, testy graniczne.
40. **[P3]** Feedy danych: potwierdź, że OHLC/wolumen z Alpaki są wiarygodne dla altów (cienka płynność = śmieciowe świece = śmieciowe sygnały).

### I. UX / produkt (jeden właściciel, nie terminal Bloomberga)
41. **[P1]** UI MUSI krzyczeć, gdy bot bezczynny: „BEZCZYNNY 7 dni — 0 wejść" na górze, zamiast zielonego +16%. Zaufanie właściciela > ładne liczby.
42. **[P2]** Mniej zakładek, mniej metryk. Właściciel chce wiedzieć trzy rzeczy: czy żyje, czy zarabia vs BTC, czy coś wymaga decyzji.
43. **[P2]** Alarmy push dla stanów, nie tylko trejdów: bezczynność, paraliż bramek, shadow-budżet, rozjazd ksiąg.
44. **[P3]** Dokończ UX listy pozycji (zgłoszony rozjazd) — ale dopiero po stabilizacji rdzenia; kosmetyka nie naprawi braku handlu.

### J. Proces / meta (jak podejmujemy decyzje)
45. **[P1]** Zrób JEDEN decydujący eksperyment: najprostszy możliwy bot (kup BTC gdy cena > 200d SMA, sprzedaj gdy poniżej — nic więcej) na tych samych danych. Jeśli bije obecny silnik, **cała złożoność ma ujemną wartość.**
46. **[P1]** Ustal DATĘ decyzji: „do [data] bot ma ≥N zamknięć i wynik vs BTC, albo tniemy aktywny trading do regułowego DCA." Bez daty impas trwa w nieskończoność.
47. **[P2]** Każda zmiana strategii = zapisana HIPOTEZA + test jej obalenia PRZED wdrożeniem, nie po. Koniec z „dodajmy i zobaczmy".
48. **[P1]** STOP dokładania funkcji, dopóki rdzeń nie rozwiązany. Zamrożenie nowych feature'ów; tylko: uprość, zmierz uczciwie, rozstrzygnij premisę.
49. **[P2]** Koszt alternatywny jawnie: czas w 277 knobów vs po prostu trzymanie BTC. Jeśli bot = „unikanie rynku w bessie", to stop-loss na holdzie robi to taniej.
50. **[P1]** Pytanie ostateczne, uczciwie: **budujesz to, bo ma zarabiać, czy bo to ciekawy projekt?** Obie odpowiedzi OK — ale apka dziś UDAJE pierwsze, a jest drugim. Wybór determinuje wszystko powyżej.

---

## 4. Gdybym miał zrobić 3 rzeczy jutro (bez czekania na resztę)

1. **Uczciwy pomiar (P1, bezpieczne, dziś):** honesty nie kłamie przy 0 trejdów + metryka „% czasu w rynku" + alarm bezczynności. Żeby UI przestało usypiać.
2. **Najprostszy baseline (P1, rozstrzygający):** zakoduj bota „BTC vs 200d SMA, nic więcej", puść walk-forward na tych samych danych. Jeśli bije obecny silnik — mamy odpowiedź i kierunek: tnij.
3. **Decyzja premisy (P1, Twoja):** zarabiać czy projekt? + kill-criterion + data decyzji. Bez tego każdy kolejny tydzień to ten sam raport „bez zmian".

## 5. Brutalnie, jedno zdanie na koniec

Ta apka nie ma dziś problemu technicznego — ma problem **egzystencjalny**: jest
świetnie zbudowanym narzędziem bez udowodnionej racji bytu, które właśnie
zademonstrowało, że w obecnej formie albo wybucha, albo stoi. Najwartościowszym
ruchem może być **radykalne uproszczenie do czegoś, co da się obronić danymi** —
nawet jeśli to „regułowe DCA w BTC", a nie autonomiczny trader z przewagą LLM.
