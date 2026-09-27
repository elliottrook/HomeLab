#!/bin/bash
set -euo pipefail
umask 077

VMID=122
SOURCE=/dev/pve/vm-122-disk-0
SOURCE_REAL="$(readlink -f "$SOURCE")"
MOUNT=/mnt/aster-s0-v5-forensic
EVIDENCE=/var/lib/vz/template/cache/aster-s0-20260926/run-v5/forensics
STAGE=/var/lib/vz/template/cache/aster-s0-20260926/seed-source-v5
VALIDATOR="$STAGE/s0_vm_corpus_release.py"
LOOP_DEVICE=

cleanup() {
  local rc=$?
  trap - EXIT INT TERM HUP
  if mountpoint -q "$MOUNT"; then umount "$MOUNT" || rc=90; fi
  if [ -n "$LOOP_DEVICE" ] && losetup "$LOOP_DEVICE" >/dev/null 2>&1; then
    losetup --detach "$LOOP_DEVICE" || rc=91
  fi
  rmdir "$MOUNT" 2>/dev/null || true
  exit "$rc"
}
trap cleanup EXIT INT TERM HUP

for id in 118 119 120 121 122; do [ "$(qm status "$id")" = 'status: stopped' ]; done
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

python3 -c '
import hashlib,json,pathlib,sys
mount=pathlib.Path(sys.argv[1]);stage=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3])
candidate=json.loads((stage/"candidate-manifest.json").read_text())
mapping={
 "aster-s0-corpus.service":"etc/systemd/system/aster-s0-corpus.service",
 "corpus_entry.py":"usr/local/lib/aster-s0/corpus_entry.py",
 "payload-manifest.json":"usr/local/lib/aster-s0/payload-manifest.json",
}
for name in ("routing_smoke.py","s0_descriptive.py","s0_vm_corpus_worker.py"):
 mapping["source/"+name]="usr/local/lib/aster-s0/"+name
for name in candidate["files"]:
 if name.startswith("corpus/"):mapping[name]="usr/local/share/aster-s0/"+name
rows=[]
for source,guest in sorted(mapping.items()):
 path=mount/guest
 if not path.is_file() or path.is_symlink():raise SystemExit("artifact-type:"+guest)
 raw=path.read_bytes();expected=candidate["files"][source]
 if len(raw)!=expected["bytes"] or hashlib.sha256(raw).hexdigest()!=expected["sha256"]:raise SystemExit("artifact-drift:"+guest)
 stat=path.stat();rows.append({"guest_path":"/"+guest,"bytes":len(raw),"mode":oct(stat.st_mode & 0o7777),"uid":stat.st_uid,"gid":stat.st_gid,"sha256":expected["sha256"]})
out.write_text(json.dumps({"artifacts":rows,"content_exported":False},sort_keys=True,indent=2)+"\n")
' "$MOUNT" "$STAGE" "$EVIDENCE/generated-artifacts.json"

for name in result.json protocol.txt; do
  file="$MOUNT/var/lib/aster-s0/output/$name"
  limit=2097152; [ "$name" = protocol.txt ] && limit=4194304
  if [ -e "$file" ]; then
    [ -f "$file" ] && [ ! -L "$file" ]
    [ "$(stat -c %s "$file")" -le "$limit" ]
    stat -c '%n %s %a %u:%g' "$file" > "$EVIDENCE/$name.metadata.txt"
    sha256sum "$file" >> "$EVIDENCE/$name.metadata.txt"
    install -m 0600 "$file" "$EVIDENCE/$name"
  else
    printf '%s\n' absent > "$EVIDENCE/$name.metadata.txt"
  fi
done

if [ -d "$MOUNT/var/log/journal" ]; then
  journalctl --directory="$MOUNT/var/log/journal" --unit=aster-s0-corpus.service --no-pager -n 200 --output=json | python3 -c '
import json,sys
keys=("__REALTIME_TIMESTAMP","_SYSTEMD_UNIT","PRIORITY","SYSLOG_IDENTIFIER","_PID","MESSAGE","RESULT","EXIT_CODE","EXIT_STATUS")
for line in sys.stdin:
 row=json.loads(line);print(json.dumps({key:row[key] for key in keys if key in row},sort_keys=True,ensure_ascii=True))
' > "$EVIDENCE/corpus-journal.jsonl"
else
  : > "$EVIDENCE/corpus-journal.jsonl"
fi
for log in "$MOUNT/var/log/cloud-init.log" "$MOUNT/var/log/cloud-init-output.log"; do
  if [ -f "$log" ]; then grep -a -i 'aster-s0-corpus' "$log" | tail -n 100; fi
done > "$EVIDENCE/cloud-init-corpus-lines.txt" || true

sha256sum "$EVIDENCE"/* > "$EVIDENCE/evidence-sha256.txt.part"
mv "$EVIDENCE/evidence-sha256.txt.part" "$EVIDENCE/evidence-sha256.txt"
printf 'forensic_collection=complete\nloop=%s\nroot=%s\n' "$LOOP_DEVICE" "$ROOT"
