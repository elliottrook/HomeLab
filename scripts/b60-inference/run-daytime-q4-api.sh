#!/bin/sh
set -eu

endpoint=http://192.168.70.12:11435
runner=/run/b60-runner-v3.pyz
fixtures=/run/b60-synthetic-fixtures-v2.json
server=/opt/llama.cpp-b11081/llama-server
model=/opt/models/qwen3.8-27b-iq4xs/Qwen3.8-27B-UD-IQ4_XS-00001-of-00002.gguf

restore() {
    pct exec 110 -- systemctl stop aster-b60-candidate.service 2>/dev/null || true
    pct exec 110 -- systemctl reset-failed aster-b60-candidate.service 2>/dev/null || true
    pct exec 110 -- systemctl start --no-block aster-llama.service || true
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        if pct exec 110 -- systemctl is-active --quiet aster-llama.service &&
           pct exec 110 -- curl -fsS "$endpoint/health" >/dev/null; then
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
pct exec 110 -- systemd-run --unit=aster-b60-candidate --collect \
    --property=User=ollama --property=Group=ollama \
    --property='SupplementaryGroups=video render' --service-type=simple -- \
    "$server" -m "$model" -ngl 999 -c 8192 -np 1 -t 4 -tb 4 -b 256 -ub 128 \
    -fa on -ctk q4_0 -ctv q4_0 --jinja --reasoning off --reasoning-budget 0 \
    --host 192.168.70.12 --port 11435 --api-key-file /etc/aster-llama-api-keys --metrics

attempt=0
while [ "$attempt" -lt 60 ]; do
    if pct exec 110 -- systemctl is-active --quiet aster-b60-candidate.service &&
       pct exec 110 -- curl -fsS "$endpoint/health" >/dev/null; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 5
done
test "$attempt" -lt 60

if [ "$#" -eq 0 ]; then
    set -- /var/lib/b60-inference/evidence/2026-10-10-calibrated-aster512-q4-cold.json aster-conversation
fi
test $(( $# % 2 )) -eq 0
while [ "$#" -gt 0 ]; do
    output=$1
    fixture=$2
    shift 2
    pct exec 114 -- python3 "$runner" --fixtures "$fixtures" \
        --fixture "$fixture" --endpoint "$endpoint" \
        --api-key-file /root/.news-aggregator-llama-key --output "$output" \
        --execute --allow-production-endpoint
done
