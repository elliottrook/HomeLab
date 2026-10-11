#!/bin/sh
set -eu

guest=110
news_guest=114
endpoint=http://192.168.70.12:11435
runner=/run/aster_analysis_summary_runner.py
cases=/run/aster-analysis-role-v1.json
output=/var/lib/b60-inference/evidence/aster-analysis-summary-v2-9b-production-20261010.json
unit_sha=6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e
binary_sha=5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d
model_sha=cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13
runner_sha=a806e10d8459d7e9990a056ffceded1603bfde1ed50fa75d5dad174fbad669f1
cases_sha=ca1ecae58cd588b2251ff0c5ef10d36f0fe13ff3fec05e4f194d58b67c8767bd

restore_timers() {
    status=$?
    trap - EXIT HUP INT TERM
    pct exec "$news_guest" -- systemctl start news-aggregator-ingest.timer || status=1
    pct exec "$news_guest" -- systemctl start news-aggregator-digest.timer || status=1
    exit "$status"
}

test "$(pct exec "$guest" -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = "$unit_sha"
test "$(pct exec "$guest" -- sha256sum /opt/llama.cpp-b11429/llama-server | awk '{print $1}')" = "$binary_sha"
test "$(pct exec "$guest" -- sha256sum /usr/share/ollama/.ollama/models/blobs/sha256-$model_sha | awk '{print $1}')" = "$model_sha"
test "$(pct exec "$news_guest" -- sha256sum "$runner" | awk '{print $1}')" = "$runner_sha"
test "$(pct exec "$news_guest" -- sha256sum "$cases" | awk '{print $1}')" = "$cases_sha"
pct exec "$guest" -- systemctl is-active --quiet aster-llama.service
pct exec "$guest" -- curl -fsS "$endpoint/health" >/dev/null
pct exec "$news_guest" -- test ! -e "$output"

pct exec "$news_guest" -- systemctl stop news-aggregator-ingest.timer
pct exec "$news_guest" -- systemctl stop news-aggregator-digest.timer
trap restore_timers EXIT HUP INT TERM
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-ingest.service && exit 1 || true
pct exec "$news_guest" -- systemctl is-active --quiet news-aggregator-digest.service && exit 1 || true
pct exec "$news_guest" -- python3 "$runner" --endpoint "$endpoint" \
    --api-key-file /root/.news-aggregator-llama-key --cases "$cases" \
    --label qwen35-9b-summary-v2-production --output "$output" --max-tokens 256 || true
