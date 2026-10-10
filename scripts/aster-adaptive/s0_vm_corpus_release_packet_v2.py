"""Render the corrected local-only V5b corpus release packet. No remote or VM operations."""

import hashlib
import json
from pathlib import Path


VMID = 123
BASE = '/var/lib/vz/template/cache/aster-s0-20260926'
ISO_NAME = 'aster-s0-corpus-descriptive-002.iso'
IMAGE_SHA512 = ('a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876'
                    'eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False).encode('ascii')


def render(candidate_dir, validator_path):
    candidate_dir = Path(candidate_dir)
    validator_path = Path(validator_path)
    candidate = json.loads((candidate_dir / 'candidate-manifest.json').read_text())
    expected = {
        'user': candidate['files']['user-data']['sha256'],
        'meta': candidate['files']['meta-data']['sha256'],
        'candidate': digest((candidate_dir / 'candidate-manifest.json').read_bytes()),
        'validator': digest(validator_path.read_bytes()),
    }
    create = f'''#!/bin/bash
set -euo pipefail
umask 077
VMID=123
BASE={BASE}
SOURCE="$BASE/debian-13-generic-amd64-20260914-2601.qcow2"
SEED_SOURCE="$BASE/seed-source-v5b"
RELEASE="$BASE/release-v5b"
ISO_NAME={ISO_NAME}
ISO="/var/lib/vz/template/iso/$ISO_NAME"
ISO_PART="$ISO.part"
fail() {{ printf 'release_v5b=failed\\nreason=%s\\n' "$1" >&2; exit 1; }}
[ "$(pvesh get /cluster/nextid)" = "$VMID" ] || fail nextid
[ ! -e "/etc/pve/qemu-server/$VMID.conf" ] || fail vmid-exists
for old in 118 119 120 121 122; do [ "$(qm status "$old")" = 'status: stopped' ] || fail "vm${{old}}-state"; done
[ ! -e "$ISO" ] && [ ! -e "$ISO_PART" ] && [ ! -e "$RELEASE" ] || fail path-exists
[ -d "$SEED_SOURCE" ] || fail seed-source-absent
[ "$(stat -c %s "$SOURCE")" = 433651712 ] || fail image-size
[ "$(sha512sum "$SOURCE" | awk '{{print $1}}')" = {IMAGE_SHA512} ] || fail image-hash
[ "$(sha256sum "$SEED_SOURCE/user-data" | awk '{{print $1}}')" = {expected['user']} ] || fail user-hash
[ "$(sha256sum "$SEED_SOURCE/meta-data" | awk '{{print $1}}')" = {expected['meta']} ] || fail meta-hash
[ "$(sha256sum "$SEED_SOURCE/candidate-manifest.json" | awk '{{print $1}}')" = {expected['candidate']} ] || fail candidate-hash
[ "$(sha256sum "$SEED_SOURCE/s0_vm_corpus_release_v2.py" | awk '{{print $1}}')" = {expected['validator']} ] || fail validator-hash
MEM_AVAILABLE_KIB="$(awk '$1=="MemAvailable:" {{print $2}}' /proc/meminfo)"
LOCAL_LVM_AVAILABLE_KIB="$(pvesm status | awk '$1=="local-lvm" && $3=="active" {{print $6}}')"
LOCAL_AVAILABLE_KIB="$(pvesm status | awk '$1=="local" && $3=="active" {{print $6}}')"
[ "$MEM_AVAILABLE_KIB" -ge 8388608 ] || fail memory-gate
[ -n "$LOCAL_LVM_AVAILABLE_KIB" ] && [ "$LOCAL_LVM_AVAILABLE_KIB" -ge 16777216 ] || fail local-lvm-gate
[ -n "$LOCAL_AVAILABLE_KIB" ] && [ "$LOCAL_AVAILABLE_KIB" -ge 2097152 ] || fail local-gate
install -d -m 0700 "$RELEASE"
date --iso-8601=seconds > "$RELEASE/start-time.txt"
qm list > "$RELEASE/qm-list-before.txt"
pct list > "$RELEASE/pct-list-before.txt"
pvesm status > "$RELEASE/storage-before.txt"
printf 'MemAvailableKiB=%s\\n' "$MEM_AVAILABLE_KIB" > "$RELEASE/memory-before.txt"
(cd "$SEED_SOURCE" && genisoimage -output "$ISO_PART" -volid cidata -joliet -rock user-data meta-data) > "$RELEASE/genisoimage.txt" 2>&1
isoinfo -R -f -i "$ISO_PART" | sort > "$RELEASE/iso-files.txt"
printf '/meta-data\\n/user-data\\n' > "$RELEASE/iso-files.expected"
diff -u "$RELEASE/iso-files.expected" "$RELEASE/iso-files.txt"
isoinfo -R -i "$ISO_PART" -x /user-data > "$RELEASE/user-data.extracted"
isoinfo -R -i "$ISO_PART" -x /meta-data > "$RELEASE/meta-data.extracted"
[ "$(sha256sum "$RELEASE/user-data.extracted" | awk '{{print $1}}')" = {expected['user']} ] || fail extracted-user-hash
[ "$(sha256sum "$RELEASE/meta-data.extracted" | awk '{{print $1}}')" = {expected['meta']} ] || fail extracted-meta-hash
sha256sum "$ISO_PART" > "$RELEASE/seed-iso.sha256"
stat -c '%n %s %a %u:%g' "$ISO_PART" > "$RELEASE/seed-iso.stat"
mv "$ISO_PART" "$ISO"
qm create "$VMID" --name aster-s0-corpus-v2 --memory 1024 --balloon 0 --cores 1 --sockets 1 --cpu x86-64-v2-AES --bios ovmf --machine q35 --ostype l26 --scsihw virtio-scsi-single --serial0 socket --vga serial0 --onboot 0 --hotplug 0 --tablet 0 --description 'Disposable S0 accepted-corpus descriptive run; no vNIC; no credentials'
qm disk import "$VMID" "$SOURCE" local-lvm --format raw --target-disk scsi0
qm disk resize "$VMID" scsi0 8G
SCSI_VOLUME="$(qm config "$VMID" | sed -n 's/^scsi0: \\([^,]*\\).*/\\1/p')"
[[ "$SCSI_VOLUME" =~ ^local-lvm:vm-123-disk-[0-9]+$ ]] || fail imported-volume
qm set "$VMID" --scsi0 "$SCSI_VOLUME,discard=on,backup=0,ssd=1"
qm set "$VMID" --efidisk0 local-lvm:0,efitype=4m,pre-enrolled-keys=0
qm set "$VMID" --ide2 "local:iso/$ISO_NAME,media=cdrom"
qm set "$VMID" --boot order=scsi0
[ "$(qm status "$VMID")" = 'status: stopped' ] || fail final-state
qm config "$VMID" --current > "$RELEASE/qm-config.txt"
python3 "$SEED_SOURCE/s0_vm_corpus_release_v2.py" "$RELEASE/qm-config.txt" > "$RELEASE/config-validation.txt"
pvesm list local-lvm --vmid "$VMID" > "$RELEASE/volumes.txt"
qm list > "$RELEASE/qm-list-after.txt"
pct list > "$RELEASE/pct-list-after.txt"
sha256sum "$RELEASE"/* > "$RELEASE/evidence-sha256.txt.part"
mv "$RELEASE/evidence-sha256.txt.part" "$RELEASE/evidence-sha256.txt"
printf 'release_v5b=complete\\nvmid=%s\\nstate=stopped\\n' "$VMID"
'''.encode()
    run = f'''#!/bin/bash
set -euo pipefail
umask 077
VMID=123
BASE={BASE}
SEED_SOURCE="$BASE/seed-source-v5b"
RELEASE="$BASE/release-v5b"
RUN="$BASE/run-v5b"
CAPTURE="$RUN/serial.capture"
fail() {{ printf 'run_v5b=failed\\nreason=%s\\n' "$1" >&2; exit 1; }}
[ -d "$RELEASE" ] || fail release-evidence-absent
[ ! -e "$RUN" ] || fail run-path-exists
[ "$(qm status "$VMID")" = 'status: stopped' ] || fail initial-state
qm config "$VMID" --current | python3 "$SEED_SOURCE/s0_vm_corpus_release_v2.py" - >/dev/null || fail config-gate
ISO_DIGEST="$(awk '{{print $1}}' "$RELEASE/seed-iso.sha256")"
[ "$(sha256sum /var/lib/vz/template/iso/{ISO_NAME} | awk '{{print $1}}')" = "$ISO_DIGEST" ] || fail iso-drift
install -d -m 0700 "$RUN"
date --iso-8601=seconds > "$RUN/start-time.txt"
qm list > "$RUN/qm-list-before.txt"
pct list > "$RUN/pct-list-before.txt"
qm start "$VMID"
set +e
timeout --signal=TERM --kill-after=10s 300s script --quiet --flush --return --command "qm terminal $VMID" "$CAPTURE"
CAPTURE_RC=$?
set -e
printf '%s\\n' "$CAPTURE_RC" > "$RUN/capture-exit-code.txt"
FINAL_STATE="$(qm status "$VMID")"
if [ "$FINAL_STATE" != 'status: stopped' ]; then qm stop "$VMID"; FINAL_STATE="$(qm status "$VMID")"; printf '%s\\n' forced > "$RUN/host-stop.txt"; else printf '%s\\n' not-required > "$RUN/host-stop.txt"; fi
[ "$FINAL_STATE" = 'status: stopped' ] || fail final-state
[ -f "$CAPTURE" ] || fail capture-absent
CAPTURE_BYTES="$(stat -c %s "$CAPTURE")"
[ "$CAPTURE_BYTES" -le 4194304 ] || fail capture-oversize
sha256sum "$CAPTURE" > "$RUN/serial.capture.sha256"
printf 'capture_bytes=%s\\n' "$CAPTURE_BYTES" > "$RUN/capture-size.txt"
qm config "$VMID" --current > "$RUN/qm-config-after.txt"
qm list > "$RUN/qm-list-after.txt"
pct list > "$RUN/pct-list-after.txt"
sha256sum "$RUN"/* > "$RUN/evidence-sha256.txt.part"
mv "$RUN/evidence-sha256.txt.part" "$RUN/evidence-sha256.txt"
[ "$CAPTURE_RC" -eq 0 ] || fail capture-command
printf 'run_v5b=capture-complete\\nvmid=%s\\nstate=stopped\\n' "$VMID"
'''.encode()
    release = {
        'schema': 'aster-s0-vm-corpus-release.v2',
        'status': 'local-release-not-authorized', 'vmid': VMID,
        'run_id': candidate['run_id'],
        'candidate_manifest_sha256': expected['candidate'],
        'payload_manifest_sha256': candidate['payload_manifest_sha256'],
        'accepted_corpus_included': True, 'accepted_corpus_evaluated': False,
        'remote_staging_authorized': False, 'vm_creation_authorized': False,
        'boot_authorized': False, 'automatic_retry': False,
        'files': {},
    }
    files = {'create-stopped-vm-v5b.sh': create, 'run-once-v5b.sh': run,
             's0_vm_corpus_release_v2.py': validator_path.read_bytes()}
    release['files'] = {name: {'bytes': len(raw), 'sha256': digest(raw)}
                        for name, raw in sorted(files.items())}
    files['release-manifest.json'] = canonical(release) + b'\n'
    return files


def write_packet(output, candidate_dir, validator_path):
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True, mode=0o700)
    files = render(candidate_dir, validator_path)
    for name, raw in files.items():
        path = output / name
        path.write_bytes(raw)
        path.chmod(0o700 if name.endswith('.sh') else 0o600)
    return files


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 4:
        raise SystemExit('usage: s0_vm_corpus_release_packet_v2.py OUTPUT CANDIDATE VALIDATOR')
    write_packet(sys.argv[1], sys.argv[2], sys.argv[3])
