#!/bin/sh
set -eu

guest=104
agent=/opt/aster-agent/aster_agent.py
candidate=/run/aster_agent.identity-candidate.py
backup=/opt/aster-agent/aster_agent.py.pre-9b-identity-20261010
before_sha=a58349341487f137a8de0b746fdf602ddf21abbeeb60caa78dccf4a06dd4fb5f
after_sha=a311a020ccf4965e7d1efee43bcbaacfc7b6f95379bba87daaf082eec5ea4b66
armed=0

rollback() {
    status=$?
    trap - EXIT HUP INT TERM
    if [ "$armed" -eq 1 ]; then
        pct exec "$guest" -- install -o root -g root -m 0644 "$backup" "$agent" || true
        pct exec "$guest" -- systemctl restart aster-agent.service || true
        pct exec "$guest" -- systemctl is-active --quiet aster-agent.service || status=1
    fi
    exit "$status"
}

test "$(pct exec "$guest" -- sha256sum "$agent" | awk '{print $1}')" = "$before_sha"
test "$(pct exec "$guest" -- sha256sum "$candidate" | awk '{print $1}')" = "$after_sha"
pct exec "$guest" -- test ! -e "$backup"
pct exec "$guest" -- /opt/aster-agent/venv/bin/python -m py_compile "$candidate"
pct exec "$guest" -- install -o root -g root -m 0644 "$agent" "$backup"
armed=1
trap rollback EXIT HUP INT TERM
pct exec "$guest" -- install -o root -g root -m 0644 "$candidate" "$agent"
pct exec "$guest" -- systemctl restart aster-agent.service
pct exec "$guest" -- systemctl is-active --quiet aster-agent.service
test "$(pct exec "$guest" -- sha256sum "$agent" | awk '{print $1}')" = "$after_sha"
trap - EXIT HUP INT TERM
