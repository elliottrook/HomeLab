# Recovery backup migration — 2026-10-05

Status: MIGRATION COMPLETE 2026-10-05 18:38 PDT. Old-source retirement pending next scheduled cycle.
Authorization: Jason explicitly requested migration to the new SATA mirror and
an ETA. Stream M, this bounded migration approved as a whole; no source/history
purge, photo ingestion, unrelated SAS expansion or Git push.

## Scope and preflight

Both SATA extended tests passed. Recovery is ONLINE, 3.51 TiB available. Media
seven-disk expansion and post-expansion scrub completed without errors. Existing
backup pull/guard/cloud cycle succeeded today. Live backup data approximately
1.13 TiB; old Media/backup history is intentionally not migrated wholesale.
Current source retained for recovery, no deletion until verified cutover/restore.
Only backup-relay LXC 112 may need a brief stop/restart to change its read-only
mounts. Home Assistant backup share path changes require reconnect validation;
Home Assistant itself is not to be restarted as a default.

## Copy map

| Source under Media/backup | Target under Recovery |
|---|---|
| homelab-proxmox-guests | guests/homelab-proxmox-guests |
| aster-lxc110 | guests/aster-lxc110 |
| gowest | family/gowest |
| configuration | configuration/exports |
| mac | configuration/mac |
| home-assistant | configuration/home-assistant |
| jellyfin | configuration/jellyfin |
| paperless-service | configuration/paperless-service |
| service-reconstruction | configuration/service-reconstruction |

Recovery/photos remains empty; no reconciled photo migration is authorized by
this backup copy. Existing family-file content stays in its current backup scope.

## Execution and resumability

Source checkpoint: `Media/backup@recovery-migration-20261005` created with all
current backup folders. This does not include old snapshots. Worker copies from
that immutable point using rsync -aHAX --numeric-ids, then performs a full
checksum/metadata dry-run comparison for every mapped tree. Dry-run --delete
only detects unexpected target extras; it does not delete files.

Worker: `/mnt/Media/backup-ops/recovery-migration-20261005/copy.py`, initial PID
161223. State `status.json`, protected per-tree copy/verify logs and `worker.log`
in that directory. Local source: scripts/backup/recovery-migration-copy.py.
Phase reaches `ready-for-final-delta` only after every comparison has no differences.
Failures record phase=failed and error; no cutover occurs automatically. Re-running
copies only changed/missing files and then rechecks; inspect failure first.
No credentials or private file contents are emitted to session/Git.

At approximately 10:03 PDT transfer was 160–190 MiB/s. Initial end-to-end estimate
6–10 hours allows for small-file overhead, full verification and cutover. Rates
are early and not a completion guarantee. Source payload approximately 1.245 TB
logical. Native backup jobs continue using Media while the baseline copy runs.

## Cutover checklist — not yet executed

1. Require successful full baseline comparison. Record current source producer
   state and checkpoint only relevant TrueNAS task/share settings, Proxmox fstab,
   LXC 112 config and relay script/service under protected root-only paths.
2. Confirm no live rsync/relay jobs, pause relay timer and TrueNAS producers
   (rsync 1–3, cron 1/7/8) temporarily; freeze Home Assistant backup SMB writes
   briefly during its final delta. Identify any remaining writers before moving.
3. Final live delta for each mapping, with checksum verification. Inspect exact
   destination-only files before any target-only deletion; never remove source.
4. Update TrueNAS rsync 1/3 to Recovery/guests paths, task 2 to
   Recovery/configuration/mac. Cron 1 writes Recovery/family/gowest. Config-export
   ROOT and cron 7 log target move to Recovery/configuration/exports/truenas.
   Retention guard ROOT moves to Recovery/guests/homelab-proxmox-guests; its
   non-backup operational state can remain in Media/backup-ops for this phase.
5. SMB share 4 retains name home-assistant and its ACL but targets
   Recovery/configuration/home-assistant. Verify service-account write/access;
   root traversal permissions may require a narrow execute ACL, not broad reads.
6. Expose only Recovery/guests, family and configuration through separate read-only
   NFS exports to existing authorized Proxmox host 192.168.50.10, preserving
   root mapping and no wider network trust. Mount these explicitly on Proxmox;
   give LXC 112 three read-only bind mounts at /srv/recovery/{guests,family,configuration}.
   No assumption that an NFS parent export traverses child ZFS datasets.
7. Install source identity markers outside copied subtrees and verify all mount
   identities. Candidate scripts/backup/idrive-recovery-relay-sync.sh maps each
   source tree to its EXISTING cloud prefix and preserves 110/115 exclusions.
   Update systemd mount conditions to the new three mountpoints. First use
   rclone dry runs and require no unexplained cloud deletions before live relay.
   Current cloud script remains deployed until then; no dual scheduled relay.
8. Update monitoring paths in Doctor/check-configuration-backups and manual
   reconstruction exporter. Resume schedules, exercise bounded producer paths,
   verify configuration archive restoration and selected guest integrity, run
   relay and confirm unchanged privacy/exclusion boundaries.
9. Set reviewed bounded snapshot retention on new family/configuration datasets;
   do not replicate layered full guest history onto the guest dataset. Retain
   old snapshots for now; avoid leaving new snapshots accumulating on old source
   after cutover. Recovery photos policy waits for actual photo reconciliation.
10. Preserve old source until successful new scheduled cycle and restore evidence.
    Document source retirement separately with exact candidate scope. No blanket
    deletion of Media/backup or historical cloud versions in this migration.

## Recovery and remaining gates

Until cutover, all original jobs keep running unchanged. If the copy fails, stop
and repair destination only. During cutover, restore exact old task/share/mount
settings to resume old source; never operate two cloud relays simultaneously.
Do not claim completion from file copy alone. Completion requires verified data,
working producers/readers, tested recovery, monitoring and documented retention.
No further disks/pools/apps/public exposure/credential changes are part of scope.
NetBox addressing and rack layout are unaffected. Update operational/wikified
storage guidance after cutover; this runbook and TrueNAS live state are authority.

## Cutover evidence — October 5 evening

All nine baseline trees completed full checksum/metadata verification. Final
live comparison found zero changes in eight trees; only TrueNAS export files
changed, and their delta was copied and checksum-compared successfully.
TrueNAS checkpoint: pre-cutover-settings.json in the protected migration ops
directory. Proxmox and relay checkpoints: /root/recovery-cutover-20261005.

- Rsync 1/2/3 now target Recovery and all three manual runs succeeded (jobs
  7878/7879/7880). The source export is restricted rrsync, so generic remote path
  validation cannot execute; enabled updates used validate_rpath=false after
  real successful source pulls. Schedules restored unchanged.
- Gowest final pull to Recovery/family succeeded. Guest guard completed with zero
  candidates; Doctor retention check passed and eight guard regression tests pass.
- NFS exports 4/5/6 expose only guests/family/configuration read-only to
  192.168.50.10 using the same root mapping as before. Proxmox fstab and LXC 112
  mp0/1/2 now use these mounts. Identity markers verified inside LXC.
- Old relay NFS mount unmounted and old NFS share 3 disabled. LXC 112 was briefly
  restarted; no other guest restarted. Cloud timer restored; first new live relay
  pending completion. Dry run completed with zero proposed deletions/errors and
  five copies for configuration changes. LXC 110/Paperless exclusions preserved.
- SMB share 4 keeps its name and uses the new home-assistant path. Existing CIFS
  client needed a mount-unit reconnect after the server path changed. Restarted
  only mnt-data-supervisor-mounts-Backup_Synology.mount, not Home Assistant.
  Synthetic write confirmed on Recovery and absent from old Media, then removed.
  UID 3001 received traverse-only ACL on Recovery and configuration parents;
  backup-folder ACL/ownership retained, no broad listing/read permissions added.
- Restored and hash-verified 3,705 configuration files from the migrated archive;
  archive SHA-256 matched its status. This is file restoration proof, not a new
  whole-guest boot restore. Synthetic restore removed.
- Snapshot tasks 5–10 cover family/configuration: 14 daily, 4 weekly, 3 monthly.
  Initial snapshots taken. Old Media/backup tasks 2/3/4 disabled, histories retained.
  No repeated guest-archive snapshot layer was enabled.

A fresh config export exposed two newly running shadow apps outside the previous
allowlist (unified-lazylibrarian-shadow and unified-audiobookshelf-shadow).
Their /config mounts total about 3 MiB and are separate from media libraries.
Exporter coverage is being extended narrowly, with Audiobookshelf using its
bundled SQLite backup API; validation must pass before claiming config protection
healthy. No application configuration or media source is changed by this fix.

At 18:35 PDT the new configuration export passed: 20 applications, 21 SQLite
checks, 3,746 archive file hashes verified, 573,905,800-byte archive, media
excluded. Both TrueNAS and Synology configuration monitoring checks pass. The
new Audiobookshelf instance uses its own bundled SQLite runtime (instance-specific
regression test added); the generic SQLite attempt was rejected and did not
replace the prior good archive. Failure marker cleared after successful publish.
Guest/family/config jobs and cloud timer are enabled. New cloud run is still
being validated; do not rerun the baseline copy worker after cutover.

First complete Recovery relay succeeded at 18:36:51 PDT. Its scan began before
the final new configuration export published, so a cryptcheck correctly found
the cloud archive was an older size. A bounded configuration-only final sync is
running before repeating cryptcheck; this is a source-generation race, not a
baseline migration checksum failure. No old backups have been deleted.

## Completion — 18:38 PDT

Configuration-only final sync succeeded (two updated files; obsolete failure
marker removed), then the latest encrypted cloud configs.tar.gz passed cryptcheck
with one match and zero differences. Both configuration checks and all targeted
backup freshness/retention checks pass. All pools healthy. Eleven backup tests
pass; shell syntax and diff whitespace checks pass. No cloud key prefix changes.

Migration state phase is complete. All producer schedules and cloud timer enabled;
Recovery is the live backup destination. Old Media backup files, snapshots and
checkpoint remain intact. Next overnight cycle is the source-retirement gate;
source deletion is not included in this completion. Do not restart the baseline
copy worker against now-live Recovery. To roll back, pause producers/relay, account
for any NEW Recovery writes, restore protected task/share/mount checkpoints and
validate before resuming; simply reverting paths can omit newer recovery points.

No additional SAS disk was added. Recovery/photos remains reserved and empty.
Original photo-source reconciliation/Google retirement remains a separate phase.
Git changes are local only until push approval. The two shadow configuration
allowlist entries must be reviewed when their owning project retires those
containers; the unknown-app/missing-app guards remain enabled.
