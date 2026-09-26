#!/bin/bash
set -euo pipefail
umask 077

VMID=119
NAME=aster-s0-fixture-v1
BASE=/var/lib/vz/template/cache/aster-s0-20260926
SOURCE="$BASE/debian-13-generic-amd64-20260914-2601.qcow2"
SEED_SOURCE="$BASE/seed-source-v1"
RELEASE="$BASE/release-v1b"
ISO_NAME=aster-s0-bootstrap-canary-002.iso
ISO="/var/lib/vz/template/iso/$ISO_NAME"
ISO_PART="$ISO.part"
EXPECTED_IMAGE_SHA512=a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c
EXPECTED_USER_SHA256=e81ee511b3bac0a361fdfb660386f2e61ef8af2925a7f744557ec25283eaab68
EXPECTED_META_SHA256=a043603996ec3e8bebd6d65578818879811fdec070648deada99173cd5821274
EXPECTED_CANDIDATE_SHA256=c5e4eb98bc7847e97969b9a853b3da4cf801bcbb5748e53ac2f9c9b6f82831bf
EXPECTED_VALIDATOR_SHA256=63347c7952411206c7fde19d1187c63ce6a5f46f44059ee3501e39cbee8a7e72

fail() { printf 'release_v1b=failed\nreason=%s\n' "$1" >&2; exit 1; }

[ "$(pvesh get /cluster/nextid)" = "$VMID" ] || fail nextid
[ ! -e "/etc/pve/qemu-server/$VMID.conf" ] || fail vmid-exists
[ "$(qm status 118)" = 'status: stopped' ] || fail vm118-state
[ ! -e "$ISO" ] || fail iso-exists
[ ! -e "$ISO_PART" ] || fail iso-part-exists
[ ! -e "$RELEASE" ] || fail release-evidence-exists
[ -d "$SEED_SOURCE" ] || fail seed-source-absent
[ "$(stat -c %s "$SOURCE")" = 433651712 ] || fail image-size
[ "$(sha512sum "$SOURCE" | awk '{print $1}')" = "$EXPECTED_IMAGE_SHA512" ] || fail image-hash
[ "$(sha256sum "$SEED_SOURCE/user-data" | awk '{print $1}')" = "$EXPECTED_USER_SHA256" ] || fail user-data-hash
[ "$(sha256sum "$SEED_SOURCE/meta-data" | awk '{print $1}')" = "$EXPECTED_META_SHA256" ] || fail meta-data-hash
[ "$(sha256sum "$SEED_SOURCE/candidate-manifest.json" | awk '{print $1}')" = "$EXPECTED_CANDIDATE_SHA256" ] || fail candidate-hash
[ "$(sha256sum "$SEED_SOURCE/s0_vm_release.py" | awk '{print $1}')" = "$EXPECTED_VALIDATOR_SHA256" ] || fail validator-hash

MEM_AVAILABLE_KIB="$(awk '$1=="MemAvailable:" {print $2}' /proc/meminfo)"
[ "$MEM_AVAILABLE_KIB" -ge 8388608 ] || fail memory-gate
LOCAL_LVM_AVAILABLE_KIB="$(pvesm status | awk '$1=="local-lvm" && $3=="active" {print $6}')"
LOCAL_AVAILABLE_KIB="$(pvesm status | awk '$1=="local" && $3=="active" {print $6}')"
[ -n "$LOCAL_LVM_AVAILABLE_KIB" ] && [ "$LOCAL_LVM_AVAILABLE_KIB" -ge 16777216 ] || fail local-lvm-gate
[ -n "$LOCAL_AVAILABLE_KIB" ] && [ "$LOCAL_AVAILABLE_KIB" -ge 2097152 ] || fail local-gate

install -d -m 0700 "$RELEASE"
date --iso-8601=seconds > "$RELEASE/start-time.txt"
qm list > "$RELEASE/qm-list-before.txt"
pct list > "$RELEASE/pct-list-before.txt"
pvesm status > "$RELEASE/storage-before.txt"
printf 'MemAvailableKiB=%s\n' "$MEM_AVAILABLE_KIB" > "$RELEASE/memory-before.txt"

(
  cd "$SEED_SOURCE"
  genisoimage -output "$ISO_PART" -volid cidata -joliet -rock user-data meta-data
) > "$RELEASE/genisoimage.txt" 2>&1
isoinfo -R -f -i "$ISO_PART" | sort > "$RELEASE/iso-files.txt"
printf '/meta-data\n/user-data\n' > "$RELEASE/iso-files.expected"
diff -u "$RELEASE/iso-files.expected" "$RELEASE/iso-files.txt"
isoinfo -R -i "$ISO_PART" -x /user-data > "$RELEASE/user-data.extracted"
isoinfo -R -i "$ISO_PART" -x /meta-data > "$RELEASE/meta-data.extracted"
[ "$(sha256sum "$RELEASE/user-data.extracted" | awk '{print $1}')" = "$EXPECTED_USER_SHA256" ] || fail extracted-user-hash
[ "$(sha256sum "$RELEASE/meta-data.extracted" | awk '{print $1}')" = "$EXPECTED_META_SHA256" ] || fail extracted-meta-hash
sha256sum "$ISO_PART" > "$RELEASE/seed-iso.sha256"
stat -c '%n %s %a %u:%g' "$ISO_PART" > "$RELEASE/seed-iso.stat"
mv "$ISO_PART" "$ISO"

qm create "$VMID" --name "$NAME" --memory 1024 --balloon 0 --cores 1 --sockets 1 \
  --cpu x86-64-v2-AES --bios ovmf --machine q35 --ostype l26 \
  --scsihw virtio-scsi-single --serial0 socket --vga serial0 --onboot 0 \
  --hotplug 0 --tablet 0 \
  --description 'Disposable S0 bootstrap canary v1; no vNIC; no corpus'
qm disk import "$VMID" "$SOURCE" local-lvm --format raw --target-disk scsi0
qm disk resize "$VMID" scsi0 8G
SCSI_VOLUME="$(qm config "$VMID" | sed -n 's/^scsi0: \([^,]*\).*/\1/p')"
[[ "$SCSI_VOLUME" =~ ^local-lvm:vm-119-disk-[0-9]+$ ]] || fail imported-volume
qm set "$VMID" --scsi0 "$SCSI_VOLUME,discard=on,backup=0,ssd=1"
qm set "$VMID" --efidisk0 local-lvm:0,efitype=4m,pre-enrolled-keys=0
qm set "$VMID" --ide2 "local:iso/$ISO_NAME,media=cdrom"
qm set "$VMID" --boot order=scsi0

[ "$(qm status "$VMID")" = 'status: stopped' ] || fail final-state
qm config "$VMID" --current > "$RELEASE/qm-config.txt"
python3 "$SEED_SOURCE/s0_vm_release.py" "$RELEASE/qm-config.txt" > "$RELEASE/config-validation.txt"
pvesm list local-lvm --vmid "$VMID" > "$RELEASE/volumes.txt"
qm list > "$RELEASE/qm-list-after.txt"
pct list > "$RELEASE/pct-list-after.txt"
sha256sum "$RELEASE"/* > "$RELEASE/evidence-sha256.txt.part"
mv "$RELEASE/evidence-sha256.txt.part" "$RELEASE/evidence-sha256.txt"
printf 'release_v1b=complete\nvmid=%s\nstate=stopped\n' "$VMID"
