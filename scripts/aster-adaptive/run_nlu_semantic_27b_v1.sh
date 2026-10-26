#!/bin/sh
set -eu

guest=110
endpoint=http://192.168.70.12:11435
packet=/tmp/aster-nlu-semantic-v1
output=/tmp/aster-nlu-semantic-27b-v1-result.json
accepted_unit_sha=a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3
accepted_binary_sha=0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5
candidate_binary_sha=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
candidate_model=/opt/models/qwen3.8-27b-iq4xs/Qwen3.8-27B-UD-IQ4_XS-00001-of-00002.gguf
accepted_model=/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf

restore() {
    status=$?
    trap - EXIT HUP INT TERM
    pct exec "$guest" -- systemctl stop aster-b60-candidate.service 2>/dev/null || true
    pct exec "$guest" -- systemctl reset-failed aster-b60-candidate.service 2>/dev/null || true
    pct exec "$guest" -- systemctl start --no-block aster-llama.service || status=1
    attempt=0
    while [ "$attempt" -lt 90 ]; do
        if pct exec "$guest" -- systemctl is-active --quiet aster-llama.service &&
           pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null; then
            break
        fi
        attempt=$((attempt + 1))
        sleep 5
    done
    test "$attempt" -lt 90 || status=1
    test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = "$accepted_unit_sha" || status=1
    test "$(pct exec "$guest" -- sha256sum /opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server | awk '{print $1}')" = "$accepted_binary_sha" || status=1
    pct exec "$guest" -- test -r "$accepted_model" || status=1
    exit "$status"
}
trap restore EXIT HUP INT TERM

test "$(local-ai-lease status | tr -d '[:space:]')" = '{"state":"ready"}'
test "$(pct status "$guest")" = 'status: running'
test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = "$accepted_unit_sha"
test "$(pct exec "$guest" -- sha256sum /opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server | awk '{print $1}')" = "$accepted_binary_sha"
test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$candidate_binary_sha"
pct exec "$guest" -- test -r "$candidate_model"
pct exec "$guest" -- test -r "$accepted_model"
pct exec "$guest" -- test -d "$packet"
pct exec "$guest" -- test ! -e "$output"
pct exec "$guest" -- systemctl is-active --quiet aster-llama.service
! pct exec "$guest" -- systemctl is-active --quiet aster-b60-candidate.service

pct exec "$guest" -- systemctl stop aster-llama.service
sleep 30
pct exec "$guest" -- systemd-run --unit=aster-b60-candidate --collect \
    --property=User=ollama --property=Group=ollama \
    --property='SupplementaryGroups=video render' --service-type=simple -- \
    /opt/llama.cpp-b11081/llama-server -m "$candidate_model" -ngl 999 -c 8192 \
    -np 1 -t 4 -tb 4 -b 256 -ub 128 -fa on -ctk q4_0 -ctv q4_0 --jinja \
    --reasoning off --reasoning-budget 0 --host 192.168.70.12 --port 11435 \
    --api-key-file /etc/aster-llama-api-keys --metrics

attempt=0
while [ "$attempt" -lt 90 ]; do
    if pct exec "$guest" -- systemctl is-active --quiet aster-b60-candidate.service &&
       pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null; then
        break
    fi
    attempt=$((attempt + 1))
    sleep 5
done
test "$attempt" -lt 90

pct exec "$guest" -- sh -c "cd '$packet' && python3 nlu_semantic_development_runner_v1.py \
    --fixture fixtures/nlu-development-v1.json --key-file /etc/aster-llama-api-keys \
    --model aster-qwen3.8-27b --output '$output'"
