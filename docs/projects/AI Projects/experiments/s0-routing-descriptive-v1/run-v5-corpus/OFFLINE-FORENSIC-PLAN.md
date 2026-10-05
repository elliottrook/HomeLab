# VM122 offline read-only forensic plan

Status: **prepared locally; separate execution approval required**

Inspect only retained VM122 OS volume `local-lvm:vm-122-disk-0` while VM122 is
stopped. Create a temporary read-only loop mapping, mount partition 1 with journal
replay disabled, collect the bounded allowlist below, then unmount and detach. Do
not boot, repair, replay the journal, run guest code, retry V5, inspect unrelated
files, tune routers or expose corpus content.

## Fail-closed preconditions

- VMs118–122 are stopped and VM122's exact reviewed configuration validates.
- `/dev/pve/vm-122-disk-0` is 8,589,934,592 bytes and is not mounted.
- Partition 1 has the pinned source-image start, size and UUID.
- Mount and evidence paths are absent.
- The loop and partition report read-only; the mount reports
  `ro,noload,nosuid,nodev,noexec`.

Any mismatch invokes the cleanup trap and ends the inspection.

## Evidence allowlist

- metadata and SHA-256 only for the exact unit, entry point, payload, three source
  files and nine accepted corpus artifacts; corpus contents are not exported;
- existence, metadata and SHA-256 of `result.json` and `protocol.txt`, copying only
  bounded regular non-symlink files when present;
- at most 200 journal records for `aster-s0-corpus.service`, restricted to
  timestamp, unit, priority, identifier, PID, message, result and exit status;
- at most 100 cloud-init lines mentioning only `aster-s0-corpus`; and
- partition, filesystem, loop and mount receipts proving read-only custody.

Do not read credentials, SSH keys, machine identity, random seed, unrelated
journals, environment files or service data. Do not execute anything from the guest
filesystem.

## Cleanup and authority

A trap unmounts and detaches on success, error, signal or interruption. Verify no
mount or loop mapping remains and VMs118–122 remain stopped. The inspection may
establish the V5 failure and whether bounded outputs exist. It grants no correction,
new candidate, second boot, cleanup, promotion or push authority.
