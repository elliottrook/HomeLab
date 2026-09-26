# V0 disposable-VM operations candidate

Status: local review artifact; **do not execute without the V1–V3 approval**

This directory contains deterministic seed sources for the bootstrap canary. The
candidate manifest binds every generated file except this explanatory operations
plan. No ISO exists and no Proxmox state has changed.

## Fixed source

- Image: `debian-13-generic-amd64-20260914-2601.qcow2`
- Exact byte length: `433651712`
- SHA-512:
  `a733e7d49442a03e70d03e4eb5aaf3967f3efc69ef70952f9bb10fc1ee2c4876eb95956b5ad2d31350e5fada768feb651352535fb8cd1233f61998a5a7d2e93c`
- Payload manifest SHA-256:
  `85d3421acb001256b2f0e307b61fd9728438ca72daaca5209ea9d6f45c480315`
- Candidate manifest SHA-256:
  `0d015cc70e6df5b31048fd203916dcaf0b783e8ecd3bbaae6b6c76f339610c47`

The two local source files used to create the ISO are `user-data` and `meta-data`.
The remaining files make the generated content and proposed VM configuration
reviewable without parsing YAML.

## Preflight before any mutation

Re-run the read-only host inventory and stop unless all are true:

1. Proxmox quorum/host status is healthy and no backup/migration task is active.
2. `MemAvailable` is at least 8 GiB and swap use is not increasing.
3. `local-lvm` has at least 16 GiB free and `local` has at least 2 GiB free.
4. The chosen VMID is the current free ID and the exact name is absent.
5. VM105 and every service guest are unchanged from the recorded preflight.
6. Candidate file hashes match `candidate-manifest.json`.

The VMID and build-specific paths must be substituted once, recorded in a release
manifest and then treated as immutable. A past `nextid` value is never reused as
authority.

## Reviewed command shape

These commands document the intended mutations. They are deliberately parameterised
until the release manifest binds `VMID`, `BUILD_ID`, `SOURCE`, `SEED_ISO` and exact
volume identities. The release reviewer must compare `qm config` with
`vm-config-proposal.json` before permitting a start.

```sh
qm create "$VMID" --name "aster-s0-fixture-$BUILD_ID" --memory 1024 --balloon 0 \
  --cores 1 --sockets 1 --cpu x86-64-v2-AES --bios ovmf --machine q35 \
  --ostype l26 --scsihw virtio-scsi-single --serial0 socket --vga serial0 \
  --onboot 0 --hotplug 0 --tablet 0 --description "Disposable S0 fixture VM; no corpus"

qm disk import "$VMID" "$SOURCE" local-lvm --format raw --target-disk scsi0
qm disk resize "$VMID" scsi0 8G
qm set "$VMID" --scsi0 "<observed-imported-volume>,discard=on,backup=0"
qm set "$VMID" --efidisk0 local-lvm:0,efitype=4m,pre-enrolled-keys=0
qm set "$VMID" --ide2 "local:iso/$SEED_ISO,media=cdrom"
qm set "$VMID" --boot order=scsi0
qm config "$VMID"
```

There is intentionally no `net0`, `agent`, start, template, clone, passthrough,
VirtioFS or credential command. The imported volume name must come from the actual
`qm disk import`/`qm config` result and be bound before the later `qm set`; do not
guess its disk number.

Generate the ISO on the Proxmox host from a fresh directory containing only the
hash-verified `user-data` and `meta-data`:

```sh
genisoimage -output "$SEED_ISO_PATH.part" -volid cidata -joliet -rock user-data meta-data
isoinfo -d -i "$SEED_ISO_PATH.part"
isoinfo -f -i "$SEED_ISO_PATH.part"
sha256sum "$SEED_ISO_PATH.part"
mv "$SEED_ISO_PATH.part" "$SEED_ISO_PATH"
```

The listing must contain exactly `/USER_DATA.;1` and `/META_DATA.;1` (allowing the
Rock Ridge/Joliet names `user-data` and `meta-data`) and no other payload. Record the
final ISO length and SHA-256 before attachment.

## Start, capture and deadline

Starting the VM is a later V2 step, after stopped-state review. The release wrapper
must start capture immediately after `qm start`, give `qm terminal` a PTY using the
existing `script` tool, cap capture at 300 seconds/4 MiB, and send no serial input.
The exact wrapper remains **UNKNOWN / REQUIRES LIVE FIXTURE VERIFICATION** because
`qm terminal` is available only on the Proxmox host. The strict offline parser is
implemented in `scripts/aster-adaptive/s0_vm_serial.py`.

If the VM remains running at the deadline, issue one `qm stop` for this VM and
record a failed bootstrap. Do not retry. Do not inspect or mount the disk during the
normal path.

## Rollback and recovery

Before boot, rollback is to keep the new VM stopped and detach only its new seed
and disk after verifying their exact volume identities. After boot, stop and retain
the VM, disk and bounded capture for diagnosis. Destruction of the VM or volumes is
not part of V1–V3 and requires its own explicit destructive-action approval. No
rollback command may name VM105 or any pre-existing volume.
