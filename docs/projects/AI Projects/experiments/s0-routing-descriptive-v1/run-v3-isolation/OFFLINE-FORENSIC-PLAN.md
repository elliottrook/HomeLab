# VM120 offline read-only forensic plan

Status: **prepared locally; separate execution approval required**

Inspect only retained VM120 OS volume `local-lvm:vm-120-disk-0` while VM120 is
stopped. Create a temporary read-only loop mapping, mount only partition1 with
journal replay disabled, collect the bounded allowlist below, unmount and detach.
Do not boot, repair, relabel, replay the journal, run guest code, retry V3, inspect
unrelated files or access the accepted corpus.

## Fail-closed preconditions

- VM120 is stopped and its exact reviewed configuration still validates.
- VMs118 and119 remain stopped.
- `/dev/pve/vm-120-disk-0` is 8,589,934,592 bytes and is not mounted.
- Its reviewed partition1 starts at sector262144, spans16515039 sectors and has
  UUID `6bb09544-3ae5-42bc-8660-47d62a9f894d`.
- Mount and evidence paths are absent.

The loop mapping must report read-only, and partition1 must also report read-only.
The ext4 mount must include `ro,noload,nosuid,nodev,noexec`. Any mismatch triggers
the cleanup trap and ends the inspection.

## Evidence allowlist

- length, mode, owner and SHA-256 of the reviewed unit, probe and payload manifest;
- existence and metadata of bounded `result.json` and `protocol.txt`, copying them
  only when regular, non-symlink files no larger than8192 bytes;
- at most100 journal records for `aster-s0-isolation.service`, restricted to
  timestamp, unit, priority, identifier, PID, result, exit status and message;
- at most100 cloud-init lines mentioning only `aster-s0-isolation`; and
- partition, filesystem, loop and mount receipts needed to prove read-only custody.

Do not read credential files, SSH keys, machine identity, random seed, unrelated
journals, environment files, service data or personal data. Do not execute anything
from the guest filesystem.

## Cleanup and decision

A trap unmounts and detaches on success, error, signal or interruption. Afterward,
verify no mount or loop mapping remains and all three fixture VMs are stopped. A
cleanup failure is a manual-recovery condition. The inspection may establish the
precise V3 failure, but it grants no correction, second boot, cleanup, corpus access
or push authority.

