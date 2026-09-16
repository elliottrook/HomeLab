#!/usr/bin/env bash
# setup-vault.sh — one-time setup for the credential-broker pattern.
# Run as root (or your operator account with sudo) on the control-plane
# host, e.g. a small unprivileged LXC on the T5810.
set -euo pipefail

AGENT_USER="hlabagent"   # runs Claude Code / the agent — never touches secrets
VAULT_USER="hlabvault"   # owns every credential — nothing else can read it
REGISTRY_DIR="/etc/homelab-broker"     # non-secret: aliases -> hostnames/users
VAULT_DIR="/var/lib/homelab-broker/vault"  # secret: aliases -> keys

# 1. Create the two service users (no login shell needed for the vault user).
id -u "$AGENT_USER" &>/dev/null || useradd -r -m -s /bin/bash "$AGENT_USER"
id -u "$VAULT_USER"  &>/dev/null || useradd -r -m -s /usr/sbin/nologin "$VAULT_USER"

# 2. Non-secret registry: alias -> host/user/port. Safe to put in git.
mkdir -p "$REGISTRY_DIR"
chown root:root "$REGISTRY_DIR"
chmod 755 "$REGISTRY_DIR"
[ -f "$REGISTRY_DIR/hosts.json" ] || echo '{}' > "$REGISTRY_DIR/hosts.json"

# 3. Secret vault: alias -> private key. Owned solely by the vault user, 700.
mkdir -p "$VAULT_DIR"
chown "$VAULT_USER":"$VAULT_USER" "$VAULT_DIR"
chmod 700 "$VAULT_DIR"

# 4. Install the broker binary and lock down its permissions.
install -o root -g root -m 755 ./hb-connect /usr/local/bin/hb-connect

# 5. Install the sudoers rule (the actual trust boundary).
visudo -cf ./etc-sudoers.d-homelab-broker
install -o root -g root -m 440 ./etc-sudoers.d-homelab-broker /etc/sudoers.d/homelab-broker

echo "Done. Register a host with: sudo -u $VAULT_USER hb-connect --add <alias> <user@host>"
echo "Agent user '$AGENT_USER' can now run: sudo -u $VAULT_USER hb-connect run <alias> \"<command>\""
