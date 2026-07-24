#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GielDarek -- deploy "wielkiej przebudowy" (PM-mode, dynamiczne uniwersum,
# newsy Alpaca/AlphaVantage/NewsAPI/SerpAPI, blackout newsów, zdjęty kaganiec,
# popupy). Idempotentny: można puszczać wielokrotnie.
#
# Co robi:
#   1. Przełącza repo na gałąź deployową i zaciąga najnowszy kod.
#   2. Wymusza w .env (i .env.staging) wszystkie NIE-sekretne knoby tej zmiany
#      -- bo .env nadpisuje kod, więc bez tego część zmian by nie weszła.
#   3. Przebudowuje i restartuje kontenery (prod app + staging) z tego kodu.
#   4. Sprawdza health.
#
# NIE dotyka sekretów: kluczy Alpaca ani kluczy newsów. Klucze newsów muszą już
# być w .env (skrypt tylko ostrzega, jeśli ich nie ma). Klucze Alpaca zostają
# nietknięte (prod = żywe, staging = paper -- świadomie różne).
#
# Użycie (na serwerze, w katalogu repo):  ./deploy/deploy.sh
# ---------------------------------------------------------------------------
set -euo pipefail

BRANCH="claude/automated-stock-trading-app-ulacio"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
echo "==> Repo: $ROOT"

# --- 1) Kod ----------------------------------------------------------------
echo "==> Pobieram gałąź $BRANCH"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"   # .env jest w .gitignore, więc go NIE rusza
echo "==> Kod na: $(git rev-parse --short HEAD) $(git log -1 --format=%s)"

# --- 2) .env: wymuś nie-sekretne knoby (idempotentnie) ---------------------
setenv() { # setenv KEY VALUE FILE
  local k="$1" v="$2" f="$3"
  touch "$f"
  sed -i "/^${k}=/d" "$f"
  printf '%s=%s\n' "$k" "$v" >> "$f"
}

apply_knobs() { # apply_knobs FILE
  local f="$1"
  [ -f "$f" ] || { echo "   (pomijam $f -- brak pliku)"; return 0; }
  echo "==> Ustawiam knoby w $f"
  # Kadencja / agresja
  setenv POLL_INTERVAL_MINUTES 15 "$f"
  setenv EXTENDED_POLL_INTERVAL_MINUTES 30 "$f"
  setenv PRICE_MOVE_TRIGGER_PCT 1.5 "$f"
  # Oszczędność tokenów poza sesją: Claude w nodze POZA SESJĄ tylko na
  # katalizatorze (news / mocny ruch), bez rutynowego heartbeatu.
  setenv EXTENDED_PRICE_MOVE_TRIGGER_PCT 3.0 "$f"
  setenv EXTENDED_FULL_ANALYSIS_EVERY_MINUTES 0 "$f"
  setenv FULL_ANALYSIS_EVERY_MINUTES 30 "$f"
  setenv MAX_POSITION_PCT 90 "$f"
  # Zdjęty kaganiec (zostają tylko pasy bezpieczeństwa w kodzie)
  setenv CLAUDE_PAUSE_TRADING_AT_BUDGET true "$f"
  setenv CLAUDE_ESCALATION_ENABLED false "$f"
  setenv MIN_BUY_CONFIDENCE 0.55 "$f"
  setenv MAX_CONCURRENT_POSITIONS 4 "$f"
  setenv ENTRY_FILTER_ENABLED true "$f"
  setenv MAX_NEW_POSITIONS_PER_DAY 4 "$f"
  setenv MIN_HOLD_MINUTES 90 "$f"
  setenv AUTO_DEMOTE_ENABLED false "$f"
  setenv CLAUDE_MONTHLY_BUDGET_USD 150 "$f"
  # Blackout newsów (bezpieczeństwo: brak danych = stop nowych wejść + alarm)
  setenv NEWS_BLACKOUT_HALT_ENABLED true "$f"
  setenv NEWS_MIN_HEADLINES 3 "$f"
  # Dynamiczne uniwersum (whitelista zbędna)
  setenv DYNAMIC_UNIVERSE_ENABLED true "$f"
  setenv UNIVERSE_MAX_SYMBOLS 24 "$f"
}

apply_knobs .env
apply_knobs .env.staging

# Ostrzeżenie, jeśli brakuje kluczy newsów (skrypt ich NIE wpisuje -- to sekrety)
for K in ALPHA_VANTAGE_API_KEY NEWSAPI_API_KEY SERPAPI_API_KEY; do
  if ! grep -qE "^${K}=.+" .env 2>/dev/null; then
    echo "   UWAGA: brak $K w .env -- to źródło newsów będzie pominięte (Alpaca News i tak działa)."
  fi
done

# --- 3) Build + restart ----------------------------------------------------
echo "==> Przebudowuję i restartuję kontenery (prod + staging)"
docker compose up -d --build

# --- 4) Health -------------------------------------------------------------
echo "==> Status kontenerów"
docker compose ps
echo "==> Czekam na start i sprawdzam health (prod :8000)"
sleep 6
curl -fsS localhost:8000/api/status >/dev/null && echo "   OK: /api/status odpowiada" || echo "   UWAGA: /api/status nie odpowiada jeszcze -- sprawdź: docker compose logs -f app"
echo "==> Gotowe. Health board: localhost:8000/api/health  |  dashboard: :8000 (prod), :8092 (staging)"
