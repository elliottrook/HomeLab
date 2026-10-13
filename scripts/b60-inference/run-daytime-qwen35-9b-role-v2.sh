#!/bin/sh
set -eu

guest=110
news_guest=114
endpoint=http://192.168.70.12:11435
runtime=/dev/shm/b60-qwen35-9b/runtime/llama-b11429
server=$runtime/llama-server
model=/dev/shm/b60-qwen35-9b/model/Qwen3.5-9B-Q4_K_M.gguf
runner=/run/aster_local_role_runner-v2.py
cases=/run/aster-local-role-v2.json
output=/var/lib/b60-inference/evidence/aster-local-role-v2-9b-20261010.json
accepted_binary_sha=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
accepted_unit_sha=e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184
model_sha=cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13
runner_sha=15db3db86f7ac42cc444386b35fb1b62b60d4eda12ab2710f0bab62ed0902a1b
cases_sha=f16974de558a62321c4d439f504aa6805659381b3b43320d59afbc526dca40b2

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
test "$(pct exec "$guest" -- sha256sum "$model" | awk '{print $1}')" = "$model_sha"
test "$(pct exec "$news_guest" -- sha256sum "$runner" | awk '{print $1}')" = "$runner_sha"
test "$(pct exec "$news_guest" -- sha256sum "$cases" | awk '{print $1}')" = "$cases_sha"
pct exec "$news_guest" -- test ! -e "$output"

pct exec "$news_guest" -- systemctl stop news-aggregator-ingest.timer
pct exec "$news_guest" -- systemctl stop news-aggregator-digest.timer
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-ingest.service && exit 1 || true
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-digest.service && exit 1 || true

pct exec "$guest" -- systemctl stop aster-llama.service
sleep 30
pct exec "$guest" -- awk '/MemAvailable/ {if ($2 < 4194304) exit 1}' /proc/meminfo

pct exec "$guest" -- systemd-run --unit=aster-b60-candidate --collect \
    --property=User=ollama --property=Group=ollama \
    --property='SupplementaryGroups=video render' --service-type=simple -- \
    /usr/bin/env "LD_LIBRARY_PATH=$runtime" "$server" -m "$model" -ngl 999 \
    -c 8192 -np 1 -t 4 -tb 4 -b 256 -ub 128 -fa on -ctk q4_0 -ctv q4_0 \
    --jinja --reasoning off --reasoning-budget 0 \
    --chat-template-kwargs '{"enable_thinking":false}' \
    --host 192.168.70.12 --port 11435 --api-key-file /etc/aster-llama-api-keys --metrics

wait_for_health aster-b60-candidate.service
pct exec "$news_guest" -- python3 "$runner" --endpoint "$endpoint" \
    --api-key-file /root/.news-aggregator-llama-key --cases "$cases" \
    --label qwen35-9b-q4km --output "$output"
pct exec "$guest" -- awk '/MemAvailable/ {if ($2 < 4194304) exit 1}' /proc/meminfo
