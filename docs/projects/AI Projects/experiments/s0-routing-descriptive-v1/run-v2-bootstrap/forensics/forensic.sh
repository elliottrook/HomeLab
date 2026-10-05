#!/bin/bash
set -euo pipefail

SOURCE=/dev/pve/vm-118-disk-0
SOURCE_REAL="$(readlink -f "$SOURCE")"
MOUNT=/mnt/aster-s0-v2-forensic
EVIDENCE=/var/lib/vz/template/cache/aster-s0-20260926/run-v2/forensics
LOOP_DEVICE=

cleanup() {
  local rc=$?
  trap - EXIT INT TERM HUP
  if mountpoint -q "$MOUNT"; then
    umount "$MOUNT" || rc=90
  fi
  if [ -n "$LOOP_DEVICE" ] && losetup "$LOOP_DEVICE" >/dev/null 2>&1; then
    losetup --detach "$LOOP_DEVICE" || rc=91
  fi
  rmdir "$MOUNT" 2>/dev/null || true
  exit "$rc"
}
trap cleanup EXIT INT TERM HUP

[ "$(qm status 118)" = "status: stopped" ]
[ "$(blockdev --getsize64 "$SOURCE")" = 8589934592 ]
[ -z "$(findmnt -rn -S "$SOURCE")" ]
[ ! -e "$MOUNT" ]
[ ! -e "$EVIDENCE" ]

install -d -m 0700 "$MOUNT" "$EVIDENCE"
LOOP_DEVICE="$(losetup --find --show --read-only --partscan "$SOURCE")"
udevadm settle
[ "$(blockdev --getro "$LOOP_DEVICE")" = 1 ]

ROOT="${LOOP_DEVICE}p1"
[ -b "$ROOT" ]
[ "$(blockdev --getro "$ROOT")" = 1 ]
partx --show --output NR,START,SECTORS,UUID "$LOOP_DEVICE" > "$EVIDENCE/partition-table.txt"
grep -Eq '^ *1 +262144 +16515039 +6bb09544-3ae5-42bc-8660-47d62a9f894d$' "$EVIDENCE/partition-table.txt"

losetup --list --output NAME,BACK-FILE,RO "$LOOP_DEVICE" > "$EVIDENCE/loop-receipt.txt"
grep -Fq "$SOURCE_REAL" "$EVIDENCE/loop-receipt.txt"
grep -Eq ' +1$' "$EVIDENCE/loop-receipt.txt"
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,RO "$LOOP_DEVICE" > "$EVIDENCE/lsblk-before-mount.txt"
dumpe2fs -h "$ROOT" 2>/dev/null | grep -E '^(Filesystem UUID|Filesystem state|Filesystem features|Last mount time|Last write time):' > "$EVIDENCE/filesystem-state.txt"

mount -t ext4 -o ro,noload,nosuid,nodev,noexec "$ROOT" "$MOUNT"
findmnt -rn -o SOURCE,FSTYPE,OPTIONS --target "$MOUNT" > "$EVIDENCE/mount-receipt.txt"
grep -Fq 'ro,' "$EVIDENCE/mount-receipt.txt"
grep -Eq '(noload|norecovery)' "$EVIDENCE/mount-receipt.txt"
grep -Fq 'nosuid' "$EVIDENCE/mount-receipt.txt"
grep -Fq 'nodev' "$EVIDENCE/mount-receipt.txt"
grep -Fq 'noexec' "$EVIDENCE/mount-receipt.txt"

UNIT="$MOUNT/etc/systemd/system/aster-s0-canary.service"
CANARY="$MOUNT/usr/local/lib/aster-s0/canary.py"
PAYLOAD="$MOUNT/usr/local/lib/aster-s0/payload-manifest.json"
for file in "$UNIT" "$CANARY" "$PAYLOAD"; do
  [ -f "$file" ]
  stat -c '%n %s %a %u:%g' "$file"
  sha256sum "$file"
done > "$EVIDENCE/generated-artifacts.txt"

grep -Fq 'f105dc8a3a8dbbab339cc492f7f36c1f09779d88ea35566084cb96555c201a0d' "$EVIDENCE/generated-artifacts.txt"
grep -Fq '7c8295cdd39d5d2133decb522da22047b4cffd87195068735070b072a4c2b321' "$EVIDENCE/generated-artifacts.txt"
grep -Fq '20ede161a4783101dba418a124493a5c5860f404d9959674a122cae527b7cbe3' "$EVIDENCE/generated-artifacts.txt"

RESULT="$MOUNT/var/lib/aster-s0/output/result.json"
if [ -e "$RESULT" ]; then
  [ -f "$RESULT" ]
  RESULT_SIZE="$(stat -c %s "$RESULT")"
  [ "$RESULT_SIZE" -le 2097152 ]
  stat -c '%n %s %a %u:%g' "$RESULT" > "$EVIDENCE/result-metadata.txt"
  sha256sum "$RESULT" >> "$EVIDENCE/result-metadata.txt"
  install -m 0600 "$RESULT" "$EVIDENCE/result.json"
else
  printf '%s\n' absent > "$EVIDENCE/result-metadata.txt"
fi

if [ -d "$MOUNT/var/log/journal" ]; then
  journalctl --directory="$MOUNT/var/log/journal" --unit=aster-s0-canary.service \
    --no-pager -n 100 --output=json | python3 -c '
import json,sys
keys=("__REALTIME_TIMESTAMP","_SYSTEMD_UNIT","PRIORITY","SYSLOG_IDENTIFIER","_PID","MESSAGE")
for line in sys.stdin:
    row=json.loads(line)
    print(json.dumps({key:row[key] for key in keys if key in row},sort_keys=True,ensure_ascii=True))
' > "$EVIDENCE/canary-journal.jsonl"
else
  : > "$EVIDENCE/canary-journal.jsonl"
fi

for log in "$MOUNT/var/log/cloud-init.log" "$MOUNT/var/log/cloud-init-output.log"; do
  if [ -f "$log" ]; then
    grep -a -i 'aster-s0-canary' "$log" | tail -n 100
  fi
done > "$EVIDENCE/cloud-init-canary-lines.txt" || true

sha256sum "$EVIDENCE"/* > "$EVIDENCE/evidence-sha256.txt.part"
mv "$EVIDENCE/evidence-sha256.txt.part" "$EVIDENCE/evidence-sha256.txt"
printf 'forensic_collection=complete\nloop=%s\nroot=%s\n' "$LOOP_DEVICE" "$ROOT"
