# Media RAIDZ2 widening

Owner Jason; started 2026-10-03; Stream M. User authorized beginning sequential
addition of the four SAS candidates, healthiest first. First bounded operation:
attach Z1Z4BJ7Z0000C4453Q38 (WWN 5000c50058c120ef) to the existing RAIDZ2 vdev.
Status: first expansion completed 2026-10-04 05:39 PDT; post-expansion scrub running. No other candidate queued.

## Scope and live evidence

TrueNAS 25.10.5, Media id 1, single six-disk Hitachi RAIDZ2 vdev GUID
13190488833263279493. ONLINE, zero read/write/checksum errors; expansion feature
already enabled. 72% physical allocation, 3.81 TiB dataset availability.
Recovery is a separate two-SATA mirror running extended SMART tests.

BJ7Z has zero grown defects, unchanged three historical uncorrected reads,
zero uncorrected writes, stable non-medium count 37. Original extended test and
September 25 full write/read test passed with zero bad blocks. Fresh short test
requested before attach. Identify through WWN/serial and unused-disk inventory,
not a remembered Linux device letter.

Other candidates: 471FR has 110 grown defects and three historical reads;
BTVM has zero media errors but unresolved growing non-medium counts; BK81 has
1,205 grown defects and historical read/write failures. No further disks are
queued until first expansion is complete and health reviewed. BK81 is not
recommended for this healthy pool; BTVM's unexplained counter requires caution.

## Risk and recovery

Widening permanently rewrites allocation across the existing vdev; RAIDZ2 still
provides two-disk tolerance. It cannot be rolled back by simply detaching the
new disk. Existing media are replaceable by owner policy; current non-media
backups were verified today against Proxmox and retained cloud copies. Fresh
configuration export exists from 05:01 today. No snapshot claims rollback for
pool topology. No backup deletion or consumer change is part of this operation.
The pool remains accessible but heavy I/O can reduce performance. SATA extended
tests use different drives; avoid extra bulk migration or compaction experiments.
Stop on unhealthy pool, changing disk identity, failed fresh test, or new errors.

## Implementation and validation

Use TrueNAS `pool.attach`, pool 1, target existing RAIDZ2 GUID and exactly BJ7Z.
Never use pool.update to introduce an unprotected single-disk vdev. Capture job
ID and verify the new leaf is under the same RAIDZ2, then record expansion
progress. Do not queue repeated calls or another disk while expansion is active.
After completion verify zero ZFS errors, changed capacity, SMART counters and
application availability. Existing blocks retain their old parity ratio; final
capacity is not assumed equal to a freshly built seven-disk vdev.

## Integration and persistence

TrueNAS is storage authority; Doctor already queries all pool health. TrueNAS
job/status provides progression; no new service, credentials, exposure, network,
NetBox addressing or application topology. Existing scrub scheduling remains.
No immediate quota/backup schedule changes. Repository tracks disk membership;
update operator records at completion. Resume with pool job/status and exact
serial mapping; never blindly replay attach. Git push requires separate approval.

## Milestones

- [x] Fresh short test and exact live preflight pass.
- [x] Attach initiated; correct seven-leaf RAIDZ2 and active expansion verified.
- [ ] Expansion completes; pool/SMART/capacity checks pass.
- [ ] Review next candidate independently before another permanent expansion.

## Reference

https://www.truenas.com/docs/scale/25.10/scaletutorials/storage/managepoolsscale/#extending-a-raidz-vdev

## Execution evidence — 2026-10-03 11:06 PDT

Fresh short test completed without error. Immediately rechecked exact serial/WWN,
unused membership, 4 TB size, zero grown defects, stable read=3/write=0 historical
uncorrected counters, Media healthy and six ONLINE original children with zero
ZFS errors. Submitted `pool.attach` for pool 1, RAIDZ2 GUID
13190488833263279493, disk sdf/BJ7Z. Job **292** is RUNNING, Expanding.

ZFS reports expansion of raidz2-0 started 11:06:35 PDT, total 15.9 TiB to
redistribute. Seven ONLINE leaves now exist within the same RAIDZ2; the new
partition UUID is e6ee3b14-30d9-4848-ac8f-1d760123f1b1. No known data errors.
Do not interpret middleware's initial 25% formatting/job progress as actual data
expansion progress; use `zpool status Media`. Completion and final capacity are
pending. The operation persists on TrueNAS independently of this conversation.
Recovery SATA extended tests continue separately. No further SAS disks submitted.

2026-10-03 19:59 PDT check: 8.11/15.9 TiB redistributed, 50.98%, 266 MiB/s;
ZFS estimated 8h32 remaining (approximately October 4 04:31 PDT). All seven
leaves ONLINE, zero read/write/checksum errors. No further disks added.

2026-10-04 07:51 PDT: expansion finished at 05:39:56 after 18h33m21s,
15.9 TiB redistributed. All seven members ONLINE, no ZFS errors. BJ7Z remains
zero grown defects, read/write/verify uncorrected 3/0/0 unchanged. Media dataset
availability now 6.10 TiB (previously 3.81 TiB). Scrub started at expansion
completion: 26.93%, 0B repaired, estimated 5h56 remaining. Wait for scrub result
before another expansion or bulk backup migration.
