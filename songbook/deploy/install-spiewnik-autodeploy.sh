#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# ŚPIEWNIK — INSTALATOR własnego auto-deployu (osobny od GielDarka).
# Uruchamiasz RAZ na serwerze:
#     sudo bash songbook/deploy/install-spiewnik-autodeploy.sh
# Od tej chwili śpiewnik sam przebudowuje się, gdy w repo pojawią się zmiany w
# jego kodzie (patrz songbook/deploy/autopull-spiewnik.sh). Nie rusza GielDarka.
#
# Idempotentny. Odinstalowanie — na końcu pliku (w komentarzu).
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
INTERVAL="${1:-5min}"   # np. sudo bash ... 3min

if [ "$(id -u)" -ne 0 ]; then
  echo "Uruchom przez sudo:  sudo bash songbook/deploy/install-spiewnik-autodeploy.sh" >&2
  exit 1
fi

echo "==> Repo: $ROOT   |   interwał: $INTERVAL"
chmod +x "$ROOT/songbook/deploy/autopull-spiewnik.sh" "$ROOT/songbook/deploy/spiewnik.sh"

OWNER="$(stat -c '%U' "$ROOT")"
echo "==> Auto-deploy śpiewnika będzie biegł jako: $OWNER"

cat > /etc/systemd/system/spiewnik-autodeploy.service <<UNIT
[Unit]
Description=Spiewnik auto-deploy (rebuild spiewnik stack on new commit)
After=docker.service network-online.target
Wants=docker.service network-online.target

[Service]
Type=oneshot
User=$OWNER
WorkingDirectory=$ROOT
ExecStart=$ROOT/songbook/deploy/autopull-spiewnik.sh
UNIT

cat > /etc/systemd/system/spiewnik-autodeploy.timer <<UNIT
[Unit]
Description=Spiewnik auto-deploy co $INTERVAL

[Timer]
OnBootSec=2min
OnUnitActiveSec=$INTERVAL
Unit=spiewnik-autodeploy.service

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now spiewnik-autodeploy.timer

echo "==> Zainstalowane. Status timera:"
systemctl list-timers spiewnik-autodeploy.timer --no-pager || true
echo
echo "GOTOWE. Zmiany w kodzie śpiewnika wdrożą się same w <= $INTERVAL (bez terminala)."
echo "  Log:         journalctl -u spiewnik-autodeploy.service -f"
echo "  Wymuś teraz: sudo systemctl start spiewnik-autodeploy.service"
echo "  Odinstaluj:  sudo systemctl disable --now spiewnik-autodeploy.timer && \\"
echo "               sudo rm /etc/systemd/system/spiewnik-autodeploy.{service,timer} && \\"
echo "               sudo systemctl daemon-reload"
