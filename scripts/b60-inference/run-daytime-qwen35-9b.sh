#!/bin/sh
set -eu

guest=110
news_guest=114
endpoint=http://192.168.70.12:11435
runtime=/dev/shm/b60-qwen35-9b/runtime/llama-b11429
server=$runtime/llama-server
bench=$runtime/llama-bench
model=/dev/shm/b60-qwen35-9b/model/Qwen3.5-9B-Q4_K_M.gguf
runner=/run/b60-runner-v3.pyz
fixtures=/run/b60-synthetic-fixtures-v2.json
evidence=/var/lib/b60-inference/evidence/qwen35-9b-20261010
accepted_binary_sha=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
accepted_unit_sha=e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184

wait_for_health() {
    unit=$1
    attempt=0
    while [ "$attempt" -lt 60 ]; do
        if pct exec "$guest" -- systemctl is-active --quiet "$unit" &&
           pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    return 1
}

restore() {
    status=$?
    trap - EXIT HUP INT TERM
    pct exec "$guest" -- systemctl stop aster-b60-candidate.service 2>/dev/null || true
    pct exec "$guest" -- systemctl reset-failed aster-b60-candidate.service 2>/dev/null || true
    pct exec "$guest" -- systemctl stop aster-llama.service 2>/dev/null || true
    sleep 30
    pct exec "$guest" -- systemctl start --no-block aster-llama.service || true
    wait_for_health aster-llama.service || status=1
    pct exec "$news_guest" -- systemctl start news-aggregator-ingest.timer || status=1
    pct exec "$news_guest" -- systemctl start news-aggregator-digest.timer || status=1
    exit "$status"
}

trap restore EXIT HUP INT TERM

test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$accepted_binary_sha"
test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = "$accepted_unit_sha"
pct exec "$guest" -- test -x "$server"
pct exec "$guest" -- test -x "$bench"
pct exec "$guest" -- test -s "$model"
pct exec "$news_guest" -- test -s "$runner"
pct exec "$news_guest" -- test -s "$fixtures"

pct exec "$news_guest" -- systemctl stop news-aggregator-ingest.timer
pct exec "$news_guest" -- systemctl stop news-aggregator-digest.timer
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-ingest.service && exit 1 || true
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-digest.service && exit 1 || true

pct exec "$guest" -- systemctl stop aster-llama.service
sleep 30

available_kib=$(pct exec "$guest" -- awk '/MemAvailable/ {print $2}' /proc/meminfo)
test "$available_kib" -ge 4194304

pct exec "$guest" -- mkdir -p "$evidence"
pct exec "$guest" -- sh -c "test ! -e '$evidence/llama-bench.json'"
pct exec "$guest" -- sh -c \
    "LD_LIBRARY_PATH='$runtime' '$bench' -m '$model' -ngl 999 -p 512,4096 -n 128 -b 256 -ub 128 -t 4 -ctk q4_0 -ctv q4_0 -fa on -r 5 -o json > '$evidence/llama-bench.json'"
pct exec "$guest" -- chmod 0600 "$evidence/llama-bench.json"

pct exec "$guest" -- systemd-run --unit=aster-b60-candidate --collect \
    --property=User=ollama --property=Group=ollama \
    --property='SupplementaryGroups=video render' --service-type=simple -- \
    /usr/bin/env "LD_LIBRARY_PATH=$runtime" "$server" -m "$model" -ngl 999 \
    -c 8192 -np 1 -t 4 -tb 4 -b 256 -ub 128 -fa on -ctk q4_0 -ctv q4_0 \
    --jinja --reasoning off --reasoning-budget 0 \
    --chat-template-kwargs '{"enable_thinking":false}' \
    --host 192.168.70.12 --port 11435 --api-key-file /etc/aster-llama-api-keys --metrics

wait_for_health aster-b60-candidate.service

for fixture in aster-conversation aster-persona aster-read-only-tool aster-grounded-retrieval; do
    output="/var/lib/b60-inference/evidence/qwen35-9b-20261010-${fixture}.json"
    pct exec "$news_guest" -- test ! -e "$output"
    pct exec "$news_guest" -- python3 "$runner" --fixtures "$fixtures" \
        --fixture "$fixture" --endpoint "$endpoint" \
        --api-key-file /root/.news-aggregator-llama-key --output "$output" \
        --execute --allow-production-endpoint
    pct exec "$news_guest" -- python3 -c \
        "import json; d=json.load(open('$output')); assert all(x['correct'] for x in d['samples'])"
done

pct exec "$guest" -- awk '/MemAvailable/ {if ($2 < 4194304) exit 1}' /proc/meminfo
