# Recovery SATA mirror

Owner: Jason. Started 2026-10-03. Stream M, bounded allocation approved by Jason:
“Nothing to keep on the sata drives. Please allocate them as recommended.”
Status: allocation and extended SMART qualification complete; migration pending.

## Purpose, scope and authority

Create a separate two-disk mirrored Recovery pool for guest recovery,
configurations, family files and photo backups. TrueNAS live inventory is the
storage authority. Only SATA IronWolf ST4000VN008 drives ZGY7C8NF and ZDH9JCR8
are authorized for destructive preparation. Existing Media and boot pools,
four spare SAS drives and active backup destinations are excluded.

## Evidence and risk assessment

Both 4 TB drives are unused in TrueNAS and carry unmounted legacy Synology RAID
partitions. Owner explicitly released all their old contents for deletion.
SMART health passes; reallocations, pending sectors, uncorrectable sectors,
reported errors and CRC errors are zero. Power-on hours approximately 25,846 and
22,260. Short tests started; extended tests estimated 597–600 minutes.

Pool creation irreversibly replaces the old disk layout; no old-content rollback
is required or possible after formatting. Guard by exact serial/model/size and
unused-disk membership immediately before using the TrueNAS pool API. No force
operation against a current pool. A mirror tolerates one disk failure, not loss
of the whole NAS. Existing backup copies remain the recovery path until a later
verified migration. No service interruption expected; stop on errors or disk
identity mismatch. Fresh long tests must pass before production migration.

## Layout and privacy

One MIRROR vdev, no cache/log/special devices; approximately 3.64 TiB raw mirrored
capacity. Root-private backup datasets, compression LZ4, atime off, no executable
payload requirement, normal synchronous-write semantics and checksums. No shares
or network exposure created. No key material generated or exported; local storage
follows the existing unencrypted backup-pool posture; cloud encryption unchanged.

Proposed capacity caps: guests 1 TiB; configuration 100 GiB; family 600 GiB;
photos 1.2 TiB. Quotas cap combined data/history, not reserved allocations. Total
caps leave roughly 20% physical headroom. Photo cap can be reviewed after full
library inventory. No snapshots scheduled over empty datasets; design retention
and update consumers during the separately scoped migration.

## Milestones and validation

- [x] Exact identity/unused verification and fresh short SMART tests pass.
- [x] TrueNAS-managed Recovery mirror online with both exact disks.
- [x] Four private datasets and quotas verified; bounded write/read test passes.
- [x] Extended SMART tests pass on both disks before production data migration.
- [ ] Migration, restore proof, backup consumers and retention: future phase.

Persist job identifiers and results here. Do not recreate an existing Recovery
pool on resume. Query pool topology, SMART test logs and dataset properties first.

## Integration and maintenance

TrueNAS handles pool health/alerts and scrub scheduling; verify managed scrub
exists. Existing SMART service remains active; fresh extended qualification tests
are independent of future recurring tests. Doctor already checks TrueNAS pool
health; inventory/docs record the new pool. NetBox/network, DNS, firewall,
Homepage, authentication, AI identities and rack wiring unchanged. No new service
or secret introduced. Wiki/operational migration guidance is deferred until the
consumer migration is designed; this document is the allocation record.

## Evidence log

2026-10-03: serials map to sdh (ZGY7C8NF) and sdj (ZDH9JCR8); both listed by
`disk.get_unused`; current Media consists only of six Hitachi SAS disks. No SATA
mounts, clean SMART counters. User waived legacy content preservation explicitly.

2026-10-03 10:57 PDT: fresh short SMART tests passed on both drives. TrueNAS
pool.create job 259 SUCCESS; pool id 2 Recovery is ONLINE with one MIRROR vdev,
sdh/ZGY7C8NF and sdj/ZDH9JCR8. Usable ZFS dataset availability is 3.51 TiB
(after partitioning/ZFS reserve), pool size 3.62 TiB. All four datasets created
with quotas 1024/100/600/1228 GiB, LZ4, atime off, exec off, standard sync,
POSIX permissions root:root 0700; quota warning 80%, critical 90%.

Each dataset passed a 16 MiB random write, fsync and direct-read SHA-256 comparison;
synthetic files removed. This is a bounded functional check, not a full-surface
write test. All pools healthy; no changes to existing backup destinations.
TrueNAS automatically created enabled scrub task 2 (Sunday midnight check,
35-day threshold). Existing Doctor queries all TrueNAS pools.

Extended SMART tests started 10:57 PDT. Estimated completion: ZGY7C8NF 20:54,
ZDH9JCR8 20:57 on October 3. These are running, not passed. On resume query
`smartctl -a -j /dev/disk/by-id/ata-ST4000VN008-2DR166_<serial>` and confirm
both latest Extended offline entries complete without error, no new relevant
SMART errors and pool health before scheduling migration. No migration or
backup-consumer cutover is performed by this allocation task.

2026-10-03 19:59 PDT: both latest Extended offline SMART tests completed without
error (ZGY7C8NF at 25,853 hours; ZDH9JCR8 at 22,267 hours). Reallocated, pending,
offline uncorrectable, reported uncorrectable and CRC counts all remain zero.
Recovery ONLINE with zero ZFS errors. Qualification gate passed; backup migration
has not started. Media expansion is still active, so avoid extra bulk migration
load until it finishes.
