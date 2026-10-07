# Backup cleanup proposal — 2026-10-03

Status: CLEANUP EXECUTED 2026-10-03; next scheduled cycle pending validation. Jason approved the next step: exact
obsolete local/cloud archive cleanup and guarded ongoing reconciliation. Cloud
version purging, backup snapshot deletion and broader migrations remain excluded.
Requested by Jason after the storage/backup review. This is the first bounded
cleanup, not approval of the broader storage migration or replacement software.

## Exact scope

The adjacent [manifest](backup-cleanup-2026-10-03-manifest.json) records source,
TrueNAS and cloud inventories, every candidate filename/size, and retained files.
Candidates are full guest archives absent from the current Proxmox source
retention set. Absence makes them older recovery points, not corrupt files.
Deleting them intentionally gives up those older restore dates.

- Local target: /mnt/Media/backup/homelab-proxmox-guests on TrueNAS.
- Cloud target: only corresponding named current objects under
  idrive-crypt:homelab-proxmox-guests in homelab-backup-relay.
- Exclude legacy LXC 110 from this batch despite its absence from the ordinary
  source match: it has a separate mirror and requires an explicit separate decision.
- No source Proxmox backups will be removed. Its current 7 daily / 4 weekly /
  6 monthly policy remains unchanged in this first pass.
- Do not delete any Media/backup snapshots: they contain family/configuration
  history as well as guest archive history.
- No photographs, family files, surveillance recordings, old Synology disk
  contents, legacy cloud bucket, VM configurations or live media files are targets.

## Guest archive preview

| VMID | Local copies now | Retained source matches | Local candidates | Local logical GiB | Cloud candidate GiB |
|---|---:|---:|---:|---:|---:|
| 100 | 43 | 11 | 32 | 83.34 | 83.34 |
| 101 | 42 | 11 | 31 | 80.84 | 80.84 |
| 102 | 41 | 11 | 30 | 147.66 | 147.66 |
| 103 | 40 | 11 | 29 | 74.78 | 74.78 |
| 104 | 41 | 11 | 30 | 50.85 | 50.85 |
| 105 | 40 | 11 | 29 | 244.09 | 244.09 |
| 106 | 40 | 11 | 29 | 39.55 | 39.55 |
| 107 | 40 | 11 | 29 | 36.10 | 36.10 |
| 108 | 39 | 11 | 28 | 9.03 | 9.03 |
| 109 | 36 | 11 | 25 | 24.04 | 24.04 |
| 111 | 33 | 10 | 23 | 28.22 | 28.22 |
| 112 | 16 | 9 | 7 | 1.75 | 1.75 |
| 113 | 26 | 9 | 17 | 6.17 | 6.17 |
| 114 | 19 | 8 | 11 | 9.76 | 9.76 |
| 115 | 19 | 8 | 11 | 22.58 | 0.00 |
| 116 | 12 | 7 | 5 | 11.13 | 11.13 |
| 117 | 9 | 7 | 2 | 0.71 | 0.71 |

Totals: **368 local candidate archives, 870.59 GiB logical size**.
**357 matching cloud candidates, 848.01 GiB plaintext size**.
There are 168 retained source-matching archives across 17 guests; the excluded
legacy LXC 110 archive also remains untouched in the shared directory.
The 11 local-only Paperless candidates explain the difference between local
and cloud counts. Paperless remains excluded from whole-guest cloud backup.

All 168 retained files have matching names and sizes between source and TrueNAS.
All 160 cloud-eligible retained files also have matching cloud names/sizes.
These metadata checks alone do not prove restore success. Newest-copy checksum
verification is recorded separately below when complete.

Completed verification: **all 17 newest retained archives have identical SHA-256
checksums on Proxmox and TrueNAS; all 17 TrueNAS archives pass zstd integrity
testing**. Exact filenames, byte sizes and hashes are in the
[verification record](backup-cleanup-2026-10-03-verification.json).
This confirms matching readable compressed archives, not a fresh boot/restore
of every guest or cloud cryptographic verification. All 160 retained cloud-eligible
archive names/sizes match; the eight Paperless archives are intentionally local-only.

## Media snapshot preview

One snapshot is already beyond the existing seven-day compaction rollback window:

`Media/data@archive-compact-20260923-233906`

Read-only `zfs destroy -nvp` previews **1,677,147,406,440 bytes (1.525 TiB)**
reclaimed. No holds, clones or deferred destruction were reported. Keep the other
seven Media/data snapshots, including the separately named repair checkpoint.
No recursive deletion or child-dataset selection is proposed.

The compaction log recorded failed expiry (rc=1) on October 1 and October 3;
other expired snapshots were successfully removed on October 3. The deployed
code discards stderr and only records the return code. The precise reason for
this snapshot's failure remains unproven. A dry-run reclaim estimate does not
prove that real destruction will succeed.

## What the savings mean

- Snapshot removal: ZFS's current preview is about 1.53 TiB immediately
  reclaimable, subject to concurrent changes and actual execution success.
- Local archive removal: 870.59 GiB of live logical files disappear, but existing
  Media/backup snapshots may continue referencing their blocks. Do not promise
  that much immediate pool free space or add it directly to the snapshot estimate.
- Cloud: the current visible payload could drop from approximately 1.675 TB to
  approximately 0.764 TB (decimal), before new uploads and version accounting.
  Versioned S3 deletion may retain the underlying bytes as noncurrent versions;
  current-object removal alone does NOT guarantee a corresponding billing reduction.
- Do not purge all cloud versions. Exact encrypted keys/version IDs and lifecycle
  policy need read-only inspection before any separately approved permanent purge.
  Historical objects belonging to other data must remain protected.

## Retention correction to accompany approved cleanup

The immediate objective is to make the destination follow the existing source
policy, not to shorten that source policy yet.

1. Keep task 1's exact destination, include filters, SSH source and 04:00 schedule.
   Proposed change: enable destination deletion only for the already included
   guest archive patterns. Never add --delete-excluded or --ignore-errors.
2. Before enabling it, capture a dry run of the actual deployed rsync arguments;
   check that its proposed deletions match a freshly generated manifest, with no
   unexpected paths. Verify source storage is mounted, latest backup jobs succeeded,
   every expected guest retains a nonempty set and recent recovery copies exist.
3. Add fail-closed checks around reconciliation: a missing/empty source, failed
   scan, unexpected guest-set change or deletion spike must stop deletion and alert.
   If the native task cannot provide those checks, use a narrowly scoped guarded
   reconciliation step instead of enabling unattended deletion blindly.
4. Snapshot expiry: keep the existing seven-day policy for this first step, capture
   stderr, report failed expiry as a failure, and run bounded expiry independently
   of new transcoding work. Never automatically select repair/manual snapshots.
5. Configure monitoring for source/destination archive-count drift, retention
   failures, cloud growth and free space. Verify another scheduled cycle before
   claiming the recurring problem resolved.

These are proposed settings/implementation requirements, not deployed code.
The broader 7-daily/4-weekly guest policy, retired VM 105 reduction, PBS/restic
migration, shorter media rollback window, cloud version disposal and other
changes remain separate proposals.

## Execution gates and recovery

- Re-inventory immediately before execution. This dated manifest is not a
  permanently valid deletion authorization; stop if retained files changed or
  candidates differ materially.
- Check source and destination newest-copy checksums and archive integrity.
  Existing September restore evidence is useful but not a fresh restore of every
  current guest. Preserve the source archives and all newer destination history.
- Ensure backup/relay/compaction jobs are not racing the approved operation.
  Removing current local archives can cause the next relay sync to remove their
  current cloud objects; authorization must explicitly cover that propagation.
- Snapshot deletion is irreversible for its unique blocks. The rollback lost is
  old replaceable-media state, not the live media dataset.
- Retention-setting rollback is to restore the previous task settings. It cannot
  recreate permanently deleted backup versions.
- After execution compare exact retained sets, ZFS/pool health, free-space change,
  relay completion, cloud visible size, and a selected restore/integrity check.
- No automatic broad retries or recursive deletion if any target fails.

## Execution checkpoint

Fresh inventories match all 368 local and 357 cloud candidates; all 168 retained
local and 160 cloud-eligible copies still match source names/sizes. Existing
same-day SHA-256/zstd evidence remains applicable. No backup jobs are active.
A guarded reconciliation script was tested locally and its live dry run reports
exactly 368 archives / 934,793,933,980 bytes. Native rsync deletion remains disabled.
The media snapshot proposal above was superseded by the separately completed
owner-directed media cleanup; see archive-duplicate-sweep-2026-10-03.json.

## Completed cleanup and deployed guard

- Deleted exactly 368 local archives (934,793,933,980 bytes / 870.59 GiB) and
  357 current cloud objects (910,545,776,948 bytes / 848.01 GiB). Cloud dry run
  matched the approved filenames; deletion used that exact list and max-delete 357.
- Post inventories prove every candidate absent and all other guest archives
  unchanged: 169 local archives (168 source matches plus preserved LXC 110) and
  162 cloud guest objects remain. Family/configuration paths were not targets.
- Cloud current size: **764,133,725,770 bytes**, 111,727 files, down from
  1,674,679,502,718 bytes. Billing/version bytes were not purged or remeasured.
- Selected newest LXC 112 cloud archive passed `rclone cryptcheck`: one match,
  zero differences. Same-day 17-guest source/local SHA-256 and zstd evidence is
  retained. This does not claim a new guest boot restore.
- Media/backup now references 1.06 TiB live and 1.48 TiB in unchanged snapshots;
  total remains 2.54 TiB. Pool remains healthy, 72% used. Those snapshots retain
  family/configuration history and were not deleted for capacity recovery.

Native rsync task 1 remains enabled at 04:00 with `delete=false`. TrueNAS cron 8
runs `/usr/bin/python3 /mnt/Media/backup-ops/guest-retention-reconcile.py --execute`
at 06:00 America/Los_Angeles, before the 07:00 relay. It uses the existing
read-only restricted SSH/rsync export; no new credentials or firewall rules.
The source's 7 daily / 4 weekly / 6 monthly policy is unchanged.

The guard requires a successful pull within 30 hours, all 17 expected guests,
at least seven source recovery points per guest, latest backups under 48 hours
old, and matching local sizes for every retained file. It checks the source
again before deletion and rejects running pulls, changed files, changed source
guest sets, source inventory shrink over 20%, more than 25 deletions, over 20%
local deletion, or candidates absent from its last good source inventory.
Only regular archive files for guests 100–117 except 110 qualify. All other
paths are ignored. Bootstrap mode requires an exact separately approved manifest.

Eight regression tests passed. Initial live dry run matched 368 candidates;
the approved execution succeeded; a second live execution was a successful no-op.
State is `/mnt/Media/backup-ops/guest-retention-state.json`, initial evidence log
`cleanup-20261003.log`, recurring log `last-run.log`. HomeLab Doctor checks success
and age under 30 hours; failures retain their error in state. The new Doctor
check passed live. Source/deletion guard failures stop rather than widening scope.

**Remaining gate:** observe the next scheduled pull → reconciliation → relay cycle.
No claim is made yet that an overnight production cycle has passed. To suspend
reconciliation, disable only cron 8; native pull/relay remain in place. Deleted
current cloud objects were not version-purged, and local snapshot history was
preserved, but restoration must be explicitly scoped rather than assumed.

Integration impact: backup retention, Doctor, automation and repository runbooks
updated. No service, IP, topology, authentication or application changes; NetBox,
DNS/firewall, Homepage, rack records and AI service identities are unaffected.
No new public exposure or secret handling. The script/manifest are reproducible
from Git; the source inventory state can be re-established only after review.
Remote Git synchronization remains pending separate push authorization.

## First scheduled-cycle observation — 2026-10-04

At 07:51 PDT, the overnight TrueNAS guest pull had succeeded, 06:00 retention
reconciliation succeeded with zero candidates, and cloud relay completed
successfully at 07:41 PDT (35.623 GiB uploaded, 28 files). This verifies the
scheduled sequence, including a safe no-op; no production prune candidates
occurred in this cycle, so recurring deletion is not claimed exercised overnight.

## Scheduled deletion verified — 2026-10-05

The overnight pull succeeded. At 06:00 the guard successfully removed 17 obsolete
local archives, 38,884,945,923 bytes. The cloud relay completed at 07:39:45 PDT,
uploading 36.602 GiB and deleting 17 objects / 34.158 GiB (including one
Home Assistant history object). The local/cloud counts differ by the intended
Paperless exclusion and the unrelated normal Home Assistant rotation. This
confirms the recurring production prune path, beyond the prior no-op cycle.

## Cloud version discrepancy review — 2026-10-07

Read-only review requested before any push. No cloud deletions, lifecycle changes
or Git push performed. Current decrypted payload is 805,835,728,127 bytes across
111,782 files. S3 ListObjectVersions across 113 pages gives 806,037,092,255 bytes
current encrypted objects plus 1,038,299,453,764 bytes noncurrent versions:
1,844,336,546,019 bytes total, matching independent rclone --s3-versions size.
The reported 1.68 TB dashboard value is below this live inventory; dashboard age
or accounting cannot be established from the API evidence.

| Prefix | Current encrypted bytes | Noncurrent bytes | Noncurrent versions |
|---|---:|---:|---:|
| homelab-proxmox-guests | 458590469180 | 1021053826174 | 405 |
| gowest | 332803410449 | 1124972561 | 43 |
| jellyfin | 13346546936 | 0 | 0 |
| configuration | 1152401834 | 15412352573 | 67 |
| home-assistant | 111858528 | 708198240 | 26 |
| mac | 32383465 | 103901 | 26 |
| service-reconstruction | 10654 | 0 | 0 |
| paperless-service | 11209 | 0 | 0 |
| old synthetic validation prefixes combined | 0 | 315 | 3 |

405 delete markers coexist with the 405 noncurrent guest archive versions.
Guest history accounts for 98.34% of noncurrent bytes. Versioning is Enabled;
GetBucketLifecycleConfiguration returns NoSuchLifecycleConfiguration. Previously
approved current-object cleanup and nightly retention remove visibility but do
not expire the previous S3 versions. This explains ongoing growth despite the
current payload remaining near 800 GB. Migration preserved cloud prefixes.
Only homelab-backup-relay was visible using this credential; this is not an
account-wide billing or other-region inventory.

Recommended bounded follow-up: enumerate exact noncurrent guest keys/version IDs,
match deleted/expired archives against the retention evidence and current live
recovery points, then request approval to permanently purge only that reviewed
set. Potential reduction 1,021,053,826,174 bytes to 823,282,719,845 bytes total
before subsequent uploads. Preserve current objects and family/config versions.
Install prefix-specific noncurrent-version expiry: propose one day for guest
archives (their current dated archives already implement Proxmox retention),
30 days for family files, and 14 days for configuration exports; automatically
remove expired delete markers. These are proposals, not applied policies.
One day still adds roughly a daily batch of retired archives; 800 GB is a target,
not a hard cap. Never apply age expiry to current guest objects: monthly restore
points are intentionally older. Keep versioning enabled. Add current/noncurrent
size reporting and alerts so future retention drift is visible.

IDrive documents NoncurrentVersionExpiration/NoncurrentDays at
https://learn.idrive.com/s3-storage-e2/s3-compatible-api . Permanent expiry reduces
historical recovery protection; exact prefix/rule preview and approval required.

## Approved cloud execution — 2026-10-07

Jason explicitly approved the recommended remote cleanup, old Media retirement,
documentation and push, with another SAS addition only if appropriate. The exact
405 noncurrent guest versions were verified to have current delete markers,
valid guest-archive names and no matching retained Recovery filename. Inventory
was rechecked unchanged under the relay lock before deletion. All 405 version
IDs were acknowledged deleted: 1,021,053,826,174 encrypted bytes removed. All 178
current guest object version IDs and sizes remained unchanged.

Afterward: current 806,037,092,255 bytes; history 17,245,627,590 bytes; total
823,282,719,845 bytes. This is 823.3 GB decimal. Nine lifecycle rules were applied
and read back exactly: noncurrent guest versions 1 day; Gowest family 30 days;
configuration, Home Assistant, Mac, Jellyfin and service-reconstruction/Paperless
configuration prefixes 14 days; expired delete markers removed bucket-wide.
No current-object age expiration or versioning suspension. Family/config history
will expire only according to these approved windows. Existing guest retention
continues to define the dated current archives. Provider lifecycle processing
is asynchronous, so empty guest delete markers may remain temporarily.

Root-only LXC 112 evidence: /var/lib/idrive-version-maintenance/ contains exact
cleanup manifest, acknowledged deleted versions, lifecycle before/request/readback
and usage.json. Permanent version deletion has no rollback. Do not rerun the
fixed 20261007 execution mode; its count/size gates deliberately reject replay.
The first attempt stopped before mutation because this rclone uses cryptdecode
--reverse; the corrected invocation was then validated and executed.

Installed idrive-usage-audit.timer at 10:00 America/Vancouver plus up to five
minutes jitter. Its service calls the script without mutation flags, obtains the
same relay lock, and records aggregate current/history usage. Manual service run
passed. HomeLab Doctor reads that report and warns if older than 30 hours, total
usage exceeds 1 TB decimal, or noncurrent history exceeds 150 GB. This reports
only authorized bucket scope, not account-wide billing. Sixteen backup tests,
Doctor shell syntax and both configuration-backup checks pass.
