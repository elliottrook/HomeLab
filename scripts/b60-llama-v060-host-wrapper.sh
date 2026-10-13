#!/bin/sh
set -eu

guest=110
runner=/usr/local/sbin/b60-llama-v060-experiment
host_result=/var/log/b60-llama-v060-experiment
start_epoch="$(date +%s)"

mkdir -p "$host_result"
chmod 0700 "$host_result"

restore() {
    pct exec "$guest" -- systemctl start aster-llama.service || true
}
trap restore EXIT HUP INT TERM

journalctl -k --since "@$start_epoch" --no-pager >"$host_result/kernel.log"
pct exec "$guest" -- "$runner"
journalctl -k --since "@$start_epoch" --no-pager >"$host_result/kernel.log"

if grep -Eqi 'xe.*(reset|wedged|fault)|out of memory|oom-killer|device lost' "$host_result/kernel.log"; then
    echo "GPU/OOM hazard detected; candidate rejected" >"$host_result/ABORTED"
    exit 1
fi

pct exec "$guest" -- systemctl is-active --quiet aster-llama.service
date -u +%FT%TZ >"$host_result/COMPLETE"
trap - EXIT HUP INT TERM
