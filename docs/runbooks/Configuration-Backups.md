# Configuration backups

> Owner: Jason. Verified deployment: 2026-09-26.
> Scope: all active HomeLab application/infrastructure configurations and
> restoration-critical databases/account state. Bulk media is excluded.
> Immich photos are a separate process owned by Jason.

## Coverage and schedule

| Configuration group | Recurring protection | Restore material |
|---|---|---|
| TrueNAS applications | Daily 05:00 TrueNAS cron task 7 | `/mnt/Media/backup/configuration/truenas/configs.tar.gz` |
| TrueNAS OS / managed apps / browser guards | Same daily export | Native config export including its secret seed; managed-app definitions, Docker inventory/networks, guard definitions and host SSH configuration |
| Synology DSM and Immich | Daily 03:30 DSM `homelab-config-backup.timer`; existing 04:30 TrueNAS family-file pull | `/volume1/homes/.homelab-config-backups/configs.tar.gz`, copied to `/mnt/Media/backup/gowest/homes/.homelab-config-backups/` |
| Proxmox-hosted apps | Existing all-guest nightly 02:30 archives; TrueNAS pull at 04:00 | Guests 100–109, 111–117 in the normal pull; 110 retains its separate 04:20 same-site task |
| OPNsense, Arista, Proxmox host, NUT, monitoring | Existing Sunday 06:00 Mac job; TrueNAS daily 04:15 pull | `~/lab/private-backups/<service>/` |
| Media automation configuration | Same weekly job plus TrueNAS daily tool export | Video archiver, Jellyfin integrity reference manifests and `/mnt/Media/data/tools` |
| Operator lab configuration | Added to existing weekly Mac job | SSH configuration/keys, HomeLab `configs/`, lab LaunchAgents, AsterLab worker identity/custody; `private-backups/operator-configs/` |

Proxmox guest archives cover Docker LXC 100's Homepage, Homarr, code-server,
primary Pi-hole, Portainer, Beszel and other installed guest-local services;
UniFi, Home Assistant, Aster, Authentik, NPM, Forgejo, monitoring, NetBox, wiki,
news, Paperless, speech and OpenBao remain under their guest protection.
External media mounts are not a substitute for configuration backups and are
not included by the new NAS exporters. Relay LXC 112 and OpenBao LXC 117 were
added to the existing TrueNAS pull without changing its schedule or removing
any previous include. OpenBao's independent human recovery shares remain
separate; a vault archive does not replace those shares.

The TrueNAS exporter explicitly covers Newtarr, Sonarr, Radarr, Lidarr,
Prowlarr, SABnzbd, Jellyfin, secondary Pi-hole, File Browser, Dockge, Dozzle,
FlareSolverr, retained Calibre desktop settings, Calibre Web Automated, Seerr, Profilarr and Audiobookshelf.
Stateless containers and ingress services are represented by protected container,
network and deployment definitions. It backs up the actual `/config` Docker
volumes of the ARR applications, not just their mostly empty `/appdata` mounts.
Audiobookshelf's database is selected separately from the adjacent audiobook
folders. Library files, downloads, recordings, transcoding/cache payloads and
Pi-hole DNS-query history are excluded. User/account/library catalogue state,
watch progress, playlists and custom configuration are retained.

Existing family-file protection continues. Paperless whole-guest archives and
LXC 110 model archives retain their prior off-site exclusions; the reviewed
Paperless service reconstruction export remains the off-site exception. This
change does not erase old backups or expand photo/media replication.

## Consistency, privacy and failure handling

- TrueNAS exporter: `scripts/backup/truenas-app-configs.py`, deployed root-only
  at `/mnt/Media/appdata/config-backup-tools/truenas-app-configs.py`.
- SQLite databases use their online-backup API and integrity checks. The copied
  databases are checkpointed into standalone files. Audiobookshelf requires its
  own SQLite 3.44.2 library: its schema is newer than TrueNAS's host library.
  It uses native `VACUUM INTO`, validates the result, and removes the temporary
  container-local file after copying. The live application database is unchanged.
- File Browser's Bolt database is copied during a brief container pause, with
  unpause in a `finally` block. Other services are not stopped by the exporter.
- Unknown configuration mounts, changed expected mounts, repeatedly changing
  files, database or archive errors prevent success publication. Temporary
  candidates are excluded from relay replication. The previous verified archive
  remains available if publication fails; use the manifest/status pair.
- Synology uses vendor `synoconfbkp export`, protected compose/environment
  definitions, PostgreSQL custom-format dumps and role definitions, and a
  supplemental host/package configuration archive. No Immich `library/`, raw
  PostgreSQL data directory or ML model cache is copied. Native pg_dump includes
  application metadata needed when restoring separately backed-up photos.
- Configurations contain credentials. Archives and staging are root-private;
  operator backups are private to Jason. Never print/extract their contents into
  an AI conversation or commit them to Git. TrueNAS's config secret seed is
  intentionally retained so encrypted configuration values are recoverable.
- Source pool snapshots alone are not independent backups. The existing backup
  hub snapshots retain daily/weekly/monthly history; the existing rclone crypt
  relay provides the encrypted off-site copy. Its timer is explicitly 07:00
  America/Vancouver, with the existing 15-minute jitter, after NAS exports and
  snapshots; the prior UTC timer ran before them. Keep its independent protected
  recovery bundle and OpenBao recovery shares available outside their services.
- The Mac weekly wrapper attempts every exporter and reports failure afterward,
  so one unavailable host does not prevent the remaining configurations being
  backed up. No exporter failure is silently treated as success.

## Verification and monitoring

Final TrueNAS export: 17 application entries, 18 SQLite databases, 3,604
verified files, approximately 545 MiB compressed. Calibre desktop settings and
both library catalogues are included without book files. A separate directory restore
matched every file hash; all 18 restored databases passed integrity checks using
an isolated container with no network or production mounts. File Browser’s restored Bolt
database also opened successfully in its isolated exact application image.
The synthetic test
also verifies active-WAL consistency, media exclusions and stale/failed monitor
behavior. A second complete export passed after publication hardening.

Synology export: approximately 52 MiB, 8 verified payload files including both
PostgreSQL databases. Source and TrueNAS-copy SHA-256 matched. Both custom dumps
were restored with the exact pinned PostgreSQL image in an isolated container;
Immich restored 61 tables. The fixture and its volumes were removed. This is a
configuration/database restore, not photo-file restoration or an in-place DSM
rebuild. The DSM vendor export was generated and hash verified; destructive
restoration onto the live NAS was intentionally not performed.

`python3 scripts/check-configuration-backups.py` checks manifest age (<30 h),
expected application/database counts, archive-size consistency, media exclusion,
failure markers, the copied Synology archive and its active timer. Doctor invokes
this check. Existing Doctor checks cover infrastructure exports, guest backup
age, TrueNAS pulls/snapshots and encrypted relay completion. First future
calendar-triggered runs remain observation items; installation, direct execution,
repeatability and recovery have been tested.

## Restoring

1. Identify the service, its image/version and a known-good dated snapshot or
   encrypted object version. Restore into a private scratch directory first.
2. Verify the archive hash and every `manifest.json` file hash. Validate database
   integrity using the matching application/database version, particularly ABS.
3. Restore deployment/environment/network definitions and original account IDs.
   For Jellyfin, restore the SSO config and encryption key together. Recreate
   private guards before exposing an application; never restore passwordless
   backends onto unrestricted host ports.
4. For Immich, initialize the pinned PostgreSQL service and restore roles/database
   following its supported recovery procedure. Restore Jason's separately backed
   photo library at the recorded `/data` mapping. Without that library, a database
   restore alone cannot recover photos.
5. For DSM/TrueNAS, use their supported configuration-import workflow; review
   version compatibility, network settings and recovery access before rebooting.
6. Verify native recovery, SSO, client behavior and account permissions before
   promoting a restored service. Do not overwrite current production databases
   merely to undo an SSO change; that would lose later application state.

Synology's older `systemctl` does not support `enable --now`: use separate
`systemctl enable homelab-config-backup.timer` and `systemctl start ...` commands.
Timer/service definitions are backed up. After a DSM upgrade, verify that the
custom timer remains enabled; Doctor alerts when its status/backup age fails.

## Close-out evidence

- TrueNAS published archive SHA-256:
  `1dfc1686f6ba03b63934c61f86ebda138c5db57e52f50636d423134a73e293d4`.
- Synology published/copied archive SHA-256:
  `0f2ca69285991e4a072380db6b036f1b4ea873b57c6e84a0ec5c4985452b6b80`.
- Operator configuration archive SHA-256:
  `e509fcb319ecf9e2749960ec5a23a8a091c9762a917e2431e9207a42069f5192`.
- TrueNAS pull configuration checkpoint: `/root/config-backup-closeout-20260926`.
- Relay script checkpoint: `/root/idrive-relay-sync.before-config-backups-20260926`.
- Manual hub snapshot: `Media/backup@config-closeout-20260926T2344Z`.
- Fresh changed-guest archives and final off-site round-trip verification are
  still in progress; do not claim project archival until their outcomes are recorded.
