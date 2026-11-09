# GielDarek — meta-analiza od pierwszych zasad (2026-11-09)

> Zamówienie właściciela: „Na Alpace na realną kasę wychodziłeś na zero, krypto 24/7
> to katastrofa. Pełna, dogłębna analiza od filozofii, analiza WSZYSTKIEGO co
> wdrożono i skasowano, meta-analiza narzędzia (przewaga LLM + 24/7 autonadzór).
> Aplikacja ma działać jak zamierzyłem. Super-detalicznie, warstwa po warstwie,
> kilkadziesiąt rekomendacji."
>
> Bez lukru, w %. To papier (krypto) i była realna, ale mała kasa (akcje).

---

## 0. Jedno zdanie prawdy

**Zbudowaliśmy technicznie dobrą maszynę, która robi DOKŁADNIE ODWROTNIE niż mówią
jej własne, udokumentowane wnioski strategiczne — i dlatego przegrywa.** Akcje:
cienka przewaga nie do odróżnienia od szumu → realnie zero. Krypto: wdrożyliśmy
LLM-wetowane, częste wejścia, rotację niepłynnych altów na mikro-giełdzie — czyli
cztery rzeczy, które nasze własne dokumenty nazwały „brak przewagi / koszt zabija
edge / cienki venue" → **−39% od szczytu**. Problem nie jest w jakości kodu
(jest dobra). Problem jest w **premisie i w rozjeździe między tym, co wiemy, a tym,
co robimy.**

---

## 1. Filozofia: co chcieliśmy, co zbudowaliśmy, gdzie się rozjechało

**Zamierzenie (z `roadmap-krypto.md`):** aplikacja monitorująca CAŁY rynek krypto na
Alpace, łącząca przewagę **algo + LLM** do maksymalizacji zysku, z realną **krzywą
uczenia** (rośnie skuteczność w czasie).

**Co nasze WŁASNE dokumenty ustaliły jako prawdę (zanim cokolwiek poszło nie tak):**

| Źródło | Ustalenie |
|---|---|
| `krypto-strategia.md` | Przewaga w krypto = **trend-following / momentum** (mechaniczny, dekada walk-forward). „**MNIEJ, dłuższych, wyższej-konwikcji** pozycji." W risk-off **trzymaj BTC/gotówkę**. |
| `krypto-rebudowa.md` | „**Sentyment z newsów/LLM — brak powtarzalnej przewagi**; news jest w cenie w sekundy." |
| `zalozenia-analiza.md` | Akcje: edge +$0.17–0.46/trejd na ~30% trafności, ale „**cały wynik wisi na kilku wygranych**", „z +$17 na szczycie do **~$0 dziś**". „Maszyna na procenty, nie kwoty." „**To walidacja edge, nie dochód.**" |
| `audyt-strategii-2026-09.md` | „**Predykcje prawdopodobnie coś wnoszą, ale to HIPOTEZA, nie fakt.**" Najważniejsze do zrobienia: **test Claude vs mechanika** (shadow). „Główne ryzyko: że przewaga okaże się szumem." |

**Co faktycznie wdrożyliśmy w krypto (jesień):**

| Oś | Dokument mówił | Wdrożyliśmy | Skutek |
|---|---|---|---|
| Częstotliwość | mniej, dłużej | churn: dziesiątki wejść, poll 15–30 min, 24/7 | koszt (spread) zjada edge |
| Rola LLM | brak edge w newsach/sentymencie | LLM wetuje KAŻDE wejście | $24,5 kosztu + zatwierdził blowout |
| Dobór | trzymaj BTC, rotuj alty tylko w potwierdzonym up-reżimie | rotacja ~19 altów non-stop | przegrywa z trzymaniem BTC |
| Wielkość | wg głębokości książki | % konta, bez bramki płynności (do 10-27) | $232k w HYPE (100× obrotu) |
| Walidacja | udowodnij edge vs mechanika PRZED skalą | skalowaliśmy ($1M, max_concurrent 20, LLM) bez dowodu | −39% |

**Wniosek filozoficzny:** nie mamy problemu „brakuje nam funkcji". Mamy problem
**dyscypliny**: wiedza była, implementacja ją złamała. Każde „ulepszenie" (więcej
slotów, LLM on, szersze uniwersum) było ruchem W STRONĘ większego ryzyka bez
udowodnionej przewagi — czyli hazardem, nie inżynierią edge.

---

## 2. Werdykt z twardych danych (bez interpretacji)

- **Akcje (realna kasa, ~$600):** szczyt +$17 → ~$0. **Breakeven.** Edge statystycznie
  nieodróżnialny od szumu na ~45–54 zamknięciach. Test „Claude vs mechanika" **nigdy
  nie rozstrzygnięty** — czyli nie wiemy, czy LLM w ogóle coś dokładał.
- **Krypto (paper $1M):** → **$609k (−39% od szczytu)**. Realized życiowy **−$139k**.
  Trafność na surowym logu **0%** (zatruta bazą kosztową z blowoutu, ale kierunek:
  same straty). Tydzień blowoutu: realized **−$25 345**.
- **Walk-forward (nasz własny, #15/#28):** strategia **bije trzymanie BTC tylko w 1 z 4
  okien OOS**, mediana alfy **−21%**. Altseason-gate **pogorszył** wynik. To jest
  najtwardszy fakt: **nie ma udowodnionej przewagi nad `kup i trzymaj BTC`.**
- **Blowout HYPE (10-27):** $232k (27% konta) w jedną niepłynną monetę, 3 zlecenia/30 min,
  fille po zamrożonej cenie → rozjazd baza↔broker ~$226–366k, do dziś nierozwiązany.
- **Koszt LLM:** przebił budżet do **272%** zanim go wyłączyliśmy; brak dowodu, że
  dokładał wartość.

**Jedna liczba, która podsumowuje wszystko:** system, który po dziesiątkach transakcji
**przegrywa z `trzymaj BTC`**, nie ma edge. Reszta to szczegóły.

---

## 3. Analiza warstwa po warstwie

Dla każdej warstwy: **stan → co działa → co psuje → rekomendacje (R#)**.

### Warstwa 1 — Filozofia / funkcja celu
- **Stan:** cel = „maksymalizuj zysk". Benchmark (bić BTC) jest w kryteriach go-live, ale
  NIE jest funkcją celu silnika — silnik optymalizuje „wejdź, gdy momentum", nie „pobij BTC".
- **Co psuje:** „maksymalizuj zysk" bez udowodnionego edge = maksymalizuj wariancję =
  hazard. Brak funkcji celu relatywnej do benchmarku → silnik nie wie, że przegrywa z BTC.
- **R1.** Zmień funkcję celu z „zysk absolutny" na **„alfa vs trzymanie BTC po kosztach"**.
  Jeśli nie bijesz BTC — właściwą pozycją jest **trzymać BTC**, nie rotować alty.
- **R2.** Zasada nadrzędna w kodzie, nie tylko w docu: **żadnego skalowania (kapitał,
  sloty, LLM) dopóki alfa vs BTC nie jest dodatnia na ≥50 zamknięciach / ≥3 tyg.**
- **R3.** Zdefiniuj „sukces" jako **Calmar/drawdown-adjusted alfa**, nie goły zwrot —
  walk-forward pokazał, że jedyna realna zaleta systemu to niższy drawdown, nie zwrot.

### Warstwa 2 — Venue / rynek (EGZYSTENCJALNE)
- **Stan:** Alpaca crypto. BTC ~$170k obrotu/dzień, większość altów **$2–8k/dzień**.
  To **mikro-giełda**. Przy koncie $1M (a nawet $10k) JESTEŚMY rynkiem.
- **Co psuje:** nie da się prowadzić zdywersyfikowanej rotacji momentum na venue, gdzie
  jedno sensowne zlecenie = wielokrotność dziennego obrotu. Blowout HYPE to nie wypadek —
  to **nieunikniona konsekwencja** deployu realnego kapitału w tę płynność.
- **R4.** **Rozdziel SYGNAŁ od EGZEKUCJI** (roadmap #8): bierz dane cenowo-wolumenowe
  z dużej giełdy (Binance/Coinbase), egzekwuj na Alpace tylko to, co książka uniesie.
  Bez tego cały pomiar jest na danych z martwej książki.
- **R5.** **Twardy budżet płynności per moneta** = f(dzienny obrót). Już wdrożone jako
  bramka 8× — ale to łata. Docelowo: pozycja ≤ np. 1–2% dziennego obrotu, inaczej
  moneta wypada z grywalnego koszyka.
- **R6.** **Uczciwie: rozważ, czy Alpaca crypto to w ogóle właściwy venue.** Jeśli celem
  jest realna kasa, venue z głębokością (Coinbase/Kraken/Binance) zmienia WSZYSTKO.
  Alpaca była wyborem „bo mamy integrację akcji", nie „bo to dobry rynek krypto".

### Warstwa 3 — Dane / percepcja
- **Stan:** `market_scanner.py` (skan 36 par, momentum vs BTC, próg płynności), `news_client.py`
  (905 linii!), `crypto_market_structure.py`, `market_context.py` (fear&greed, funding BTC).
- **Co działa:** skaner po naprawie progu płynności realnie poszerza uniwersum (0→~19 par).
  Mapa `dollar_vol` (ta sesja) zasila bramkę płynności.
- **Co psuje:** (a) dane z cienkiej książki Alpaki = wyceny i momentum liczone na szumie;
  (b) **905 linii klienta newsów** przy udokumentowanym braku edge z newsów = dług, nie wartość;
  (c) funding/OI tylko dla BTC (roadmap #6), brak order-booka (#7).
- **R7.** Dane do sygnału z grubego venue (patrz R4). Alpaca tylko do egzekucji i sald.
- **R8.** News/sentyment: **wytnij albo zdegraduj** do warstwy kontekstu LLM (nie do sygnału
  wejścia) — dokument mówi wprost „brak powtarzalnej przewagi".
- **R9.** Dodaj realny wolumen/głębokość per moneta (#7) — bez tego sizing jest na ślepo.

### Warstwa 4 — Sygnał / strategia
- **Stan:** `signals.py`, `strategy_profiles.py`, `technical_indicators.py`, `adaptive_risk.py`.
  **273 knoby** konfiguracji, **~15 bramek wejścia „na wiarę"** (nie zwalidowanych atrybucją).
- **Co działa:** rdzeń trend-following jest zgodny z dowodami (momentum to realny edge krypto).
- **Co psuje:** (a) **~15 bramek, których nikt nie zmierzył** — część prawie na pewno dodaje
  szum (dokument akcji: „dodawanie filtrów wejścia POGARSZAŁO wynik"); (b) churn: strategia
  wchodzi/wychodzi na szumie, płacąc spread za każdym razem; (c) altseason-gate OBIEKTYWNIE
  pogorszył wynik (walk-forward) — czyli dokładaliśmy złożoność, która szkodzi.
- **R10.** **Atrybucja edge (roadmap #3) PRZED czymkolwiek innym:** która z 15 bramek realnie
  przewiduje wygrane. Wyłącz te, które nie (prawdopodobnie większość).
- **R11.** **Drastycznie mniej, dłuższych pozycji** — wróć do tezy „mniej/dłużej/wyższa
  konwikcja". Mniej transakcji = mniej spreadu = mniej szansy, że koszt zje edge.
- **R12.** **Rdzeń = BTC trend-following**, alty tylko jako „overlay" w potwierdzonym
  up-reżimie (roadmap #26), i tylko te płynne. Domyślna pozycja w niepewności = BTC/gotówka.
- **R13.** Każda bramka/knob bez dowodu atrybucji → **kandydat do usunięcia** (patrz W13).

### Warstwa 5 — LLM (serce „przewagi LLM")
- **Stan:** `claude_advisor.py` (Sonnet wetuje wejścia), `llm_meta.py` (meta-przegląd, proposes-only),
  `opus_controller.py` (262 linie, wyłączony), `budget_tracker.py`. LLM **wyłączony** tę sesję.
- **Co psuje — fundamentalne:** (a) **nie ma dowodu, że LLM > mechanika** — to był #1
  rekomendacja KAŻDEGO audytu i NIGDY nie rozstrzygnięty; (b) LLM wetował wejścia, czyli
  używaliśmy go tam, gdzie dokument mówi „brak edge" (news/sentyment w cenie w sekundy);
  (c) to LLM zatwierdził blowout HYPE; (d) przepalał budżet (272%) bez twardego hamulca.
- **Brutalnie:** „przewaga LLM" w handlu **nie została ani raz udowodniona** w tym projekcie.
  To hipoteza, która kosztuje i jak dotąd szkodzi.
- **R14.** **Rozstrzygnij test Claude-vs-mechanika (shadow, #5/#34) RAZ NA ZAWSZE** zanim LLM
  wróci do decyzji. Mechanika biegnie, shadow-LLM proponuje równolegle, porównujesz edge po
  ≥50 zamknięciach. **Dopóki LLM nie bije mechaniki — zostaje wyłączony.** (Teraz jest.)
- **R15.** Przenieś LLM tam, gdzie MOŻE mieć edge, nie tam, gdzie nie ma:
  **(a) post-mortem per trejd (#27)** — „czemu wygrał/przegrał" → zasila atrybucję;
  **(b) meta-rozumowanie nad track-rekordem (#11, proposes-only)**;
  **(c) synteza narracji jako KONTEKST, nie trigger wejścia.** Nie wetowanie co-cykl.
- **R16.** Jeśli LLM wraca do decyzji: **twardy hamulec budżetu** (`claude_pause_trading_at_budget=True`)
  — nie powtórka 272%.
- **R17.** Opus-controller (262 linie, od 09-11 nieużywany): **wytnij albo udowodnij** — dług.

### Warstwa 6 — Ryzyko
- **Stan:** `risk_manager.py` (409 linii): halty dzienny/tygodniowy/drawdown, kill-switch dźwigni,
  halt podwodny; ~15 nakładających się heurystyk sizingu (korelacja, cooloff, conviction, vol).
- **Co działa:** halty katastroficzne (30/40/55%) i kill-switch dźwigni istnieją i trzymają.
- **Co psuje:** (a) **„zupa knobów"** — ~15 heurystyk ryzyka, które się nakładają i nikt nie
  wie, która działa; (b) halty są PROGOWE (reagują po fakcie na % straty) — blowout HYPE
  przeszedł, bo był **awarią rekoncyliacji**, nie przekroczeniem progu; (c) brak jednego
  portfelowego modelu ryzyka.
- **R18.** **Portfelowy vol-targeting (#19):** jeden model docelowej zmienności portfela
  zamiast 15 heurystyk. Mniej kodu, spójne ryzyko.
- **R19.** **Watchdog rekoncyliacji z auto-haltem (#24)** — monitor baza↔broker już jest
  (ta sesja), ale pasywny. Dodaj: **rozjazd > próg → auto-halt + alarm.** To złapałoby HYPE.
- **R20.** **Portfelowy kill-switch (#25)** — jeden tripwire „coś jest nie tak → spłaszcz
  i alarmuj", ponad progi.
- **R21.** Cap koncentracji per moneta (20%, ta sesja) + bramka płynności (8×, ta sesja):
  **zostają**, ale dostrój do realnej płynności (R5).

### Warstwa 7 — Egzekucja
- **Stan:** `_execute_trade` w `trading_engine.py`, `alpaca_client.py` (retry 403 notional).
- **Co psuje:** (a) sizing liczony z `get_price`, który rozjeżdża się z realną wyceną Alpaki
  (źródło serii 403 i części blowoutu); (b) **brak modelu poślizgu** (roadmap #13) — backtest
  i sizing udają, że własne zlecenie nie rusza książki (na mikro-venue rusza ją o wszystko);
  (c) market ordery w cienką książkę = fatalne fille.
- **R22.** **Model poślizgu/fill w backteście i sizingu (#13)** — inaczej każdy backtest
  zawyża wynik i każdy sizing jest za duży.
- **R23.** Marketable-limit zamiast market na cienkich parach; nigdy nie przekraczaj
  ułamka widocznej głębokości jednym zleceniem (#14).

### Warstwa 8 — Rekoncyliacja / księgowość (najcichszy zabójca)
- **Stan:** snapshot portfela z salda Alpaki; monitor rekoncyliacji baza↔broker (ta sesja).
- **Co psuje:** **rozjazd $226–366k** — nasza baza myśli, że trzyma HYPE (2848 szt.), broker
  ma 0. Gotówka wyszła na kupno, pozycja warta ułamek — strata zjadła się po stronie FILLI,
  a realized/unrealized jej nie widzą. **Przez tygodnie P&L kłamał** („+$1 174" przy koncie −27%).
- **R24.** **Rozwiąż istniejący desync** (do decyzji właściciela): reset papierowego konta
  Alpaca ALBO kod re-syncujący ledger z realnymi pozycjami brokera (źródłem prawdy jest broker).
- **R25.** **Fille jako źródło prawdy, nie nasz zapis:** po każdym zleceniu czytaj realny fill
  z brokera (cena, ilość), nie wpisuj kwotu z `get_price`. Większość rozjazdu stąd.
- **R26.** Watchdog rekoncyliacji (R19) czyni ten błąd niemożliwym do przeoczenia na przyszłość.

### Warstwa 9 — Pomiar / uczciwość
- **Stan:** `scorecard.py` (epoch-aware, walk realized), `shadow_analysis.py`, `self_review.py`,
  `audit.py` → branch `audit-snapshots`. Monitor rekoncyliacji + baner (ta sesja).
- **Co psuje:** (a) **baza kosztowa zatruta blowoutem** → surowy scorecard pokazuje 0%
  trafności nawet dla BTC (artefakt); (b) epoch-hacki (`stats_epoch`) to łatanie objawu, nie
  przyczyny; (c) benchmark „bić BTC" liczony z opóźnieniem, nie na wierzchu silnika.
- **R27.** **Czysty baseline (roadmap #16):** albo reset historii, albo liczenie od pierwszego
  w pełni czystego wejścia — tak, żeby ani jeden pomiar nie dziedziczył blowoutu.
- **R28.** **Nagłówek-uczciwość zawsze na wierzchu (#38):** „bijemy BTC? tak/nie · na ilu
  trejdach · od kiedy" — jedna prawda, której nie da się przeoczyć.
- **R29.** **Scorecard epoch-aware w audit-snapshot (#17)** — żeby nadzór git-first widział
  czystą liczbę, nie surowy skażony log (dziś dziedziczy skażenie — stąd „0% trafności").

### Warstwa 10 — Pętla uczenia (obiecana „krzywa uczenia")
- **Stan:** `learning.py` (labeled_closes, feature_attribution, learning_curve — ta sesja),
  `llm_meta.py`. **W 80% aspiracyjne.**
- **Co psuje:** nie ma **feature store** (#1) ani trwałego etykietowania w R (#2) — bez tego
  „uczenie" uczy się szumu. Krzywa uczenia na 0% trafności/skażonej bazie nic nie mówi.
- **R30.** **Feature store (#1) + etykiety w R (#2)** — fundament. Każda decyzja zapisuje
  PEŁNY wektor cech, który widziała; każdy zamknięty trejd dostaje wynik przypięty do tych cech.
- **R31.** **Dopiero na tym** budować atrybucję (#3) → krzywą uczenia (#15) → adaptację OOS (#4).
  Kolejność z roadmapy jest poprawna; problem w tym, że budowaliśmy górę piramidy bez podstawy.
- **R32.** **Automatyczna adaptacja tylko po walk-forward (#4)** — koniec ręcznego strojenia
  knobów (to był błąd ery akcji: „gonienie szumu").

### Warstwa 11 — Autonomia / 24/7 autonadzór
- **Stan:** `scheduler.py` (cykle co 15–30 min, 24/7), rutyna dziennego nadzoru (ten chat),
  dziennik tygodniowy. Push/alerty (#36).
- **Co psuje — kluczowe dla „24/7":** 24/7 bez edge **mnoży churn** — więcej cykli = więcej
  wejść na szumie = więcej spreadu = szybsze krwawienie. 24/7 to **mnożnik**, nie przewaga:
  mnoży to, co masz. Mamy ujemny edge → mnoży straty.
- **Co działa:** sam autonadzór (git-first snapshoty, dziennik, raport w %) jest dobry i tani —
  to realna wartość, niezależnie od silnika.
- **R33.** **Rozdziel „częstotliwość nadzoru" od „częstotliwości handlu".** Nadzór 24/7 — tak.
  Handel 24/7 — dopiero gdy edge dodatni; inaczej wolniejszy cykl (dłuższe trzymania) tnie churn.
- **R34.** Autonadzór niech **pilnuje edge, nie tylko stanu:** auto-alarm „spadliśmy poniżej
  BTC" / „drawdown > próg" / „rozjazd rekoncyliacji" — proaktywnie (#36), nie tylko w raporcie.

### Warstwa 12 — UI / kontrola
- **Stan:** ControlRoom (Kokpit/Pozycje/Werdykt/Monety/Mózg), baner rekoncyliacji (ta sesja),
  panele learning/entry-gate/scanner. Dużo dobrego UX już jest (#29–31, #35 częściowo).
- **Co psuje:** UI pokazywał „zysk bota +$1k" przy koncie −27% (księgowość kłamała, W8) —
  UI jest tak uczciwy jak dane pod spodem. Drobny dług wizualny (naprawiony pasek pozycji, ta sesja).
- **R35.** Nagłówek-uczciwość (R28/#38) na każdym ekranie. **UI nie może nigdy pokazać zysku,
  gdy konto spada** — baner rekoncyliacji to zaczął, dokończ dla wszystkich metryk.
- **R36.** Dashboard eksperymentów (#34) + widok atrybucji (#37) — gdy fundament (W10) stanie.

### Warstwa 13 — Architektura / dług
- **Stan:** `trading_engine.py` **3343 linie** (monolit), 273 knoby, ~37 modułów services.
- **Co psuje:** (a) monolit `run_cycle` — trudno testować, łatwo o bug (luka HYPE: cap
  egzekwowany tylko w auto-deploy, bo logika rozlazła); (b) 273 knoby = 273 miejsca na bug
  i iluzja kontroli; (c) heurystyki zamiast pipeline'u.
- **R37.** **Pipeline warstwowy (#23):** Dane → Feature store → Model → Decyzja → Egzekucja →
  Wynik → Uczenie. Każda warstwa testowalna osobno. Koniec monolitu heurystyk.
- **R38.** **Zamroź i przejrzyj 273 knoby (#20):** wyłącz niezwalidowane. Cel: <50 knobów,
  każdy z uzasadnieniem z danych. Mniej kodu = mniej bugów.
- **R39.** **Walk-forward jako bramka CI (#28):** każda zmiana strategii/configu MUSI przejść
  OOS walk-forward przed merge. To instytucjonalizuje dyscyplinę i kończy zygzaki.
- **R40.** Dokończ rozbicie `run_cycle` (#21) — w toku; luka HYPE pokazała koszt monolitu.

---

## 4. Co wdrożono i co skasowano (inwentarz)

**Zbudowane i żyjące (wartość realna):** skaner uniwersum, trend-following z zarządzaniem
pozycją (trailing, drabinka TP, time-exit, MTF), halty katastroficzne + kill-switch dźwigni,
snapshoty audit-first + dziennik, monitor rekoncyliacji + baner (ta sesja), cap koncentracji
+ bramka płynności (ta sesja), bogaty UI, learning.py/llm_meta.py (szkielet).

**Zbudowane, ale wątpliwej wartości (dług/do rewizji):** 905-liniowy klient newsów (brak edge),
~15 bramek wejścia „na wiarę", opus_controller (262 linie, nieużywany od 09-11), część z 273
knobów, warstwa LLM-wetowania wejść (brak dowodu edge, wyłączona).

**Skasowane / wycofane w trakcie (słusznie):** `extended_regime_benchmark` (martwy), altseason-gate
(walk-forward go odrzucił — pogarszał), LLM dla krypto (ta sesja — przepalał, zatwierdzał blowout),
podnoszenie slotów do 20 (dolało ryzyka bez edge).

**Skasowane, a NIE powinno (albo nigdy nie dokończone):** test Claude-vs-mechanika (#1
rekomendacja każdego audytu — nigdy nie rozstrzygnięty), czysty baseline pomiaru (wciąż
łatamy epochem), feature store + etykiety (fundament uczenia — nie istnieje).

---

## 5. Meta-analiza narzędzia: czy „przewaga LLM + 24/7 autonadzór" ma sens?

**Przewaga LLM w handlu — uczciwa ocena:**
- W **decyzji wejścia** (wetowanie, timing): **brak dowodu, prawdopodobnie brak edge.** News
  jest w cenie w sekundy; LLM nie jest szybszy od rynku. Nasze dane to potwierdzają (zatwierdził
  blowout, kosztował, nic nie udowodnił). **Werdykt: NIE tutaj.**
- W **syntezie/rozumieniu** (post-mortem, meta-przegląd track-rekordu, tagowanie narracji,
  tłumaczenie „dlaczego" po ludzku): **tu LLM MOŻE realnie pomóc** — nie jako predyktor ceny,
  lecz jako **analityk własnej historii** i warstwa wyjaśnialności. To zasila atrybucję i naukę.
- **Werdykt:** „przewaga LLM" jest realna jako **meta-warstwa (uczenie/wyjaśnialność)**,
  iluzoryczna jako **predyktor wejść**. Zbudowaliśmy to drugie. Powinniśmy pierwsze.

**24/7 autonadzór — uczciwa ocena:**
- **Nadzór** 24/7 (obserwacja, alarmy, dziennik, pilnowanie edge/rekoncyliacji): **realna,
  tania wartość.** Zostaw.
- **Handel** 24/7: **mnożnik, nie edge.** Mnoży to, co masz. Przy ujemnym edge mnoży straty.
  Ma sens DOPIERO po udowodnieniu dodatniego edge po kosztach.

**Zdanie meta:** narzędzie ma sens jako **autonomiczny nadzorca + meta-uczeń nad mechaniczną
strategią trend-following na płynnym rynku**. Nie ma sensu jako **LLM-predyktor wejść
churnujący niepłynne alty na mikro-giełdzie 24/7**. Zbudowaliśmy drugie; trzeba pierwsze.

---

## 6. Trzy ścieżki naprzód (decyzja właściciela)

**Ścieżka A — „Udowodnij edge, potem skaluj" (rekomendowana, najtańsza w ryzyko).**
Wróć do rdzenia: BTC trend-following + garść płynnych altów, mechanika, LLM OFF, benchmark =
BTC na wierzchu. Rozwiąż rekoncyliację (R24), wyczyść baseline (R27), włącz shadow Claude-vs-
mechanika (R14). Handluj wolniej, mniej, dłużej. **Cel: alfa vs BTC dodatnia na ≥50 zamknięciach
BEZ blowoutu.** Dopiero wtedy wracają: LLM (jeśli wygra shadow), więcej kapitału, więcej slotów.

**Ścieżka B — „Przebuduj wg roadmapy, fundament najpierw".**
Zbuduj pętlę uczenia od podstaw: feature store (#1) + etykiety (#2) + atrybucja (#3) +
watchdog rekoncyliacji (#24) + walk-forward jako bramka CI (#28). Dopiero potem bogatsze
sygnały i LLM-synteza. To ścieżka „aplikacja jak zamierzona", ale dłuższa (tygodnie pracy).
Warta, jeśli celem jest trwałe narzędzie, nie szybki wynik.

**Ścieżka C — „Zmień venue albo zamknij krypto".**
Jeśli celem jest realna kasa: Alpaca crypto to zły rynek (W2). Albo rozdziel sygnał/egzekucję
(R4) i/lub przenieś na płynną giełdę, albo uznaj, że krypto na Alpace to ślepa uliczka i wróć
do akcji — tam edge był cienki, ale venue jest płynny i breakeven to realny punkt startu do
poprawy (udowodnij LLM vs mechanika na akcjach, R14).

**Moja rekomendacja:** **A + fundament rekoncyliacji/pomiaru z B (R24–R29), natychmiast.**
Konkretnie, w tej kolejności: (1) rozwiąż desync, (2) wyczyść baseline, (3) nagłówek-uczciwość
+ watchdog rekoncyliacji, (4) wznów silnik czysto (mechanika, cap koncentracji, bramka
płynności, BTC-rdzeń, LLM off), (5) włącz shadow, (6) zbieraj ≥3 tyg / ≥50 zamknięć, (7)
dopiero wtedy decyzja o LLM i skali.

**Nie ruszam nic bez Twojego słowa.** Powiedz, którą ścieżkę (lub które rekomendacje R#)
mam zacząć wdrażać.

---

*Meta-analiza na podstawie: `roadmap-krypto.md`, `krypto-strategia.md`, `krypto-rebudowa.md`,
`zalozenia-analiza.md`, `audyt-strategii-2026-09.md`, `audyt-kodu.md`, dziennika, snapshotów
`audit-snapshots`, kodu `backend/app/services/*` i pełnej historii tej sesji (blowout HYPE,
fixy, wyłączenie LLM). Liczby paper (krypto) i realne małe (akcje). Bez lukru, w %.*
