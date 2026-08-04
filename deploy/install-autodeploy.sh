#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# GielDarek -- INSTALATOR auto-deployu. Uruchamiasz RAZ na serwerze:
#     sudo bash deploy/install-autodeploy.sh
# Od tej chwili serwer sam sprawdza GitHuba co 5 min i wdraża każdy nowy commit
# na gałęzi deployowej (patrz deploy/autopull.sh). Bez SSH z zewnątrz, bez portów.
#
# Idempotentny: możesz puścić ponownie, żeby nadpisać/naprawić instalację.
# Odinstalowanie na końcu tego pliku (w komentarzu).
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INTERVAL="${1:-5min}"   # opcjonalnie: sudo bash deploy/install-autodeploy.sh 3min

if [ "$(id -u)" -ne 0 ]; then
  echo "Uruchom przez sudo:  sudo bash deploy/install-autodeploy.sh" >&2
  exit 1
fi

echo "==> Repo: $ROOT   |   interwał: $INTERVAL"
chmod +x "$ROOT/deploy/autopull.sh"

# Wybierz właściciela deployu (kto odpala) -- ten, kto jest właścicielem repo.
OWNER="$(stat -c '%U' "$ROOT")"
echo "==> Deploy będzie biegł jako użytkownik: $OWNER"

cat > /etc/systemd/system/gield-autodeploy.service <<UNIT
[Unit]
Description=GielDarek auto-deploy (pull + deploy on new commit)
After=docker.service network-online.target
Wants=docker.service network-online.target

[Service]
Type=oneshot
User=$OWNER
WorkingDirectory=$ROOT
ExecStart=$ROOT/deploy/autopull.sh
UNIT

cat > /etc/systemd/system/gield-autodeploy.timer <<UNIT
[Unit]
Description=GielDarek auto-deploy co $INTERVAL

[Timer]
OnBootSec=2min
OnUnitActiveSec=$INTERVAL
Unit=gield-autodeploy.service

[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now gield-autodeploy.timer

echo "==> Zainstalowane. Status timera:"
systemctl list-timers gield-autodeploy.timer --no-pager || true
echo
echo "GOTOWE. Od teraz każdy push na gałąź deployową wdroży się sam w <= $INTERVAL."
echo "  Log wdrożeń:      journalctl -u gield-autodeploy.service -f"
echo "  Wymuś teraz:      sudo systemctl start gield-autodeploy.service"
echo "  Odinstaluj:       sudo systemctl disable --now gield-autodeploy.timer && \\"
echo "                    sudo rm /etc/systemd/system/gield-autodeploy.{service,timer} && \\"
echo "                    sudo systemctl daemon-reload"
