# Backup coverage audit — 2026-09-26

Read-only evidence: TrueNAS `pool.snapshottask.query`, `rsynctask.query`,
`cronjob.query`, `replication.query`, ZFS mount inventory and running Docker
mounts; Proxmox `/etc/pve/jobs.cfg`; existing backup runbooks. This is a scope
assessment, not proof of every scheduled run or exhaustive application restore.

## Confirmed scheduled-protection gaps

TrueNAS has four snapshot tasks: non-recursive `Media` daily and non-recursive
`Media/backup` daily/weekly/monthly. No ZFS replication tasks exist. Pull jobs
cover scoped Proxmox archives, Mac private backups and LXC 110; the family-file
cron copies Synology homes/Family Documents. No general NAS app-data export
appears in those schedules. Local application self-backups may exist, but copies
on the same unprotected storage do not establish independent recovery.

- Jellyfin `/config`: `Media/appdata/jellyfin`. Users, watch state, collections,
  playlists and SSO configuration have verified manual checkpoints from today,
  but no recurring snapshot or independent copy in the inspected pipeline.
- Sonarr, Radarr, Lidarr, Prowlarr and SABnzbd: both `/appdata` child datasets
  and actual `/config` Docker volumes under `Media/ix-apps/docker` are outside
  scheduled snapshots. Protect the actual database/config volumes, not merely
  similarly named `/appdata` directories.
- Newtarr, Seerr, Profilarr, Dockge and Dozzle: application state resides in
  unscheduled `Media/appdata` or child datasets.
- Secondary Pi-hole and File Browser: managed app configuration / Docker
  database volumes under `Media/ix-apps` have no scheduled snapshot coverage.
  Pi-hole has a verified manual checkpoint and copied guard reconstruction
  bundle; neither is recurring application-data coverage.
- Audiobookshelf: `/config` is under `Media/media/audiobooks`, and `/metadata`
  under its `Media/ix-apps/app_mounts` child dataset; neither is scheduled.
- Browser guard configurations in `Media/appdata`: no broad scheduled coverage;
  Pi-hole's explicitly exported reconstruction bundle is an exception.

Calibre Web Automated configuration is `/mnt/Media/apps/calibre-web-automated/config`,
which falls within the top-level `Media` filesystem in the inspected dataset
map and therefore its local snapshot. Its library is in child `Media/media`.
No independent recurring Calibre configuration copy was established.

Other child datasets (`Photos`, `homes`, `Jason_Home`, `Notes`, `Nextcloud_data`,
`shared`, older `configs/*`) are also outside these snapshot tasks. Existence
alone does not prove active, unique content; classify their contents before
calling them empty, disposable, or safe to delete.

## Partial coverage and deliberate exclusions

- Immich on Synology: native database backups enabled with retention 14; the
  rollout dump was verified. Current SSH access cannot inspect Docker mounts.
  Recurring photo/video backup and independent copies of its DB are unverified.
  Synology homes/Family Documents coverage alone does not prove Immich coverage.
- Synology Drive version-history store is an accepted exclusion; current family
  files are copied, but the approximately 315 GB history store is not.
- Media payload and Frigate recordings are intentionally excluded from off-site
  backup. Frigate's VM/configuration has separate coverage.
- LXC 110 models and Paperless LXC 115 document archives have local/TrueNAS
  protection but are deliberately excluded from the off-site tier. Paperless's
  reviewed service reconstruction export is a separate off-site exception.
- Relay LXC 112 is locally archived but absent from the TrueNAS pull filter.
- Proxmox's all-guest nightly schedule is active. The live TrueNAS pull includes
  100–109, 111, 113–116; 110 has its separate task. A configured schedule is not
  itself proof that the newest archive succeeded or was restored.

No backup schedule, replication scope or retention was changed by this audit.
New recurring protection needs an explicit scope decision; do not silently add
personal data to off-site replication. Snapshots on the source pool do not
protect against loss of that pool.
