#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# ŚPIEWNIK — samodzielny deploy (NIE dotyka GielDarka).
#
# Buduje i uruchamia WYŁĄCZNIE stack śpiewnika (osobny projekt compose
# "spiewnik", własna sieć, własny wolumen, własny port). GielDarek i inne apki
# są całkowicie nietknięte — ten skrypt nie odwołuje się do ich compose.
#
# Użycie (z katalogu repo, np. ~/gie-d):
#   bash songbook/deploy/spiewnik.sh            # sama apka (HTTP na :8090)
#   bash songbook/deploy/spiewnik.sh --audio    # + ciężki moduł akordów z audio
#   SPIEWNIK_PORT=9000 bash songbook/deploy/spiewnik.sh   # inny port
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

FILE="songbook/deploy/docker-compose.standalone.yml"
PROJECT="spiewnik"
PORT="${SPIEWNIK_PORT:-8090}"

# Wczytaj SONGBOOK_TOKEN / SONGBOOK_SEARCH_KEY z .env (jeśli jest) — bez sekretów w kodzie.
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a || true

AUDIO=0
for a in "$@"; do [ "$a" = "--audio" ] && AUDIO=1; done

export GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo dev)"
export BUILD_TIME="$(date -u +%Y-%m-%dT%H:%MZ)"
export SPIEWNIK_PORT="$PORT"

COMPOSE=(docker compose -p "$PROJECT" --project-directory "$ROOT" -f "$FILE")

echo "==> Śpiewnik: projekt '$PROJECT', port $PORT, wersja $GIT_SHA"
if [ "$AUDIO" = 1 ]; then
  export SONGBOOK_AUDIO_URL="http://songbook-audio:8100"
  echo "==> Z modułem audio (profil 'audio') — pierwszy build jest ciężki."
  "${COMPOSE[@]}" --profile audio up -d --build
else
  # Bez audio: zbuduj i wystaw samą apkę.
  "${COMPOSE[@]}" up -d --build songbook
fi

echo "==> Status:"
"${COMPOSE[@]}" ps

# Health: apka odpowiada jakimkolwiek kodem HTTP na swoim porcie?
code=000
for i in 1 2 3 4 5 6; do
  sleep 3
  code="$(curl -s -m 5 -o /dev/null -w '%{http_code}' "localhost:${PORT}/api/health" 2>/dev/null || echo 000)"
  [ "$code" != "000" ] && break
done
if [ "$code" != "000" ]; then
  echo "==> OK: śpiewnik odpowiada (HTTP $code). Adres: http://<IP-serwera>:${PORT}"
else
  echo "==> UWAGA: brak odpowiedzi na :${PORT}. Sprawdź: docker compose -p ${PROJECT} logs -f songbook"
fi
