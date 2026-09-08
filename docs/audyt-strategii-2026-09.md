# GielDarek — Audyt strategii, predykcji i rekomendacje (wrzesień 2026)

**Data:** 2026-09-02 · **Dane bazowe:** gałąź `audit-snapshots` (18 snapshotów żywego konta, 18.08–02.09) · tryb **LIVE**.
**Kontekst:** konto ~$500–800 + wpłaty $100–300/mies. · model Sonnet · poll 30 min.

> Dokument-siostra: `docs/zalozenia-analiza.md` (analiza 15 założeń, 21.08). Tu: audyt *po* wdrożeniu Scenariusza A i cofnięciu mnożnika, z predykcjami.

---

## 1. Jaka jest teraz strategia (zweryfikowane w `deploy/deploy.sh` + kod)

**Silnik:** dzienny (1d) swing pozycyjny, jeden zdyscyplinowany silnik (bez krypto, bez poza-sesją). Poll co 30 min, pełna analiza bramkowana wyzwalaczem, model **Sonnet** (eskalacja do Opusa OFF).

**Wejścia / jakość:**
- Próg pewności bazowy 0.55 **+ 0.03 za każdą otwartą pozycję** (cap 0.9), min. kupno 0.60 → progresywny próg dusi 6.+ wejście, wymuszając jakość.
- Uniwersum: whitelist 17 nazw jakości (SPY/QQQ/mega-cap + SMH/GLD/TLT), blacklist lewarowanych/odwrotnych ETF, dynamiczne uniwersum max 24, **halt na blackout newsów**.
- Limity: max 12 pozycji naraz, max 8 wejść/dzień.

**Wyjścia / anty-churn:**
- Min hold 2 dni; realny zysk **≥3% bierze od razu**; twardy TP **+6%**; stop **3%**; trailing 0.6.

**Ryzyko / sizing:**
- **Conviction sizing „Scenariusz A": mnożnik do 1.5×** (obniżony z 2.0× dnia 2026-09-02, patrz §2), twardy sufit **6% ryzyka/trade**, adaptacja edge (payoff 2.0→4.0 ściąga mnożnik do 1.0, gdy przewaga słabnie).
- Regime gate ON (risk-off → tylko GLD/TLT), adaptive risk OFF. Halt katastroficzny przy obsunięciu 45%.

**Jednym zdaniem:** *dzienny, asymetryczny (tnij straty / pozwól zyskom rosnąć), zdyscyplinowany bot z twardymi limitami ryzyka i dławikiem częstotliwości — dobrze zaprojektowany.*

---

## 2. Audyt: czy to ma sens? (dane, nie przeczucia)

Trajektoria zrealizowanego P&L (tylko akcje, od epoki 2026-08-10):

| Data | Zrealizowany | Payoff | Edge/trade | Trafność | Śr. strata |
|---|---|---|---|---|---|
| 21.08 (wdrożenie 2×) | $13.96 | 4.89× | +$0.46 | 30% | −0.61 |
| **26.08 (szczyt)** | **$17.18** | 4.57× | +$0.50 | 32% | −0.63 |
| 02.09 (dziś) | **$6.95** | **3.1×** | **+$0.17** | 28.6% | **−0.96** |
| ostatnie 7 dni | **−$10.23** | — | — | **12.5%** | — |

Trzy wnioski, w kolejności ważności:

### ① Edge jest DODATNI, ale bardzo cienki — pytanie brzmi, czy jest PRAWDZIWY
+$0.17/transakcję (payoff 3.1×) to realna, ale mikra przewaga. Cały wynik wisi na kilku dużych wygranych (ARGX, COIN, MU) przy ~30% trafności — to znaczy, że pojedynczy słaby tydzień potrafi oddać cały życiowy zysk (i dokładnie to zrobił: z +$17 na szczycie do ~$0 dziś). Nie jest to wada strategii, tylko natura asymetrii przy małej próbce. Kluczowe nie jest więc „ile to kosztuje", tylko: czy te +$0.17 to przewaga, czy szum (patrz ②).

> **Koszt tokenów AI świadomie POMIJAM w tej ocenie.** Właściciel kupuje tokeny do wielu zastosowań — to budżet dzielony/utopiony, nie marginalny wydatek doliczany do P&L bota. Doliczanie go do wyniku handlu byłoby błędem księgowym.

### ② „Predykcje mają sens" — NIE jest jeszcze udowodnione statystycznie
42–54 zamknięć to za mała próbka, żeby odróżnić przewagę od szczęścia na ogonie. Trafność ~30% + payoff 3–5× jest spójna ZARÓWNO z realną przewagą, JAK I z fartem małej próbki. Ostatnie 7 dni (12.5%, −$10) to przypomnienie, jak szumny jest ten sygnał. **Uczciwy werdykt: predykcje prawdopodobnie coś wnoszą, ale to hipoteza, nie fakt.** W kodzie jest `shadow_analysis` (co zrobiłaby sama mechanika) — dopóki nie porównasz „Claude vs mechanika" na tej samej próbce miesiąc do miesiąca, nie wiesz, czy AI realnie dokłada przewagę, czy tylko naśladuje mechanikę (którą miałbyś za darmo).

### ③ Sam projekt strategii jest zdrowy
Asymetria idzie we właściwą stronę (wygrane trzymane ~4.5 dnia, straty ~2.1), churn spadł (118→54 zamknięć/30d), twarde limity ryzyka działają, najgorsze przecieki (JAZZ, NDSN, ROST) już na blackliście. Cofnięcie 2×→1.5× (2026-09-02) jest słuszne — era 2× **pogłębiała straty (−0.61→−0.96), nie podnosząc wygranych** (płaskie ~2.98), więc amplifikowała złą stronę asymetrii.

---

## 3. Predykcje (ocena, dokąd to zmierza)

- **Przy obecnym kapitale bot jest laboratorium, nie źródłem dochodu.** Życiowo ~$0 na małej próbce; nawet w dobrym scenariuszu ~$14/mies. brutto przy 2.3% na $600 → w horyzoncie 12–18 mies. **wynik zdominują wpłaty ($100–300/mies.), nie zysk bota.** Realny „drugi strumień" zaczyna się ~$20–50k.
- **Główne ryzyko to nie rynek, tylko że „przewaga" okaże się szumem** — na 45 zamknięciach nie da się tego jeszcze rozstrzygnąć. Dlatego test vs mechanika (§4) jest ważniejszy niż kręcenie parametrami.
- **Strategia w projekcie jest dobra i skaluje się w górę** — te same knoby na $10k+ mają sens; problem jest wyłącznie skali kapitału (mikre kwoty przy małym koncie), nie logiki.

---

## 4. Rekomendacje (priorytetowo)

1. **Włącz miesięczny test „Claude vs mechanika"** (shadow-analysis). To make-or-break: dopóki Claude nie bije samej mechaniki na tej samej próbce — teza o wartości predykcji jest nieudowodniona. Najważniejsza rzecz do zrobienia.
2. **Zostaw conviction 1.5× na ~2 tygodnie, potem re-audyt.** Zmiana właśnie weszła — nie mieszaj drugiej zmiennej (ryzyko/trade 6%→4%) w tym samym oknie.
3. **Rozważ czysty A/B:** mechanika-only na stagingu (:8092) vs Claude na prodzie przez miesiąc — da porównanie, którego teza potrzebuje, bez ryzyka realną kasą.
4. **Ustaw oczekiwania w kaflu „Plan i cel":** to walidacja przewagi na małych stawkach, nie pensja. Kwoty przyjdą z kapitału.
5. **Pilnuj powtarzalnych przecieków** (CRWD, OKTA, JAZZ i spółka) — dorzucanie recydywistów do blacklisty to najtańsza poprawa edge.

**Nadrzędna prawda:** strategia jest dobrze zaprojektowana i ma (cienką) dodatnią przewagę brutto. Pytanie nie brzmi „ile kosztuje", tylko **czy ta przewaga jest prawdziwa, czy to szum małej próbki** — i to rozstrzygnie porównanie z mechaniką, nie kręcenie parametrami. Udowodnij przewagę nad mechaniką i pozwól kapitałowi rosnąć.

---

*Audyt oparty na snapshotach `audit-snapshots` (read-only `/api/audit`). Metodyka: porównanie trajektorii edge/payoff/$-per-trade wokół wdrożenia Scenariusza A (2026-08-21 18:31Z). Zastrzeżenie: próbka 42–54 zamknięć jest statystycznie mała; wnioski to sygnały, nie pewniki.*
