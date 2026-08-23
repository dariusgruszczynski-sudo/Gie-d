#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# ŚPIEWNIK — AUTO-DEPLOY (osobny od GielDarka, bez wyścigu o git).
#
# Uruchamiany cyklicznie (systemd timer). NIE dotyka gita (żadnego fetch/reset),
# więc nigdy nie wchodzi w drogę autopullowi GielDarka. Tylko:
#   1) patrzy, na jakim commicie stoi repo (HEAD — utrzymywany aktualnym przez
#      autopull GielDarka albo Twój `git pull`),
#   2) jeśli od ostatniego wdrożenia śpiewnika zmieniło się COKOLWIEK w songbook/,
#      przebudowuje TYLKO stack śpiewnika (songbook/deploy/spiewnik.sh),
#   3) zapisuje swój własny znacznik ostatnio wdrożonego commita.
#
# Dzięki temu: piszesz kod śpiewnika z web/telefonu → wjeżdża na gałąź → repo się
# aktualizuje → śpiewnik sam się przebudowuje w kilka minut. Bez terminala.
#
# Instalacja jednorazowa:  sudo bash songbook/deploy/install-spiewnik-autodeploy.sh
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
STAMP="$ROOT/.last_deployed_spiewnik_sha"

LOG() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] spiewnik: $*"; }

CUR="$(git rev-parse HEAD 2>/dev/null || echo none)"
[ "$CUR" = none ] && { LOG "brak gita — pomijam"; exit 0; }
LAST="$(cat "$STAMP" 2>/dev/null || echo none)"

if [ "$CUR" = "$LAST" ]; then
  exit 0   # nic nowego — cisza
fi

# Czy między ostatnim wdrożeniem a teraz zmieniło się coś w kodzie śpiewnika?
# (Gdy brak wcześniejszego znacznika albo commit nieznany — budujemy na pewno.)
if [ "$LAST" != none ] && git cat-file -e "${LAST}^{commit}" 2>/dev/null; then
  if [ -z "$(git diff --name-only "$LAST" "$CUR" -- songbook/ 2>/dev/null)" ]; then
    echo "$CUR" > "$STAMP"        # zmiany były, ale nie w śpiewniku — tylko odnotuj
    exit 0
  fi
fi

LOG "nowa wersja śpiewnika ${LAST:0:7} -> ${CUR:0:7} — przebudowuję stack."
# --audio jeśli włączony znacznikiem (świadomie), tak jak wcześniej audio.enabled.
AUDIO_FLAG=""
[ -f "$ROOT/songbook/deploy/audio.enabled" ] && AUDIO_FLAG="--audio"
if bash "$ROOT/songbook/deploy/spiewnik.sh" $AUDIO_FLAG; then
  echo "$CUR" > "$STAMP"
  LOG "OK — wdrożono ${CUR:0:7}."
else
  LOG "BUILD NIEUDANY — zostaje poprzednia wersja. Log: docker compose -p spiewnik logs -f songbook"
  exit 1
fi
