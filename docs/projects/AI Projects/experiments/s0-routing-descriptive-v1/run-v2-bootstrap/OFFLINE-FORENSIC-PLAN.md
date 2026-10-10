# VM118 offline read-only forensic plan

Status: **proposed; separately authorized execution required**  
Purpose: identify the V2 canary unit failure without rebooting or modifying the guest

## Scope

Inspect only retained VM118 OS volume `local-lvm:vm-118-disk-0` while VM118 is
stopped. Create a temporary read-only loop mapping, mount only the root partition
with journal replay disabled, collect an allowlisted bounded evidence set, unmount
and detach. Do not repair, relabel, replay the filesystem journal, change the VM,
run the canary, or access the accepted corpus.

## Preconditions

All must pass immediately before attachment:

1. `qm status 118` is `stopped`.
2. `qm config 118` still binds `scsi0` to exactly
   `local-lvm:vm-118-disk-0` and contains no `netN` or agent.
3. `findmnt -S /dev/pve/vm-118-disk-0` is empty.
4. The volume is exactly 8,589,934,592 bytes.
5. `partx --show` reports the observed root partition 1 beginning at sector 262144,
   EFI partition 15 and BIOS partition 14. A changed table stops the inspection.
6. The evidence output directory is new and mode 0700.

## Attachment and mount

The reviewed command shape is:

```sh
LOOP_DEVICE="$(losetup --find --show --read-only --partscan /dev/pve/vm-118-disk-0)"
losetup --list --output NAME,BACK-FILE,RO "$LOOP_DEVICE"
blockdev --getro "$LOOP_DEVICE"
lsblk -o NAME,TYPE,SIZE,FSTYPE,MOUNTPOINTS,RO "$LOOP_DEVICE"
mount -t ext4 -o ro,noload,nosuid,nodev,noexec "${LOOP_DEVICE}p1" /mnt/aster-s0-v2-forensic
```

Require the mapping receipt to name the exact source and report `RO=1`; require
`blockdev --getro` to return `1`. Require the mounted source to be partition 1 and
mount options to include `ro,noload,nosuid,nodev,noexec`. Stop and detach if any
check differs. Do not run `fsck`, `resize2fs`, `tune2fs` mutation, `vgchange`, chroot,
guest commands or executables from the mounted filesystem.

## Allowlisted evidence

Collect only:

- SHA-256, length, owner and mode for:
  - `/etc/systemd/system/aster-s0-canary.service`;
  - `/usr/local/lib/aster-s0/canary.py`;
  - `/usr/local/lib/aster-s0/payload-manifest.json`;
- existence, metadata, length and SHA-256 of
  `/var/lib/aster-s0/output/result.json`; read its bytes only if its length is at
  most 2 MiB and its digest/JSON are validated locally;
- at most 100 journal records for `aster-s0-canary.service`, with field names
  allowlisted to timestamp, unit, priority, identifier, PID and message;
- bounded cloud-init lines mentioning only the canary service invocation/failure;
  and
- filesystem UUID/state and mount receipt without directory-wide discovery.

Do not read `/etc/shadow`, SSH private keys, random seed, machine identity,
environment files, unrelated journals, user data, service data or credentials. The
generated canary files are compared with repository hashes rather than copied into
Git again.

## Mandatory detachment

Use a trap from the moment a loop device is allocated. On success or failure:

```sh
umount /mnt/aster-s0-v2-forensic
losetup --detach "$LOOP_DEVICE"
```

Then prove the mount is absent, the loop source is no longer attached, VM118 remains
stopped and all pre-existing guests retain their state. A failed unmount/detach is a
manual-recovery condition and blocks all further work.

## Decision after inspection

Record the exact cause if evidence proves one; otherwise retain `UNKNOWN`. Prepare a
new V2b seed candidate locally with a new instance/run identity and tests. Do not
boot it or proceed to V3 without a new concrete approval. The forensic inspection
does not authorize a retry, disk replacement, VM destruction or corpus execution.

