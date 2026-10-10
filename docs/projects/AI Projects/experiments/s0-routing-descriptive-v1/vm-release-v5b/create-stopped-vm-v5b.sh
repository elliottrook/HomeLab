#!/bin/bash
set -euo pipefail
umask 077
VMID=123
BASE=/var/lib/vz/template/cache/aster-s0-20260926
SOURCE="$BASE/debian-13-generic-amd64-20260914-2601.qcow2"
SEED_SOURCE="$BASE/seed-source-v5b"
RELEASE="$BASE/release-v5b"
ISO_NAME=aster-s0-corpus-descriptive-002.iso
ISO="/var/lib/vz/template/iso/$ISO_NAME"
ISO_PART="$ISO.part"
fail() { printf 'release_v5b=failed\nreason=%s\n' "$1" >&2; exit 1; }
[ "$(pvesh get /cluster/nextid)" = "$VMID" ] || fail nextid
[ ! -e "/etc/pve/qemu-server/$VMID.conf" ] || fail vmid-exists
for old in 118 119 120 121 122; do [ "$(qm status "$old")" = 'status: stopped' ] || fail "vm${old}-state"; done
[ ! -e "$ISO" ] && [ ! -e "$ISO_PART" ] && [ ! -e "$RELEASE" ] || fail path-exists
[ -d "$SEED_SOURCE" ] || fail seed-source-absent
[ "$(stat -c %s "$SOURCE")" = 433651712 ] || fail image-size
[ "$(sha512sum "$SOURCE" | awk '{print $1}')" = a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c ] || fail image-hash
[ "$(sha256sum "$SEED_SOURCE/user-data" | awk '{print $1}')" = bf7e2a99023eac362883ab2c53ea440948d89782cd0509c0ecd5cce1607f0d55 ] || fail user-hash
[ "$(sha256sum "$SEED_SOURCE/meta-data" | awk '{print $1}')" = 7b8b25af5fe5b794eeb8f0b0898c339c3fed0e74430b006dc4e64049d5324744 ] || fail meta-hash
[ "$(sha256sum "$SEED_SOURCE/candidate-manifest.json" | awk '{print $1}')" = 1222881382e7c5e7c9e33d95078dd2f640bedb69f0260bc663ca09d5242ff2c0 ] || fail candidate-hash
[ "$(sha256sum "$SEED_SOURCE/s0_vm_corpus_release_v2.py" | awk '{print $1}')" = 03f7d55c05a4b4c640cc92a8ba71c028afec732ec3227d32ec20a371649653fd ] || fail validator-hash
MEM_AVAILABLE_KIB="$(awk '$1=="MemAvailable:" {print $2}' /proc/meminfo)"
LOCAL_LVM_AVAILABLE_KIB="$(pvesm status | awk '$1=="local-lvm" && $3=="active" {print $6}')"
LOCAL_AVAILABLE_KIB="$(pvesm status | awk '$1=="local" && $3=="active" {print $6}')"
[ "$MEM_AVAILABLE_KIB" -ge 8388608 ] || fail memory-gate
[ -n "$LOCAL_LVM_AVAILABLE_KIB" ] && [ "$LOCAL_LVM_AVAILABLE_KIB" -ge 16777216 ] || fail local-lvm-gate
[ -n "$LOCAL_AVAILABLE_KIB" ] && [ "$LOCAL_AVAILABLE_KIB" -ge 2097152 ] || fail local-gate
install -d -m 0700 "$RELEASE"
date --iso-8601=seconds > "$RELEASE/start-time.txt"
qm list > "$RELEASE/qm-list-before.txt"
pct list > "$RELEASE/pct-list-before.txt"
pvesm status > "$RELEASE/storage-before.txt"
printf 'MemAvailableKiB=%s\n' "$MEM_AVAILABLE_KIB" > "$RELEASE/memory-before.txt"
(cd "$SEED_SOURCE" && genisoimage -output "$ISO_PART" -volid cidata -joliet -rock user-data meta-data) > "$RELEASE/genisoimage.txt" 2>&1
isoinfo -R -f -i "$ISO_PART" | sort > "$RELEASE/iso-files.txt"
printf '/meta-data\n/user-data\n' > "$RELEASE/iso-files.expected"
diff -u "$RELEASE/iso-files.expected" "$RELEASE/iso-files.txt"
isoinfo -R -i "$ISO_PART" -x /user-data > "$RELEASE/user-data.extracted"
isoinfo -R -i "$ISO_PART" -x /meta-data > "$RELEASE/meta-data.extracted"
[ "$(sha256sum "$RELEASE/user-data.extracted" | awk '{print $1}')" = bf7e2a99023eac362883ab2c53ea440948d89782cd0509c0ecd5cce1607f0d55 ] || fail extracted-user-hash
[ "$(sha256sum "$RELEASE/meta-data.extracted" | awk '{print $1}')" = 7b8b25af5fe5b794eeb8f0b0898c339c3fed0e74430b006dc4e64049d5324744 ] || fail extracted-meta-hash
sha256sum "$ISO_PART" > "$RELEASE/seed-iso.sha256"
stat -c '%n %s %a %u:%g' "$ISO_PART" > "$RELEASE/seed-iso.stat"
mv "$ISO_PART" "$ISO"
qm create "$VMID" --name aster-s0-corpus-v2 --memory 1024 --balloon 0 --cores 1 --sockets 1 --cpu x86-64-v2-AES --bios ovmf --machine q35 --ostype l26 --scsihw virtio-scsi-single --serial0 socket --vga serial0 --onboot 0 --hotplug 0 --tablet 0 --description 'Disposable S0 accepted-corpus descriptive run; no vNIC; no credentials'
qm disk import "$VMID" "$SOURCE" local-lvm --format raw --target-disk scsi0
qm disk resize "$VMID" scsi0 8G
SCSI_VOLUME="$(qm config "$VMID" | sed -n 's/^scsi0: \([^,]*\).*/\1/p')"
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
printf 'release_v5b=complete\nvmid=%s\nstate=stopped\n' "$VMID"
