#!/bin/sh
set -eu

guest=110
unit=/etc/systemd/system/aster-llama.service
backup=/etc/systemd/system/aster-llama.service.pre-q4-20261010
expected_unit=7e3e2d9a4c7d861b18ad2c9c83dc294893ea81f295a25918f76fcf3e0f9c9013
expected_binary=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
endpoint=http://192.168.70.12:11435
evidence=/var/lib/b60-inference/evidence/2026-10-10-q4-post-promotion.json
promoted=0

wait_for_health() {
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        if pct exec "$guest" -- systemctl is-active --quiet aster-llama.service &&
           pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    return 1
}

rollback() {
    status=$?
    trap - EXIT HUP INT TERM
    if [ "$promoted" -eq 1 ]; then
        pct exec "$guest" -- cp "$backup" "$unit"
        pct exec "$guest" -- systemctl daemon-reload
        pct exec "$guest" -- systemctl stop aster-llama.service || true
        sleep 30
        pct exec "$guest" -- systemctl start --no-block aster-llama.service || true
        wait_for_health || true
    fi
    exit "$status"
}

trap rollback EXIT HUP INT TERM

test "$(pct exec "$guest" -- sha256sum "$unit" | awk '{print $1}')" = "$expected_unit"
test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$expected_binary"
pct exec "$guest" -- test ! -e "$backup"
pct exec "$guest" -- cp -p "$unit" "$backup"
pct exec "$guest" -- sed \
    -e 's/-ctk q8_0 -ctv q8_0/-ctk q4_0 -ctv q4_0/' \
    "$backup" > /tmp/aster-llama.service.q4
pct push "$guest" /tmp/aster-llama.service.q4 "$unit" --perms 0644
promoted=1

test "$(pct exec "$guest" -- grep -c -- '-ctk q4_0 -ctv q4_0' "$unit")" -eq 1
test "$(pct exec "$guest" -- grep -c -- '-ctk q8_0 -ctv q8_0' "$unit")" -eq 0
pct exec "$guest" -- systemctl daemon-reload
pct exec "$guest" -- systemctl stop aster-llama.service
sleep 30
pct exec "$guest" -- systemctl start --no-block aster-llama.service
wait_for_health

pct exec 114 -- python3 /run/b60-runner-v3.pyz \
    --fixtures /run/b60-synthetic-fixtures-v2.json \
    --fixture aster-conversation --endpoint "$endpoint" \
    --api-key-file /root/.news-aggregator-llama-key --output "$evidence" \
    --execute --allow-production-endpoint
pct exec 114 -- python3 -c \
    'import json; d=json.load(open("/var/lib/b60-inference/evidence/2026-10-10-q4-post-promotion.json")); assert all(x["correct"] for x in d["samples"])'

test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$expected_binary"
test "$(readlink -f /sys/bus/pci/devices/0000:04:00.0/driver)" = /sys/bus/pci/drivers/xe
pct exec "$guest" -- sh -c 'vulkaninfo --summary 2>/dev/null | grep -q "BMG G21"'
pct exec 104 -- curl -fsS http://192.168.70.10:9120/health >/dev/null
pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null

trap - EXIT HUP INT TERM
pct exec "$guest" -- sha256sum "$unit" "$backup"
pct exec 114 -- sha256sum "$evidence"
