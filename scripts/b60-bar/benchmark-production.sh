#!/bin/sh
# Matched historical-suite comparison; no model/service/boot changes.
set -eu
run=/run/b60-bar-performance
out=/var/lib/b60-inference/evidence/bar-full-20261010
restore() {
 status=$?
 trap - EXIT HUP INT TERM
 pct exec 114 -- systemctl start news-aggregator-ingest.timer || status=1
 pct exec 114 -- systemctl start news-aggregator-digest.timer || status=1
 exit "$status"
}
test "$(pct exec 110 -- sha256sum /etc/systemd/system/aster-llama.service | awk '{print $1}')" = 6b09f4580ef49b1c61532d22f48cc5091ec95a0e823f73893db7a83f5c1a461e
test "$(pct exec 110 -- sha256sum /opt/llama.cpp-b11429/llama-server | awk '{print $1}')" = 5faf410bbbc00a1b94b09ee01623699f255365628dfa73b1ee552d9e52a2231d
test "$(pct exec 114 -- sha256sum "$run/aster_analysis_summary_runner.py" | awk '{print $1}')" = a806e10d8459d7e9990a056ffceded1603bfde1ed50fa75d5dad174fbad669f1
test "$(pct exec 114 -- sha256sum "$run/aster-analysis-role-v1.json" | awk '{print $1}')" = ca1ecae58cd588b2251ff0c5ef10d36f0fe13ff3fec05e4f194d58b67c8767bd
pct exec 114 -- test ! -e "$out-5.json"
trap restore EXIT HUP INT TERM
pct exec 114 -- systemctl stop news-aggregator-ingest.timer news-aggregator-digest.timer
for service in news-aggregator-ingest.service news-aggregator-digest.service; do
 if pct exec 114 -- systemctl is-active --quiet "$service"; then exit 1; fi
done
for rep in warmup 1 2 3 4 5; do
 pct exec 110 -- systemctl is-active --quiet aster-llama.service
 pct exec 110 -- curl -fsS --max-time 10 http://192.168.70.12:11435/health
 if journalctl -b -k --no-pager | grep -Eiq 'GPU HANG|wedged|device lost|DMAR.*(fault|error)|IOMMU.*[[:space:]]fault|Out of memory|oom-kill|BUG:|Oops:'; then exit 1; fi
 # Runner's correctness exit is recorded; fail on runtime/missing evidence below.
 pct exec 114 -- timeout 180 python3 "$run/aster_analysis_summary_runner.py" \
  --endpoint http://192.168.70.12:11435 --api-key-file /root/.news-aggregator-llama-key \
  --cases "$run/aster-analysis-role-v1.json" --label "full-bar-production-$rep" \
  --output "$out-$rep.json" --max-tokens 256 || {
   pct exec 114 -- test -s "$out-$rep.json" || exit 1
  }
 pct exec 114 -- python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); assert all(r["elapsed_seconds"] is not None for r in d["results"]); assert d["pass_count"] >= 12; assert {r["id"] for r in d["results"] if not r["passed"]} <= {"stale-news", "contradictory-sources", "missing-evidence", "private-public-join"}' "$out-$rep.json"
done
