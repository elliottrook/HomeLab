#!/bin/bash
set -euo pipefail
umask 077

VMID=119
BASE=/var/lib/vz/template/cache/aster-s0-20260926
SEED_SOURCE="$BASE/seed-source-v1"
RELEASE="$BASE/release-v1b"
RUN="$BASE/run-v2b"
CAPTURE="$RUN/serial.capture"

fail() { printf 'run_v2b=failed\nreason=%s\n' "$1" >&2; exit 1; }
[ -d "$RELEASE" ] || fail release-evidence-absent
[ ! -e "$RUN" ] || fail run-path-exists
[ "$(qm status "$VMID")" = 'status: stopped' ] || fail initial-state
qm config "$VMID" --current | python3 "$SEED_SOURCE/s0_vm_release.py" - >/dev/null || fail config-gate
ISO_DIGEST="$(awk '{print $1}' "$RELEASE/seed-iso.sha256")"
[ "$(sha256sum /var/lib/vz/template/iso/aster-s0-bootstrap-canary-002.iso | awk '{print $1}')" = "$ISO_DIGEST" ] || fail iso-drift

install -d -m 0700 "$RUN"
date --iso-8601=seconds > "$RUN/start-time.txt"
qm list > "$RUN/qm-list-before.txt"
pct list > "$RUN/pct-list-before.txt"
qm start "$VMID"
set +e
timeout --signal=TERM --kill-after=10s 300s script --quiet --flush --return \
  --command "qm terminal $VMID" "$CAPTURE"
CAPTURE_RC=$?
set -e
printf '%s\n' "$CAPTURE_RC" > "$RUN/capture-exit-code.txt"
FINAL_STATE="$(qm status "$VMID")"
if [ "$FINAL_STATE" != 'status: stopped' ]; then
  qm stop "$VMID"
  FINAL_STATE="$(qm status "$VMID")"
  printf '%s\n' forced > "$RUN/host-stop.txt"
else
  printf '%s\n' not-required > "$RUN/host-stop.txt"
fi
[ "$FINAL_STATE" = 'status: stopped' ] || fail final-state
[ -f "$CAPTURE" ] || fail capture-absent
CAPTURE_BYTES="$(stat -c %s "$CAPTURE")"
[ "$CAPTURE_BYTES" -le 4194304 ] || fail capture-oversize
sha256sum "$CAPTURE" > "$RUN/serial.capture.sha256"
printf 'capture_bytes=%s\n' "$CAPTURE_BYTES" > "$RUN/capture-size.txt"
qm config "$VMID" --current > "$RUN/qm-config-after.txt"
qm list > "$RUN/qm-list-after.txt"
pct list > "$RUN/pct-list-after.txt"
sha256sum "$RUN"/* > "$RUN/evidence-sha256.txt.part"
mv "$RUN/evidence-sha256.txt.part" "$RUN/evidence-sha256.txt"
[ "$CAPTURE_RC" -eq 0 ] || fail capture-command
printf 'run_v2b=capture-complete\nvmid=%s\nstate=stopped\n' "$VMID"
