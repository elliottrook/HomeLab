#!/bin/sh
# Run in LXC 115 after approval, with reviewed files staged at /opt/paperless-summary.
set -eu
root=/opt/paperless-summary
for file in gateway.py django_bridge.py broker_contract.py worker.py pipeline.py config.example.json; do
    test -f "$root/$file"
done
if ! getent passwd paperless-summary >/dev/null; then
    useradd --system --home-dir /var/lib/paperless-summary --shell /usr/sbin/nologin paperless-summary
fi
test "$(id -Gn paperless-summary)" = paperless-summary
install -d -o root -g paperless-summary -m 0750 /etc/paperless-summary
# Stop rather than replacing an operator-owned configuration.
test ! -e /etc/paperless-summary/config.json
install -o root -g paperless-summary -m 0640 "$root/config.example.json" /etc/paperless-summary/config.json
chown -R root:root "$root"
chmod -R go-w "$root"
install -o root -g root -m 0644 "$root"/systemd/*.service "$root"/systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/paperless-summary-broker.service /etc/systemd/system/paperless-summary.service /etc/systemd/system/paperless-summary.timer
# Activation follows explicit credential transfer and prerequisite validation.
