# Deploy "wielkiej przebudowy"

Zmiany (PM-mode / Claude prowadzi cały portfel, dynamiczne uniwersum zamiast
whitelisty, newsy Alpaca + AlphaVantage + NewsAPI + SerpAPI, blackout newsów =
alarm + stop nowych wejść, zdjęty kaganiec, popupy kup/sprzedaj/czeka) siedzą na
gałęzi `claude/automated-stock-trading-app-ulacio`.

## Jak wdrożyć (na serwerze produkcyjnym)

Zaloguj się i uruchom skrypt deployowy z katalogu repo:

```bash
ssh root@46.225.229.113
cd /root/Gie-d                 # <- ścieżka repo na serwerze; zmień, jeśli inna
git fetch origin claude/automated-stock-trading-app-ulacio
git checkout claude/automated-stock-trading-app-ulacio
./deploy/deploy.sh
```

`deploy.sh` jest idempotentny: zaciąga najnowszy kod, wymusza w `.env` (i
`.env.staging`) wszystkie nie-sekretne knoby tej zmiany (bo `.env` nadpisuje
kod), przebudowuje kontenery (`docker compose up -d --build`) i sprawdza health.

## Sekrety (skrypt ich NIE wpisuje)

- **Klucze Alpaca** — zostają nietknięte (prod = żywe konto, staging = paper).
- **Klucze newsów** (`ALPHA_VANTAGE_API_KEY`, `NEWSAPI_API_KEY`,
  `SERPAPI_API_KEY`) — muszą już być w `.env`. Skrypt ostrzega, jeśli któregoś
  brakuje. Alpaca News działa bez dodatkowego klucza (używa pary Alpaca).

## Po deployu

- Dashboard: `:8000` (prod), `:8092` (staging).
- Health board: `:8000/api/health` — zakładka **Puls**. Sprawdź kafelek
  „Newsy (dane)": ile nagłówków realnie spływa i czy nie ma BLACKOUTu.
- Logi: `docker compose logs -f app`.
