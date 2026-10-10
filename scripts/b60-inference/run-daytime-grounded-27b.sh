#!/bin/sh
set -eu

guest=110
news_guest=114
endpoint=http://192.168.70.12:11435
runner=/run/evals/aster_grounded_analysis_runner.py
policy=/run/local_orchestrator.py
cases=/run/aster-grounded-analysis-v2.json
output=/var/lib/b60-inference/evidence/aster-grounded-v2-27b-20261010.json
accepted_binary_sha=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
accepted_unit_sha=e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184
runner_sha=00a63cf6a8b15f46b6c76b800e86af74bbef9172b9a1361c6f3acb506455ce1f
policy_sha=fc019089bcd6ef168a040b9651086f420a696eeb842d1d4af9ab11846fe143fe
cases_sha=e31afa6e0b5051827ff7a31c2fcd9704eeb7214a35583d178b3150b3b951db96

restore_timers() {
    status=$?
    trap - EXIT HUP INT TERM
    pct exec "$news_guest" -- systemctl start news-aggregator-ingest.timer || status=1
    pct exec "$news_guest" -- systemctl start news-aggregator-digest.timer || status=1
    exit "$status"
}
trap restore_timers EXIT HUP INT TERM

test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$accepted_binary_sha"
test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = "$accepted_unit_sha"
test "$(pct exec "$news_guest" -- sha256sum "$runner" | awk '{print $1}')" = "$runner_sha"
test "$(pct exec "$news_guest" -- sha256sum "$policy" | awk '{print $1}')" = "$policy_sha"
test "$(pct exec "$news_guest" -- sha256sum "$cases" | awk '{print $1}')" = "$cases_sha"
pct exec "$news_guest" -- test ! -e "$output"
pct exec "$guest" -- systemctl is-active --quiet aster-llama.service
pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null

pct exec "$news_guest" -- systemctl stop news-aggregator-ingest.timer
pct exec "$news_guest" -- systemctl stop news-aggregator-digest.timer
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-ingest.service && exit 1 || true
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-digest.service && exit 1 || true

pct exec "$news_guest" -- python3 "$runner" --endpoint "$endpoint" \
    --api-key-file /root/.news-aggregator-llama-key --cases "$cases" \
    --label qwen3.8-27b-grounded-v2-json --output "$output" --max-tokens 256
