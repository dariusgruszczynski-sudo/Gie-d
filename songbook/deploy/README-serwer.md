# Śpiewnik na serwerze — OSOBNY, izolowany stack

Śpiewnik działa na tym samym VPS co GielDarek, ale jako **całkowicie osobna
aplikacja**: własny projekt Dockera (`spiewnik`), własna sieć, własny wolumen
danych i **własny port HTTP**. Nie ma go w `docker-compose.yml`, `deploy.sh`
ani `Caddyfile` GielDarka — możesz go budować, restartować i zatrzymywać
niezależnie, **bez najmniejszego ryzyka dla GielDarka i innych apek**.

Dostajesz:

- **synchronizację między urządzeniami** — piosenki i listy trzymane są na
  serwerze (wolumen `songbook-data`), więc widzisz je wszędzie po zalogowaniu;
- **wyszukiwanie w sieci** (teksty z chwytami, import po URL) — bo jest backend;
- **adres:** `http://<IP-serwera>:8090` (domyślny port, zmienialny).

> **Uwaga o HTTPS/PWA:** ten izolowany wariant chodzi po HTTP na własnym porcie,
> bo porty 80/443 należą do Caddy GielDarka, a świadomie go NIE ruszamy. Jeśli
> kiedyś zechcesz zieloną kłódkę i instalację PWA — patrz sekcja „Opcjonalnie:
> HTTPS przez Caddy" na końcu (to jedyne miejsce, które dokłada 1 wpis do Caddy).

---

## Wdrożenie (izolowane, nie dotyka GielDarka)

### 1. Token dostępu (DOMYŚLNIE WYŁĄCZONY)
Śpiewnik startuje **bez tokenu** — żadnego pytania o hasło. Nie używa już
współdzielonego `SONGBOOK_TOKEN` GielDarka. Chcesz mimo to chronić hasłem?
Dopisz do `~/gie-d/.env` **osobną** linię:

```
SPIEWNIK_TOKEN=twoj-dlugi-losowy-token
```

Pusty/brak = otwarty dostęp (każdy, kto zna adres i port).

### 1b. (opcjonalnie) Lepsza wyszukiwarka
Wyszukiwarka domyślnie używa DuckDuckGo (bez klucza). Dla pewniejszych wyników
dodaj **własny** klucz SerpAPI w `.env` (osobny od GielDarka — bez współdzielenia
limitu):

```
SONGBOOK_SEARCH_KEY=twoj-klucz-serpapi
```

### 2. Uruchom
Na serwerze, w katalogu repo (`~/gie-d`), po `git pull`:

```bash
bash songbook/deploy/spiewnik.sh
```

To zbuduje i wystawi WYŁĄCZNIE śpiewnika (projekt `spiewnik`, port 8090).
GielDarek i inne apki pozostają nietknięte. Inny port:

```bash
SPIEWNIK_PORT=9000 bash songbook/deploy/spiewnik.sh
```

Zatrzymanie / restart tylko śpiewnika:

```bash
docker compose -p spiewnik --project-directory . \
  -f songbook/deploy/docker-compose.standalone.yml down     # stop
bash songbook/deploy/spiewnik.sh                            # ponowny start/przebudowa
```

### 3. Wejdź
`http://<IP-serwera>:8090` → podaj token → gotowe.

> Otwórz port w firewallu, jeśli masz zaporę (np. `ufw allow 8090/tcp`).

---

## (opcjonalnie, CIĘŻKIE) Wykrywanie akordów z audio
Osobny profil `audio` dokłada mikroserwis (librosa + ffmpeg + yt-dlp) oraz
`bgutil-provider` (PO-token, obejście bot-checku YouTube). Uruchom z profilem:

```bash
bash songbook/deploy/spiewnik.sh --audio
```

- Obraz jest duży, analiza obciąża CPU, wynik jest **przybliżony** (~70–85% na
  prostym popie) — punkt startowy do poprawki w edytorze.
- Pobieranie audio z YouTube bywa niezgodne z regulaminem — używaj prywatnie.

### Gdy YouTube pokazuje „Sign in to confirm you're not a bot"
Z serwerowni YouTube często blokuje pobieranie. `yt-dlp` próbuje po kolei:
PO-token (bgutil) → klient android → domyślny. Gdy wszystko utnie:

**Cookies (Netscape):**
1. Konto **„na zapas"** (nie główne Google).
2. Zaloguj się na `youtube.com`, wyeksportuj `cookies.txt` (rozszerzenie
   „Get cookies.txt LOCALLY").
3. Wgraj do `~/gie-d/songbook-audio-cookies/cookies.txt`.
4. `bash songbook/deploy/spiewnik.sh --audio` (odtworzy kontener audio).

Cookies wygasają — jak błąd wróci, wyeksportuj ponownie. Plik jest w `.gitignore`.

> **Pewna droga bez YouTube:** przycisk **„🎵 Z pliku audio"** — wgrywasz mp3/m4a,
> analiza idzie lokalnie, bez bot-checku. Albo **„🔎 + chwyty"** — gotowe
> opracowania z chwytami po tytule.

---

## Kopia zapasowa danych
Piosenki leżą w `~/gie-d/songbook-data/library.json` — zrób backup tego pliku
(albo przycisk **Eksport kopii** w aplikacji). Te same dane działają dalej po
przejściu na izolowany stack (ten sam katalog jest podmontowany).

## Rozwiązywanie problemów
- Logi: `docker compose -p spiewnik logs -f songbook`.
- „Wymagany token" → `SONGBOOK_TOKEN` w `.env` ≠ ten wpisany w apce.
- Nie otwiera się na porcie → sprawdź firewall (otwórz `8090/tcp`) i `docker ps`.

---

## Opcjonalnie: HTTPS przez Caddy (jeśli chcesz kłódkę i PWA)
To JEDYNY wariant, który dokłada wpis do Caddy GielDarka. Caddy trasuje po nazwie
hosta, więc taki blok **nie wchodzi w drogę** innym apkom — obsługuje tylko
subdomenę śpiewnika. Wymaga, by Caddy widział kontener śpiewnika w sieci.

Najprościej: dołącz Caddy GielDarka do sieci `spiewnik_default` i dodaj blok:

```
spiewnik.46.225.229.113.sslip.io {
    encode zstd gzip
    reverse_proxy songbook:8080
}
```

Jeśli tego chcesz — powiedz, przygotuję dokładne kroki pod Twój `Caddyfile`
tak, żeby nadal nic nie groziło GielDarkowi.
