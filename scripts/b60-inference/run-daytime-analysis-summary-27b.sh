#!/bin/sh
set -eu

guest=110
news_guest=114
endpoint=http://192.168.70.12:11435
runner=/run/aster_analysis_summary_runner.py
cases=/run/aster-analysis-role-v1.json
output=/var/lib/b60-inference/evidence/aster-analysis-summary-v2-27b-20261010.json
accepted_binary_sha=47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693
accepted_unit_sha=e2019cac74dc23deb4bc92efc38cf3a31a9af1b34d43d651c15e507c392fb184
runner_sha=a806e10d8459d7e9990a056ffceded1603bfde1ed50fa75d5dad174fbad669f1
cases_sha=ca1ecae58cd588b2251ff0c5ef10d36f0fe13ff3fec05e4f194d58b67c8767bd

restore() {
    status=$?
    trap - EXIT HUP INT TERM
    pct exec "$news_guest" -- systemctl start news-aggregator-ingest.timer || status=1
    pct exec "$news_guest" -- systemctl start news-aggregator-digest.timer || status=1
    exit "$status"
}

test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11081/llama-server | awk '{print $1}')" = "$accepted_binary_sha"
test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = "$accepted_unit_sha"
test "$(pct exec "$news_guest" -- sha256sum "$runner" | awk '{print $1}')" = "$runner_sha"
test "$(pct exec "$news_guest" -- sha256sum "$cases" | awk '{print $1}')" = "$cases_sha"
pct exec "$guest" -- systemctl is-active --quiet aster-llama.service
pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null
pct exec "$news_guest" -- test ! -e "$output"

trap restore EXIT HUP INT TERM
pct exec "$news_guest" -- systemctl stop news-aggregator-ingest.timer
pct exec "$news_guest" -- systemctl stop news-aggregator-digest.timer
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-ingest.service && exit 1 || true
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-digest.service && exit 1 || true

pct exec "$news_guest" -- python3 "$runner" --endpoint "$endpoint" \
    --api-key-file /root/.news-aggregator-llama-key --cases "$cases" \
    --label qwen38-27b-summary-v2-reasoning-off --output "$output" --max-tokens 256 || true
