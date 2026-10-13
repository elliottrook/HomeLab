#!/bin/sh
set -eu

guest=104
agent=/opt/aster-agent/aster_agent.py
lab=/opt/aster-agent/lab_operations.py
agent_candidate=/run/aster_agent.metadata-candidate.py
lab_candidate=/run/lab_operations.metadata-candidate.py
agent_backup=/opt/aster-agent/aster_agent.py.pre-9b-metadata-20261010
lab_backup=/opt/aster-agent/lab_operations.py.pre-9b-metadata-20261010
agent_before=f2c45986a9201d0fe01024a8ac47962600633f6bfa979972bf700762e2e3308f
lab_before=0730cd25575ce2b0c5c632e8b106fd3d48cb03cf0a64df9c44e275238d4e4499
agent_after=a58349341487f137a8de0b746fdf602ddf21abbeeb60caa78dccf4a06dd4fb5f
lab_after=9a3d7f9c0a35952693bc39c4fc7b36d85f1b7d10060856859bbaf3ad7e7203af
armed=0

rollback() {
    status=$?
    trap - EXIT HUP INT TERM
    if [ "$armed" -eq 1 ]; then
        pct exec "$guest" -- install -o root -g root -m 0644 "$agent_backup" "$agent" || true
        pct exec "$guest" -- install -o root -g root -m 0644 "$lab_backup" "$lab" || true
        pct exec "$guest" -- systemctl restart aster-agent.service || true
        pct exec "$guest" -- systemctl is-active --quiet aster-agent.service || status=1
    fi
    exit "$status"
}

test "$(pct exec "$guest" -- sha256sum "$agent" | awk '{print $1}')" = "$agent_before"
test "$(pct exec "$guest" -- sha256sum "$lab" | awk '{print $1}')" = "$lab_before"
test "$(pct exec "$guest" -- sha256sum "$agent_candidate" | awk '{print $1}')" = "$agent_after"
test "$(pct exec "$guest" -- sha256sum "$lab_candidate" | awk '{print $1}')" = "$lab_after"
pct exec "$guest" -- test ! -e "$agent_backup"
pct exec "$guest" -- test ! -e "$lab_backup"
pct exec "$guest" -- install -o root -g root -m 0644 "$agent" "$agent_backup"
pct exec "$guest" -- install -o root -g root -m 0644 "$lab" "$lab_backup"
armed=1
trap rollback EXIT HUP INT TERM
pct exec "$guest" -- install -o root -g root -m 0644 "$agent_candidate" "$agent"
pct exec "$guest" -- install -o root -g root -m 0644 "$lab_candidate" "$lab"
pct exec "$guest" -- systemctl restart aster-agent.service
pct exec "$guest" -- systemctl is-active --quiet aster-agent.service
test "$(pct exec "$guest" -- sha256sum "$agent" | awk '{print $1}')" = "$agent_after"
test "$(pct exec "$guest" -- sha256sum "$lab" | awk '{print $1}')" = "$lab_after"
trap - EXIT HUP INT TERM
