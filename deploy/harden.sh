#!/usr/bin/env bash
# One-shot server hardening for the GielDarek VPS (Debian/Ubuntu).
# Idempotent -- safe to re-run. Does NOT touch the trading app or its data.
#
# What it does:
#   1. ufw firewall: allow SSH + 80/443 (+ 8000 dashboard), deny everything else
#   2. fail2ban: bans IPs brute-forcing SSH
#   3. unattended-upgrades: automatic security patches
#   4. SSH hardening: disable root password login + password auth -- ONLY if a
#      key is already installed (guards against locking yourself out)
#   5. .env permissions: 600 (owner-only) so keys aren't world-readable
#
# Usage (on the VPS, as root):
#   cd ~/gie-d && bash deploy/harden.sh
#
# IMPORTANT: before this disables password login, make sure you can SSH with a
# key. If you don't have one yet, from your Mac run:
#   ssh-keygen -t ed25519            # if you don't already have a key
#   ssh-copy-id root@46.225.229.113  # installs it on the server
# then re-run this script.

set -euo pipefail
GIE_D_DIR="${GIE_D_DIR:-$HOME/gie-d}"
DASHBOARD_PORT="${DASHBOARD_PORT:-8000}"

log() { printf '\n\033[1;36m== %s ==\033[0m\n' "$1"; }

log "1/5 Firewall (ufw)"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ufw >/dev/null
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
# Dashboard direct port -- keep it open for now so you don't lose access before
# HTTPS/Caddy is set up. Once Caddy is in front (see deploy/README-hardening.md)
# remove this line and bind the app to localhost.
ufw allow "${DASHBOARD_PORT}/tcp"
ufw --force enable
ufw status verbose

log "2/5 fail2ban (SSH brute-force protection)"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq fail2ban >/dev/null
cat > /etc/fail2ban/jail.d/sshd.local <<'EOF'
[sshd]
enabled = true
maxretry = 5
bantime = 1h
findtime = 10m
EOF
systemctl enable fail2ban >/dev/null 2>&1 || true
systemctl restart fail2ban
echo "fail2ban aktywny."

log "3/5 Automatyczne aktualizacje bezpieczeństwa"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq unattended-upgrades >/dev/null
echo 'APT::Periodic::Update-Package-Lists "1";' > /etc/apt/apt.conf.d/20auto-upgrades
echo 'APT::Periodic::Unattended-Upgrade "1";' >> /etc/apt/apt.conf.d/20auto-upgrades
echo "unattended-upgrades włączone."

log "4/5 Hardening SSH"
KEYS_FILE="${HOME}/.ssh/authorized_keys"
if [[ -s "$KEYS_FILE" ]]; then
  mkdir -p /etc/ssh/sshd_config.d
  cat > /etc/ssh/sshd_config.d/99-harden.conf <<'EOF'
PasswordAuthentication no
PermitRootLogin prohibit-password
PubkeyAuthentication yes
ChallengeResponseAuthentication no
X11Forwarding no
MaxAuthTries 4
EOF
  if sshd -t; then
    systemctl reload ssh 2>/dev/null || systemctl reload sshd 2>/dev/null || true
    echo "SSH: logowanie hasłem WYŁĄCZONE (tylko klucz)."
  else
    rm -f /etc/ssh/sshd_config.d/99-harden.conf
    echo "!! sshd config test nie przeszedł -- cofnięto, hasło NADAL działa."
  fi
else
  echo "!! POMINIĘTO: brak klucza w $KEYS_FILE."
  echo "   Najpierw z Maca: ssh-copy-id root@46.225.229.113, potem odpal ten skrypt ponownie."
fi

log "5/5 Uprawnienia .env"
if [[ -f "${GIE_D_DIR}/.env" ]]; then
  chmod 600 "${GIE_D_DIR}/.env"
  echo ".env ustawione na 600 (tylko właściciel)."
else
  echo "Brak ${GIE_D_DIR}/.env -- pomijam."
fi

log "GOTOWE"
echo "Firewall, fail2ban, auto-updates i uprawnienia .env skonfigurowane."
echo "Następny krok (HTTPS): deploy/README-hardening.md"
