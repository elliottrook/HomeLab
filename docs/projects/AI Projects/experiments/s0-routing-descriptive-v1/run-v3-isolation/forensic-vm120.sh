#!/bin/bash
set -euo pipefail
umask 077

VMID=120
SOURCE=/dev/pve/vm-120-disk-0
SOURCE_REAL="$(readlink -f "$SOURCE")"
MOUNT=/mnt/aster-s0-v3-forensic
EVIDENCE=/var/lib/vz/template/cache/aster-s0-20260926/run-v3/forensics
VALIDATOR=/var/lib/vz/template/cache/aster-s0-20260926/seed-source-v3/s0_vm_isolation_release.py
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

[ "$(qm status "$VMID")" = 'status: stopped' ]
[ "$(qm status 119)" = 'status: stopped' ]
[ "$(qm status 118)" = 'status: stopped' ]
qm config "$VMID" --current | python3 "$VALIDATOR" - >/dev/null
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
grep -Eiq '^ *1 +262144 +16515039 +6bb09544-3ae5-42bc-8660-47d62a9f894d$' "$EVIDENCE/partition-table.txt"

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

UNIT="$MOUNT/etc/systemd/system/aster-s0-isolation.service"
PROBE="$MOUNT/usr/local/lib/aster-s0/isolation_probe.py"
PAYLOAD="$MOUNT/usr/local/lib/aster-s0/payload-manifest.json"
for file in "$UNIT" "$PROBE" "$PAYLOAD"; do
  [ -f "$file" ]
  [ ! -L "$file" ]
  stat -c '%n %s %a %u:%g' "$file"
  sha256sum "$file"
done > "$EVIDENCE/generated-artifacts.txt"
grep -Fq '5d328814648e47f3b028d2b846a5b3b81fce91b54b694766889a55665f9ced5d' "$EVIDENCE/generated-artifacts.txt"
grep -Fq 'ba4c78c810a432b55abae6eb90a3b77df53e8ce4b71ac25d23233fa8b1a69ec0' "$EVIDENCE/generated-artifacts.txt"
grep -Fq 'da59afcadc25d3ca4707024ad145a8e83d028b2367036d4f990a23d78321b89d' "$EVIDENCE/generated-artifacts.txt"

for name in result.json protocol.txt; do
  file="$MOUNT/var/lib/aster-s0/output/$name"
  if [ -e "$file" ]; then
    [ -f "$file" ]
    [ ! -L "$file" ]
    size="$(stat -c %s "$file")"
    [ "$size" -le 8192 ]
    stat -c '%n %s %a %u:%g' "$file" > "$EVIDENCE/$name.metadata.txt"
    sha256sum "$file" >> "$EVIDENCE/$name.metadata.txt"
    install -m 0600 "$file" "$EVIDENCE/$name"
  else
    printf '%s\n' absent > "$EVIDENCE/$name.metadata.txt"
  fi
done

if [ -d "$MOUNT/var/log/journal" ]; then
  journalctl --directory="$MOUNT/var/log/journal" --unit=aster-s0-isolation.service \
    --no-pager -n 100 --output=json | python3 -c '
import json,sys
keys=("__REALTIME_TIMESTAMP","_SYSTEMD_UNIT","PRIORITY","SYSLOG_IDENTIFIER","_PID","MESSAGE","RESULT","EXIT_CODE","EXIT_STATUS")
for line in sys.stdin:
    row=json.loads(line)
    print(json.dumps({key:row[key] for key in keys if key in row},sort_keys=True,ensure_ascii=True))
' > "$EVIDENCE/isolation-journal.jsonl"
else
  : > "$EVIDENCE/isolation-journal.jsonl"
fi

for log in "$MOUNT/var/log/cloud-init.log" "$MOUNT/var/log/cloud-init-output.log"; do
  if [ -f "$log" ]; then
    grep -a -i 'aster-s0-isolation' "$log" | tail -n 100
  fi
done > "$EVIDENCE/cloud-init-isolation-lines.txt" || true

sha256sum "$EVIDENCE"/* > "$EVIDENCE/evidence-sha256.txt.part"
mv "$EVIDENCE/evidence-sha256.txt.part" "$EVIDENCE/evidence-sha256.txt"
printf 'forensic_collection=complete\nloop=%s\nroot=%s\n' "$LOOP_DEVICE" "$ROOT"
