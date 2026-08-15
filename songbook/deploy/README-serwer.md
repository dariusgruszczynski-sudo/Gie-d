# Śpiewnik na serwerze GielDarka (ten sam VPS)

Śpiewnik może działać na tym samym serwerze co GielDarek, obok niego, jako
osobna usługa w Dockerze. Dostajesz wtedy:

- **stały adres HTTPS** z zaufanym certyfikatem (zielona kłódka, PWA — „ikona na
  telefonie”): `https://spiewnik.46.225.229.113.sslip.io`
  *(subdomena sslip.io wskazuje na ten sam IP — nic nie kupujesz, nie ustawiasz DNS)*;
- **synchronizację między urządzeniami** — piosenki i listy trzymane są na
  serwerze (wolumen `songbook-data`), więc widzisz je wszędzie po zalogowaniu;
- **wyszukiwanie w sieci** (pobieranie tekstów, import po URL) — bo jest backend.

To jest wariant „z serwerem”. Artefakt Claude nadal istnieje jako wersja
podręczna (offline, dane na urządzeniu) — patrz `../README.md`.

---

## Jak to jest wpięte (bez ruszania produkcji GielDarka)

- **Osobna usługa** `songbook` w nakładce `songbook/deploy/docker-compose.songbook.yml`
  (nie zmienia głównego `docker-compose.yml`).
- **Caddy** dostał dodatkowy blok w `deploy/Caddyfile.docker` na subdomenę
  `spiewnik.*` → kontener `songbook:8080`.
- **`deploy/deploy.sh`** dołącza nakładkę do TEJ SAMEJ komendy compose (jak Caddy),
  ale tylko gdy plik nakładki istnieje — więc reszta działa jak dawniej.

## Wdrożenie

### 1. Ustaw token dostępu (zalecane)
Adres jest publiczny, więc chroń śpiewnik hasłem. Dopisz do pliku `.env` w repo
(`~/gie-d/.env`) jedną linię:

```
SONGBOOK_TOKEN=twoj-dlugi-losowy-token
```

Bez tokenu każdy z adresem miałby dostęp do Twoich piosenek. Token podajesz raz
na każdym urządzeniu (aplikacja zapamiętuje go w przeglądarce).

### 1b. (opcjonalnie) Wyszukiwarka opracowań z chwytami
Wyszukiwarka szuka w sieci opracowań z chwytami i daje listę wyników do wyboru.
Domyślnie używa DuckDuckGo (bez klucza, ale bywa mniej pewne). Dla najlepszych
wyników użyj SerpAPI:
- podaj własny klucz: `SONGBOOK_SEARCH_KEY=...` w `.env`, **albo**
- pozwól reużyć klucz GielDarka — nakładka przekazuje `SERPAPI_API_KEY` z `.env`
  (uwaga: współdzielony limit zapytań z botem).

### 2. Zbuduj i uruchom
Na serwerze, w katalogu repo (`~/gie-d`), po `git pull`:

```bash
bash deploy/deploy.sh
```

`deploy.sh` sam wykryje nakładkę śpiewnika, zbuduje kontener `songbook`
i przeładuje Caddy z nową subdomeną. GielDarek (prod + staging) buduje się jak
wcześniej.

**Albo ręcznie**, jednym compose (z `~/gie-d`):

```bash
docker compose \
  -f docker-compose.yml \
  -f deploy/docker-compose.caddy.yml \
  -f songbook/deploy/docker-compose.songbook.yml \
  up -d --build songbook caddy
```

### 3. Wejdź
`https://spiewnik.46.225.229.113.sslip.io` → podaj token → gotowe. Na telefonie
„Dodaj do ekranu głównego”, by mieć ikonę jak aplikacja.

> Jeśli IP serwera się zmieni — podmień je w `deploy/Caddyfile.docker`
> (blok `spiewnik.…`) i tu, w adresach.

## Kopia zapasowa danych
Piosenki leżą w `~/gie-d/songbook-data/library.json`. Wystarczy backup tego pliku
(albo przycisk **Eksport kopii** w aplikacji).

## Rozwiązywanie problemów
- `docker compose ... logs -f songbook` — logi śpiewnika.
- „Wymagany token” po wpisaniu → token w `.env` ≠ ten wpisany; sprawdź i podaj ponownie.
- Brak zielonej kłódki od razu → Caddy potrzebuje chwili na cert Let's Encrypt;
  wymaga otwartych portów 80/443 (te same, których używa GielDarek).
