#!/bin/sh
set -eu

bench=/opt/llama.cpp-b11081/llama-bench
model=/opt/models/qwen3.8-27b-iq4xs/Qwen3.8-27B-UD-IQ4_XS-00001-of-00002.gguf
output=/run/b60-b11081-thread-sweep-20261010.json

restore() {
    pct exec 110 -- systemctl start --no-block aster-llama.service || true
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        if pct exec 110 -- systemctl is-active --quiet aster-llama.service &&
           pct exec 110 -- curl -fsS http://192.168.70.12:11435/health >/dev/null; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    echo 'accepted service did not recover' >&2
    return 1
}

trap restore EXIT HUP INT TERM
pct exec 110 -- systemctl stop aster-llama.service
sleep 30
pct exec 110 -- sh -c "$bench -m $model -ngl 999 -p 4096 -n 128 -b 256 -ub 128 -t 2,4,8 -ctk q8_0 -ctv q8_0 -fa on -r 5 -o json >$output"
pct exec 110 -- test -s "$output"
