# 🎵 Śpiewnik

Aplikacja do prowadzenia własnego śpiewnika: **listy piosenek (setlisty)**,
**teksty z chwytami** widoczne w czytelny sposób, **moduł tabulatur** oraz
**wyszukiwarkę**, która po podaniu tytułu i zespołu sama pobiera tekst z sieci
i formatuje go pod śpiewnik.

Aplikacja działa w przeglądarce, a wszystkie dane trzymane są **lokalnie**
(localStorage). Lekki serwer w Node.js (bez żadnych zależności) serwuje
frontend i udostępnia moduł wyszukiwania/importu z internetu.

---

## Trzy sposoby użycia

### A) Na serwerze GielDarka — zalecane (dostęp zewsząd + synchronizacja)
Śpiewnik działa obok GielDarka na tym samym VPS, pod stałym adresem HTTPS
(`https://spiewnik.<ip>.sslip.io`, zaufany cert, PWA). Ma pełny backend, więc
działa **synchronizacja piosenek między urządzeniami** (dane na serwerze,
chronione tokenem) oraz **wyszukiwanie w sieci**. Instrukcja wdrożenia:
[`deploy/README-serwer.md`](deploy/README-serwer.md).

### B) Artefakt Claude (podręczna kopia, offline)
Aplikację można też opublikować jako **Artefakt Claude** — dostępny wszędzie,
gdzie zalogujesz się do Claude, bez serwera.

```bash
cd songbook && node build-artifact.mjs   # tworzy artifact/spiewnik.html (jeden plik)
```
Tu **dane są w przeglądarce urządzenia** (localStorage), a przenoszenie ich
odbywa się przez **Eksport / Import kopii**. Wyszukiwanie w sieci nie działa
(brak backendu) — użyj „Wklej tekst ręcznie” z auto-konwersją chwytów.

### C) Lokalnie (do rozwoju)
Wymagany tylko **Node.js ≥ 18** (bez `npm install` — zero zależności):

```bash
cd songbook/server && node server.js     # http://localhost:8080
```
Opcjonalnie `PORT=3000` oraz `SONGBOOK_TOKEN=...` (włącza wymóg tokenu) i
`SONGBOOK_DATA_DIR=...` (katalog danych). Frontend (`public/index.html`) można
też otworzyć wprost z dysku — działa jak wariant B.

## Synchronizacja (wariant z serwerem)

- Serwer trzyma bibliotekę w `library.json` (endpoint `GET/PUT /api/library`).
- Zmiany w aplikacji są automatycznie wysyłane (debounce ~1 s); po wejściu na
  innym urządzeniu biblioteka jest pobierana z serwera.
- Gdy ustawiony jest `SONGBOOK_TOKEN`, dostęp wymaga podania tokenu (raz na
  urządzenie). Bez tokenu dostęp jest otwarty — używaj tylko na prywatnym adresie.
- Model rozwiązywania konfliktów: „ostatni zapis wygrywa” dla całej biblioteki —
  w sam raz do użytku osobistego.

---

## Funkcje

### 📋 Listy (setlisty)
- Twórz dowolną liczbę list (ognisko, koncert, próba, msza…).
- Dodawaj piosenki, **zmieniaj kolejność** (strzałki lub przeciąganie „drag & drop”).
- Tryb **„Odtwórz listę”** — pełnoekranowy widok występu z przechodzeniem
  między utworami (klawisze ← →).

### 🎶 Piosenki — tekst i chwyty
- Format **ChordPro**: chwyty w nawiasach `[C]` dokładnie nad sylabą.
- Chwyty renderowane **czytelnie nad tekstem**, refren wyróżniony, komentarze,
  bloki tabulatury.
- **Diagramy akordów** gitarowych (rysunki chwytów) generowane automatycznie.
- **Transpozycja** o dowolną liczbę półtonów (w podglądzie i podczas występu).
- **Edytor z podglądem na żywo** + pasek narzędzi (wstaw chwyt, refren, komentarz, tabulaturę).
- Metadane: wykonawca, tonacja, kapodaster, tempo, tagi, notatki.

### 🎸 Moduł tabulatur
- Do każdej piosenki możesz dopiąć osobne tabulatury (intro, riff, solo…).
- Gotowa **pusta 6-strunowa siatka** jednym kliknięciem.
- Tabulatury w tekście przez `{start_of_tab} … {end_of_tab}` (czcionka stała).

### 🔎 Wyszukaj / Importuj
Trzy sposoby zdobycia materiału:
1. **Wykonawca + tytuł** → automatyczne pobranie tekstu z sieci
   (darmowe API [lyrics.ovh](https://lyrics.ovh), bez klucza).
2. **Import po URL** → wklej link do strony z chwytami/tabami; backend pobiera
   treść, czyści z HTML i **wykrywa chwyty nad tekstem**, formatując je do ChordPro.
3. **Wklej ręcznie** → wklej surowy tekst; **auto-konwersja** przekłada chwyty
   (linie akordów nad słowami) do formatu ChordPro. Działa też w pełni offline.

Wykryty materiał zawsze trafia do podglądu z możliwością poprawy przed zapisem.

### ⚙️ Wygląd i style
- Motyw jasny / ciemny / automatyczny.
- Czcionka, wielkość tekstu, odstęp linii, układ 1/2 kolumny.
- Kolor chwytów i tekstu, pogrubienie chwytów, włączanie/wyłączanie chwytów i diagramów.

### Dodatkowo
- 🥁 **Metronom** (na podstawie tempa utworu, Web Audio).
- 🖨 **Druk** przygotowany pod papier (ukryte menu, czarne chwyty).
- ⬇︎⬆︎ **Kopia zapasowa** — eksport/import całego śpiewnika do pliku JSON.
- 📱 Responsywność (menu chowane na telefonie).

---

## Format ChordPro (skrót)

```
{comment: Zwrotka 1}
[C]Panie mój, [G]dobry mój, [Am]bądź ze [F]mną

{start_of_chorus}
[F]Refren tutaj [C]jest wyróż[G]niony
{end_of_chorus}

{start_of_tab}
e|-----0-----0-----|
B|---0---0---0---0-|
{end_of_tab}
```

„H” jest traktowane jak „B” (zapis polski/niemiecki).

---

## Struktura projektu

```
songbook/
├── server/
│   ├── server.js        # serwer HTTP + /api/lyrics, /api/import (bez zależności)
│   └── package.json
└── public/
    ├── index.html
    ├── css/styles.css
    └── js/
        ├── app.js           # UI, routing, widoki
        ├── store.js         # dane + localStorage + kopia zapasowa
        ├── chordpro.js      # parser/renderer ChordPro + transpozycja + auto-konwersja
        ├── chords.js        # baza chwytów gitarowych + diagramy SVG
        └── search-client.js # klient modułu wyszukiwania
```

## Endpointy API

| Endpoint | Opis |
|---|---|
| `GET /api/health` | Status serwera. |
| `GET /api/lyrics?artist=&title=` | Tekst piosenki (lyrics.ovh). |
| `GET /api/import?url=` | Pobiera stronę i zwraca oczyszczony tekst. |

## Uwagi

- Automatyczne pobieranie **tekstów** korzysta z zewnętrznego, darmowego API —
  jego dostępność bywa zmienna. Import po URL i wklejanie ręczne są niezależne
  od tego źródła.
- Serwis pobiera strony wyłącznie na Twoje żądanie (podany URL). Szanuj prawa
  autorskie i regulaminy serwisów źródłowych — narzędzie służy do prywatnego
  użytku.
