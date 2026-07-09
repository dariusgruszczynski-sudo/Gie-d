# Zabezpieczenie serwera GielDarek

Krótki przewodnik jak utwardzić VPS-a, na którym stoi bot. Wszystko idempotentne
— można odpalać wielokrotnie. Kolejność ma znaczenie: **najpierw klucz SSH**,
potem reszta.

## 0. Zanim zaczniesz: klucz SSH (żeby się nie zablokować)

Skrypt wyłączy logowanie hasłem — bez klucza stracisz dostęp. Z **własnego
komputera** (nie z serwera):

```bash
ssh-keygen -t ed25519            # tylko jeśli nie masz jeszcze klucza
ssh-copy-id root@46.225.229.113  # wgrywa klucz publiczny na serwer
ssh root@46.225.229.113          # sprawdź, że wchodzi BEZ pytania o hasło
```

Jeśli `ssh-copy-id` przechodzi i drugie logowanie nie pyta o hasło — jesteś
bezpieczny, skrypt może wyłączyć hasła. Jeśli klucza nie ma, skrypt sam
**pominie** ten krok (hasło zostanie włączone) i o tym poinformuje.

## 1. Firewall + fail2ban + auto-updaty + uprawnienia (jeden skrypt)

Na serwerze:

```bash
ssh root@46.225.229.113
cd ~/gie-d && git pull origin claude/automated-stock-trading-app-ulacio
bash deploy/harden.sh
```

Co robi (`deploy/harden.sh`):

1. **ufw** — wpuszcza tylko SSH + 80/443 (+ tymczasowo 8000), resztę blokuje.
2. **fail2ban** — banuje IP próbujące zgadnąć hasło SSH (5 prób → ban 1h).
3. **unattended-upgrades** — automatyczne łatki bezpieczeństwa.
4. **SSH** — wyłącza logowanie hasłem i root-em na hasło (tylko klucz), ale
   **wyłącznie jeśli klucz jest już wgrany** (test `sshd -t` + rollback).
5. **.env → chmod 600** — klucze API czytelne tylko dla właściciela.

## 2. HTTPS przez Caddy (żeby nie latać po gołym HTTP)

Teraz dashboard chodzi po gołym HTTP na porcie 8000 — hasło do panelu i cały
ruch lecą otwartym tekstem. Caddy stawia przed nim szyfrowany reverse proxy.

```bash
# instalacja Caddy (Debian/Ubuntu)
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update && apt-get install -y caddy

# podłóż naszą konfigurację
cp ~/gie-d/deploy/Caddyfile /etc/caddy/Caddyfile
# --- jeśli masz domenę: odkomentuj wariant A w /etc/caddy/Caddyfile
#     i wpisz swoją domenę; jeśli tylko IP -- zostaw wariant B (tls internal)
systemctl restart caddy
```

Następnie zamknij aplikację do localhost (dostęp tylko przez Caddy):

```bash
cd ~/gie-d
docker compose -f docker-compose.yml -f deploy/docker-compose.localhost.yml up -d
ufw delete allow 8000/tcp      # port 8000 nie musi już być otwarty na świat
```

Od teraz wchodzisz na `https://TWOJA-DOMENA` (albo `https://46.225.229.113`
z ostrzeżeniem o self-signed przy wariancie B).

## 3. Rotacja kluczy API (WAŻNE)

Klucze, które wklejałeś w czacie, traktuj jak **spalone** — wygeneruj nowe i
podmień w `~/gie-d/.env` na serwerze (nigdy w repo):

- **eToro** — Agent Portfolio → wygeneruj nowy `x-api-key` i `x-user-key`.
- **Alpaca** — dashboard → regenerate API key.
- **Anthropic** — console.anthropic.com → nowy klucz, stary skasuj.

Po podmianie `.env`:

```bash
chmod 600 ~/gie-d/.env
cd ~/gie-d && docker compose up -d --force-recreate
```

## 4. Mocne hasło do dashboardu

W `.env` ustaw `DASHBOARD_USERS` na własną parę login:hasło (długie, losowe) —
bez tego panel jest bez logowania:

```
DASHBOARD_USERS=darek:dlugie-losowe-haslo-tutaj
```

## Checklista

- [ ] klucz SSH wgrany, logowanie bez hasła działa
- [ ] `bash deploy/harden.sh` przeszedł (ufw + fail2ban + auto-updaty)
- [ ] Caddy stoi, wchodzę po HTTPS
- [ ] app zbindowana na 127.0.0.1, port 8000 zamknięty na ufw
- [ ] klucze API zrotowane, `.env` = 600
- [ ] `DASHBOARD_USERS` ustawione na mocne hasło
