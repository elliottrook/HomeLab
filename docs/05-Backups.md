# Backups

Back up OPNsense, Proxmox, UniFi, Arista, TrueNAS and Synology configurations.

## Handling rules

- Keep exported configurations in encrypted or access-controlled storage.
- Do not commit passwords, password hashes, API keys, Tailscale authentication keys, private SSH keys or raw appliance exports to Git.
- Sanitized examples and documented procedures may be committed to this repository.
- Verify that each archive is readable before relying on it, and record the application version used to create it.
- Copy staged archives off the source host so a single host failure cannot destroy both the service and its backup.

## OPNsense/Arista/Proxmox/NUT/Observability config exports — now weekly, automated

**Automated 2026-09-10.** These five Mac-run config exports (`scripts/backup/{opnsense,arista,proxmox,nut,observability}.sh`) previously had no scheduled trigger at all — only the daily 08:15 Doctor/report job checked their age and alerted past 48h, so they only refreshed when someone ran `lab backup all` by hand (which is exactly why they'd gone stale before). A weekly launchd job (`~/Library/LaunchAgents/ca.yampy.homelab-weekly-backup.plist`, Sunday 06:00, before the daily report) now runs all five directly in sequence. None of the five needed any change to run unattended — they already used key-based SSH/`scp` and (for NUT) `sudo -n` with no password prompts. Verified with a real manual trigger (`launchctl start ca.yampy.homelab-weekly-backup`): all five completed successfully, no stderr output. Output logs: `~/lab/monitoring-state/reports/weekly-backup-{output,error}.log`.

## Verified 2026-08-08 recovery set

The dated recovery set is retained in two locations:

- Mac: `~/Documents/HomeLab-Backups/2026-08-08`
- Backup Synology shared folder: `Backup/HomeLab-Backups/2026-08-08`

The set contains private OPNsense, UniFi, TrueNAS, Homepage, Pi-hole and Tailscale recovery artifacts plus `SHA256SUMS.txt`. The Mac originals were retained after the copy.

The Synology share was mounted over SMB and the set was copied without deleting or replacing the Mac source. Verification was run from the Synology destination:

```sh
cd "/Volumes/Backup/HomeLab-Backups/2026-08-08"
shasum -a 256 -c SHA256SUMS.txt
```

All six protected files reported `OK`. The Synology copy therefore protects against loss of the Mac copy or an individual source host. It is a second-host, same-site copy and does not protect against theft, fire or another site-wide event.

Keep this shared folder restricted to the backup account. The manual dated set remains a known-good baseline; ongoing configuration and guest protection is now automated as described below.

## Automated same-site protection — TrueNAS is the backup hub

**Current architecture, live since 2026-09-08** (`docs/projects/Backup-Architecture-Redesign.md`). TrueNAS (`192.168.20.40`) replaced the Backup Synology as the same-site backup hub, separating three concerns Hyper Backup used to bundle on underpowered hardware: transport, local version history, and off-site protection. Four independent pull relationships land in the shared `Media/backup` ZFS dataset, each with tiered snapshot retention (daily/14-day, weekly/8-week, monthly/6-month):

- **Mac config** — TrueNAS's native `rsynctask` (SSH, a dedicated restricted `rrsync`-confined macOS account `truenas-pull`, OS-level ACL scoped to `~/lab/private-backups` only) pulls to `/mnt/Media/backup/mac`. Daily at 04:15.
- **Proxmox guest archives** — TrueNAS's native `rsynctask` (SSH, the existing restricted `homelab-backup` account, forced `rrsync` rooted at `/mnt/backups/dump`) pulls to `/mnt/Media/backup/homelab-proxmox-guests`. Matches the original redesign scope: 100–109, 111 (NetBox). Daily at 04:00.
- **Aster llama.cpp LXC 110 archives** — a separate TrueNAS `rsynctask` uses the same restricted source account but an exact LXC-110-only include filter and a dedicated `/mnt/Media/backup/aster-lxc110` destination. It runs daily at 04:20 with `delete: true`, so deletion is confined to this directory and the mirror follows Proxmox's bounded archive retention. This large, reproducible inference guest is intentionally excluded from the 1 TB IDrive tier; LXC 104's application/knowledge state remains in the normal encrypted off-site path.
- **`gowest` homes/Family Documents** — a different mechanism than the two above: DSM's own `rsync` daemon proved unusable (four separate SSH-account gates, then an undocumented daemon-module restriction), so `gowest` instead exports `homes`/`Family Documents` read-only over NFSv3 (restricted to TrueNAS's IP, `Squash: No mapping`), TrueNAS mounts both read-only via Init/Shutdown Scripts, and a plain local `rsync` cron job on TrueNAS copies into `/mnt/Media/backup/gowest/`. Daily at 04:30. **Known gap, accepted deliberately:** this does not capture Synology Drive's own `@synologydrive` app-config (315 GB, the actual version-history blob store, not a small index) — no smaller subset exists, so its own multi-version rollback capability is not replicated; current file state is.

All four legs are monitored by HomeLab Doctor's `check_backup_redesign_truenas` — which reads each rsync task's actual job-completion state (not file mtime, which falsely looks stale on a quiet day since rsync preserves source mtimes on unchanged files) and, for the `gowest` leg specifically, a completion-marker timestamp appended to its cron command for the same reason. Initial source/destination verification is recorded in the redesign project's evidence log.

Private keys, authorized-key material, host-key files and backup contents remain outside Git.

## Historical incident — Backup Synology unstable (2026-09-01) — fully resolved and superseded

The original incident (misdiagnosed at the time as general instability; the
real cause, found 2026-09-05, was the unit's 484 MB of RAM failing under
Hyper Backup's dedup/compression/encryption load) led first to
`Backup-Architecture-Redesign.md` making TrueNAS the permanent hub instead
of either Synology, then to `Backup-Synology-Decommission.md`, which
retires the Backup Synology outright. Both projects are substantially
complete: the TrueNAS architecture above has been live and verified since
early September, the Backup Synology's Hyper Backup role was stopped
2026-09-09, and the unit itself was powered down the same day for a 14-day
observation period (ending 2026-09-23) before its disks are considered for
reuse in TrueNAS. See those two project documents for full milestone-by-
milestone evidence. The one-off LXC 100 copy is no longer in use; LXC 110's
former manual one-off was superseded on 2026-09-10 by the bounded recurring
mirror described above.

## Encrypted IDrive e2 off-site backup

**Current architecture, live since 2026-09-08.** A dedicated, minimal, unprivileged Proxmox LXC (VMID 112, `backup-relay`, `192.168.20.33`) reads the TrueNAS `Media/backup` dataset read-only (Proxmox mounts the NFSv4 export and bind-mounts it read-only into the LXC — the relay cannot alter TrueNAS's copy) and relays an encrypted, versioned copy to IDrive e2 via `rclone` with a `crypt` remote layered on top. All CPU-heavy work (encryption, transfer, integrity checking) runs here instead of on either Synology.

- Bucket: `homelab-backup-relay`, region `us-west-4` (`s3.us-west-4.idrivee2.com`), bucket versioning **enabled** — confirmed both that it's turned on and that a genuinely older version is actually retrievable through the crypt layer via `rclone`'s S3 point-in-time read (`--s3-version-at`), not just nominally enabled.
- Credentials: a freshly generated, bucket-scoped IDrive e2 access key limited to this one bucket (never a reuse of the legacy Hyper Backup credential below), plus a separately generated `rclone crypt` password/salt, both root-only on the relay.
- Egress is boundary-limited: a dynamic OPNsense alias resolves only `s3.us-west-4.idrivee2.com`; the relay is permitted DNS/NTP and TCP 443 to that alias and explicitly denied all other egress.
- Sync: a daily `systemd` timer, 20 MiB/s bandwidth cap, non-overlap lock, logged to a protected local log. The canonical command is tracked in `scripts/backup/idrive-relay-sync.sh`; both the dedicated `aster-lxc110` directory and any legacy LXC 110 archive in the shared Proxmox directory are excluded.
- Monitored by HomeLab Doctor's `check_idrive_relay` (guest/timer/service state and post-success log freshness) — covered by the same generic failure-only alerting as every other Doctor check (`scripts/scheduled-report.sh`), no per-service alert wiring needed.

Provisioned capacity is 1 TB. Frigate recordings, media libraries, LXC 110 model archives and unrelated NAS data remain excluded.

**Legacy path, retired 2026-09-09 — do not use for new restores without checking `Backup-Synology-Decommission.md` first.** The Backup Synology ran Hyper Backup task `Mini Atlas Offsite` against a separate, older bucket (`mini-atlas-backups`, same region/endpoint). That task is now stopped (its Task Scheduler entries still show `enabled` since the whole HyperBackup *package* was stopped instead — a CLI attempt to disable just the one task failed silently and root-level API access wasn't available over SSH). Its bucket and credential were never touched or reused by the new relay; the exposed legacy S3 key is a **known, accepted risk** — Jason opted not to rotate it since he is paying IDrive e2 overage for running two buckets simultaneously and intends to decommission that bucket outright soon regardless. Recovery from this legacy bucket, if ever needed before it's decommissioned, still follows the old Hyper Backup Backup Explorer procedure: relink the S3 task with the separately stored legacy credentials, supply the encryption password, and browse versions from there.

Review IDrive e2 service, pricing, recovery performance and capacity by 2027-08-11 — now against the single active bucket. Backblaze B2 remains the documented provider fallback, and the S3-compatible design preserves the option of a trusted remote self-hosted target.

## Synology Drive same-site backup

**Current architecture, live since 2026-09-07.** This is the `gowest` leg of the TrueNAS-hub architecture described above under "Automated same-site protection" — `homes` and `Family Documents` land in `/mnt/Media/backup/gowest/{homes,family-documents}` via NFS export + TrueNAS-side cron, not Hyper Backup. See that section for the mechanism and the accepted `@synologydrive` app-config gap.

**Legacy path, retired 2026-09-10.** The main Synology previously ran Hyper Backup task `Synology Drive Backup` against the Backup Synology (share `Backup`, destination folder `GoWest_2.hbk`) — the same destination repository the pre-existing `Media Backup` task (Plex media, see below) also used. That task is now stopped: Jason stopped HyperBackup on `gowest` entirely, which necessarily also stopped `Media Backup` since both share one HyperBackup package instance on that host — accepted, since `Media Backup`'s own destination (`.42`) was already powered off by then anyway.

`Media Backup` (Plex-era) itself is **not replaced** — Plex source media was already retired in the completed Plex-to-Jellyfin migration, and its stored archive on the Backup Synology is left in place, untouched, undecided, per Jason's explicit decision; see `Backup-Synology-Decommission.md` Milestone 1 and its Milestone 5 blocking condition.

Full detail on the original discovery that led to protecting Synology Drive data at all is in
[docs/projects/completed projects/Synology-Drive-Family-Cloud.md](<projects/completed projects/Synology-Drive-Family-Cloud.md>)
(Milestone 7).

## Docker LXC 100

The service configuration lives under `/opt` inside Proxmox LXC 100 (`docker`). Before a change window, create private staging archives from the LXC shell:

```sh
stamp=$(date +%Y%m%d-%H%M%S)
tar -C /opt -czf "/root/homepage-config-${stamp}.tgz" homepage/compose.yaml homepage/config
tar -tzf "/root/homepage-config-${stamp}.tgz"
```

Treat the archive as private because Homepage configuration may later contain widget credentials. Transfer it to protected backup storage, verify its checksum after transfer, then remove the temporary copy from `/root`.

The Compose definitions are:

- Homepage: `/opt/homepage/compose.yaml`
- Pi-hole: `/opt/pihole/compose.yaml`

Restore into a test directory first, inspect ownership and permissions, validate with `docker compose config`, and only then replace a production configuration.

## Homepage

Homepage's active YAML files are in `/opt/homepage/config`. After restoring them:

```sh
cd /opt/homepage
docker compose config
docker compose up -d
docker compose ps
docker logs homepage --tail 50
```

Confirm `http://home.internal:3000`, the management tiles and all SSH launch links, including Frigate. A Homepage restart is not a substitute for a configuration backup.

## Pi-hole

Create separate Pi-hole Teleporter exports from **Settings > Teleporter** on the primary and secondary instances. Store each with the date, role and Pi-hole version. Teleporter is preferred to copying a live persistent directory because `gravity.db` and `pihole-FTL.db` can change while the service is running. After a restore, validate public resolution, local split DNS and blocking through both endpoints:

```sh
dig +short @192.168.20.20 example.com
dig +short @192.168.20.20 home.internal
dig +short @192.168.20.20 doubleclick.net
dig +short @192.168.20.40 example.com
dig +short @192.168.20.40 home.internal
dig +short @192.168.20.40 doubleclick.net
```

Expected results from either resolver are public addresses, `192.168.20.20`, and a blocking response such as `0.0.0.0`, respectively. OPNsense Dnsmasq advertises both endpoints through DHCPv4 option 6. For rollback, remove or disable that option, apply the Dnsmasq configuration and renew a test client before disabling the scoped Pi-hole firewall exception.

## Tailscale

Record the following without storing authentication keys or reusable tokens:

- `homelab-gateway` machine identity and Tailscale version
- Advertised routes: `192.168.1.0/24` and `192.168.20.0/24`
- Approved route state in the admin console
- Split-DNS route for `internal` through `192.168.1.1`
- Identity-specific access grant for the Trusted and Servers networks
- Explicit exclusion of IoT `192.168.30.0/24` and Guest `192.168.40.0/24`

Keep a private export or controlled copy of the tailnet policy. After recovery, test Homepage and one SSH target from a device using cellular data with Wi-Fi disabled. Do not create a WAN port-forward as a recovery shortcut.

An operational-state snapshot can be staged from LXC 100 with `tailscale version`, `tailscale status` and `tailscale debug prefs`, redirected to a mode-600 file. This snapshot identifies tailnet devices and the account, so transfer it to protected storage, verify its checksum, and remove the temporary LXC copy. It supplements rather than replaces the private control-plane policy copy.

## Frigate

Frigate runs in Proxmox VM 102. Its configuration backup should include:

- `/opt/frigate/compose.yaml`
- `/opt/frigate/config`
- `/etc/systemd/system/frigate-compose.service`
- `/etc/fstab`

Create the archive on the Frigate VM without including the NFS-mounted
recordings directory:

```sh
stamp=$(date +%Y%m%d-%H%M%S)
sudo tar -C / -czf "/home/jelliott/frigate-config-${stamp}.tgz" \
  opt/frigate/compose.yaml \
  opt/frigate/config \
  etc/systemd/system/frigate-compose.service \
  etc/fstab
sudo chown jelliott:jelliott "/home/jelliott/frigate-config-${stamp}.tgz"
chmod 600 "/home/jelliott/frigate-config-${stamp}.tgz"
sha256sum "/home/jelliott/frigate-config-${stamp}.tgz"
```

The archive contains camera credentials. Store it only in protected backup
locations, retain mode `0600`, verify its checksum after transfer and never
commit it to Git. Recordings remain protected separately by the TrueNAS dataset
and its storage-level backup policy.

## Home Assistant

Home Assistant OS runs as Proxmox VM 103 and is included by the enabled
all-guests Proxmox backup job. The Synology Proxmox-pull task includes VM 103
and checksum-verifies the mirrored archives. Home Assistant's own encrypted
backup system provides a separate application-aware recovery path.

The initial full backup, named `Fresh HAOS installation`, was created after
first boot and before integrations were added. Native automatic backups now run
daily, retain three copies and write to both local storage and a network share
over SMB. Backups are encrypted; the emergency kit is retained separately in
the AES-256 `Mini Atlas Recovery Keys.dmg` stored in backed-up iCloud Drive.

**Network share destination redirected 2026-09-10.** Originally the Backup
Synology's `HomeAssistant-Backups` share; now a dedicated TrueNAS SMB share
(`/mnt/Media/backup/home-assistant`, restricted user `ha-backup`, SMB-only,
no shell/broader group membership) as part of `Backup-Synology-Decommission.md`
Milestone 2. Reconfigured via the Supervisor CLI (`ha mounts update`,
reached through `qm guest exec` since HAOS has no direct SSH), keeping the
same mount name (`Backup_Synology`) for continuity in HA's own history.
Verified with a real triggered backup landing correctly on both `.local`
and the new TrueNAS share.

Recovery coverage now includes both paths:

1. Home Assistant native backups are available both locally and on TrueNAS
   for application-aware recovery;
2. the 2026-08-13 VM 103 archive was restored as temporary VM 903 with its NIC
   link disabled, `onboot=0` and a unique MAC. HAOS, Supervisor and Core booted
   successfully without an IP address; VM 903 and its disks were then removed.

HomeLab Doctor checks VM 103 presence and its Proxmox backup age, plus (since
2026-09-10) `check_home_assistant_backup_truenas` for the native-backup leg's
freshness on TrueNAS.

Do not store Home Assistant backup archives in Git. They may contain integration
credentials, device identifiers and household data.

## Aster local-agent service and legacy rollback

Aster LXC 104, llama.cpp GPU LXC 110 and legacy Ollama VM 105 are isolated Lab
VLAN 70 workloads. The Aster application and systemd source are also stored in
Git under `services/aster-agent`; API keys remain only in protected guest
environment files and must never be committed.

The earlier Hermes/Ollama recovery evidence remains valid for the rollback path.
The enabled 02:30 all-guests Proxmox job covered LXC 104 and VM 105, and fresh
local archives for those two guests were verified on 2026-08-19, then mirrored
and checksum-verified to the Backup Synology on 2026-08-20 (that mirror path is
now retired — see "Automated same-site protection" above; both VMIDs are in
the current TrueNAS backup hub's Proxmox-leg scope, 100–109/111). Isolated
restores were then validated: Hermes booted with its dashboard and gateway
processes active, and Ollama reached its Debian login prompt with networking
disabled. LXC 104 has the higher restore priority because it contains the agent
configuration and provider setup, while VM 105 contains the tested Ollama
service and custom model profile. The complete `automated/proxmox-guests`/
`homelab-proxmox-guests` tree is included in the encrypted off-site relay
without separate per-guest selection.

Named `aster-production-20260831` snapshots protect the deployed LXC 104 and
LXC 110 state locally. LXC 110's former off-host gap was closed 2026-09-10 with
the dedicated daily `/mnt/Media/backup/aster-lxc110` mirror described above.
The mirror is covered by the `Media/backup` ZFS snapshot schedules and Doctor,
but deliberately does not enter IDrive: copying the current roughly 38 GB daily
archives through their full retention window would exceed the active 1 TB tier.
The old 2026-09-01 off-site object is left untouched as historical recovery
material; relay exclusions prevent new or replacement LXC 110 uploads.

Do not commit Aster API keys, Hermes tokens, OAuth/provider state, Ollama chat
data or any model configuration containing credentials. LXC 104 and VM 105
have confirmed local, same-site and encrypted off-site coverage. LXC 110 has
local and recurring same-site coverage; its IDrive exclusion is an explicit
capacity boundary, not an untracked gap.

## NUT / UPS Server (Lenovo)

The Lenovo utility host (`nut-server`, `192.168.50.25`) runs NUT on bare
metal, so its recoverable state is a handful of small config files rather
than a Proxmox guest archive. Run `lab backup nut` (or `lab backup all`,
which now includes it) to pull a fresh copy — it lands in
`~/lab/private-backups/nut/<timestamp>/` via
[`scripts/backup/nut.sh`](../scripts/backup/nut.sh).

The four `/etc/nut/*` files are root:nut, mode 640, so `jason` can't read
them directly; the script uses `sudo -n cat` against them. This is backed
by a narrow, fixed-command sudoers rule on `nut-server`
(`/etc/sudoers.d/homelab-backup-nut`, installed 2026-09-02): four exact
`/usr/bin/cat <path>` commands, no wildcards, no shell, NOPASSWD, granted
to `jason` only for this backup pipeline's own read need. `hardening.conf`,
`/etc/network/interfaces` and `hostnamectl` need no elevation and are
pulled as plain `jason`.

This directory is already inside the TrueNAS backup hub's daily Mac-config
pull (04:15) and the encrypted IDrive e2 off-site relay. HomeLab Doctor's
`check_nut` reports live NUT/UPS health, and `check_backup_age "NUT" ...`
reports how stale this config backup is.

**`upsd.users` contains the real `upsmon` monitoring account password.**
Like other credential-bearing backups in this document, keep it within
this protected, git-ignored directory only — never commit it or paste its
contents into a tracked file. The generated password is not recorded
anywhere in the Git repository; it lives only in `upsd.users`/`upsmon.conf`
on the NUT server itself (root:nut, mode 640) and in this backup set.

Recovery outcome: if the Lenovo's disk fails, reinstall Debian, reinstall
the `nut` package set, restore these files to `/etc/nut/` and
`/etc/ssh/sshd_config.d/`, re-run `systemctl daemon-reload` plus
`systemctl enable --now nut-driver@proxmox-ups nut-driver@nas-ups
nut-server nut-monitor`, and verify with `upsc <name>@localhost`. USB
serial pinning in `ups.conf` means both CyberPower units (identical
vendor:product ID) will bind to the correct driver instance regardless of
which physical USB port either one is plugged into.

## TrueNAS

TrueNAS (`192.168.20.40`) system configuration (network, services, users,
pool/dataset layout — not application data, which is covered per-app
elsewhere in this document) is normally exported via the manual, browser-
based guided flow (`lab backup guided` opens **System Settings → General →
Manage Configuration**). That still requires a human to click through and
download the file.

**CLI/API alternative, used 2026-09-01 to avoid the manual step:**
TrueNAS's `config.save` middleware method produces the same export (the
plain configuration SQLite database; `secretseed`, `pool_keys` and
`root_authorized_keys` were all left at their default `false` — deliberately
not included, since those are genuinely sensitive extras not needed for a
routine config backup). Because it's a downloadable job, it needs the
`core.download` wrapper to get an HTTP URL, not a plain `midclt call`:

```sh
midclt call core.download '"config.save"' '[{}]' '"truenas-config.db"'
# returns [job_id, "/_download/<job_id>?auth_token=..."]
curl -s -o /tmp/truenas-config.db "http://localhost/_download/<job_id>?auth_token=<token>"
```

Pulled to `~/lab/private-backups/guided-exports/truenas/
truenas-config-<timestamp>.db` (mode `600`), which lands in the TrueNAS
backup hub's daily Mac-config pull and the encrypted IDrive e2 off-site
relay. The
temporary file on TrueNAS itself and the single-use download token are
not reusable after the transfer. This is a one-off snapshot, not a
recurring task — repeat manually (or automate) as needed; there's no
scheduled job for this today.

## Jellyfin

Jellyfin runs on TrueNAS (`192.168.20.40`) as a Docker Compose service
(container name `6f532232719b…`, not a TrueNAS catalog app). Media is a
host bind mount of `/mnt/Media/data` at `/media` inside the container — that
payload is intentionally excluded from encrypted off-site backup, per the
existing media-exclusion policy above. Separately, Jellyfin's own
application database (users, watch state, playlists, collections, plugin
configuration) lives in a Docker-managed named volume under `Media/ix-apps`,
which is a much smaller, non-replaceable dataset distinct from the media
payload.

**Current coverage is incomplete.** Only three manual, one-off ZFS
snapshots of `Media/ix-apps` exist: two taken as pre-change checkpoints
during the Plex-to-Jellyfin migration project
(`pre-plex-migration-20260830-210033` and
`pre-boxsets-plugin-20260901-100925` — see
[docs/projects/completed projects/Plex-to-Jellyfin-Media-Migration.md](<projects/completed projects/Plex-to-Jellyfin-Media-Migration.md>)),
plus one general point-in-time checkpoint (`config-backup-20260902-004225`,
2026-09-01) taken via TrueNAS's `zfs.snapshot.create` middleware API (the
`truenas_admin` account lacks direct `zfs snapshot` shell permission — use
the API method instead). There is no recurring/scheduled snapshot task for
`Media/ix-apps`, and
neither snapshot is mirrored to the Backup Synology or the encrypted
off-site IDrive e2 task — unlike every other application covered in this
document (Home Assistant, Authentik, Homepage, Pi-hole, etc.), Jellyfin has
no automated backup path at all today. This is a real gap, not a documented
exclusion: the excluded-by-policy item is the media payload, not the
application database.

This matters concretely: on 2026-09-01, a Jellyfin built-in maintenance
task (`Clean up collections and playlists`, triggered on every server
startup) silently deleted 73 real movie collections after a routine
restart, apparently racing ahead of a library re-index. They were
successfully recreated from the Plex-to-Jellyfin migration's own source
data in that case, but a similar or larger loss (e.g. watch history, user
accounts, or the same event without surviving migration source data to
recover from) would not currently be recoverable from anything but those
two stale manual snapshots. See the Milestone 8 section of the migration
doc above for the full incident record.

**It recurred on 2026-09-05** — a TrueNAS reboot fired the same startup
task and destroyed **71** collections (70 with a single member, 1 with
two; small collections are what it targets, which is why the 11 playlists
have never been affected). Restored on 2026-09-06 from the preserved
migration manifests in `~/lab/private-backups/plex-jellyfin-migration/` —
all 71 movie IDs still resolved, which is a direct, real-world validation
of retaining those exports at Milestone 9 closeout.

**Resolved 2026-09-06:** the task's `StartupTrigger` was cleared via
`POST /ScheduledTasks/{taskId}/Triggers` with an empty trigger list, so it
no longer fires automatically. The task itself still exists and can be run
manually from the dashboard if its legitimate function (pruning references
to genuinely deleted media) is ever needed. Trade-off accepted knowingly:
a deleted film may now leave a stale entry in a collection, against no
longer losing ~70 real collections on every restart. To reverse, restore
the trigger with `[{"Type": "StartupTrigger"}]`.

**Recommended follow-up, not yet actioned:** add `Media/ix-apps` (or
specifically Jellyfin's named config volume within it) to a recurring
snapshot schedule and to the TrueNAS backup hub / encrypted off-site
pipeline, following the same pattern already used for Home Assistant and
the other applications in this document. This needs an explicit decision
on schedule and mechanism before implementation — not made unilaterally as
part of documenting current state. (Note: since this data already lives
*on* TrueNAS, "recurring snapshot" is the relevant local-protection piece —
the off-site relay would need this dataset added to its scope separately.)

## Prometheus / Grafana observability

LXC 109 is included automatically by the enabled all-guests Proxmox snapshot
job. Its first archive, created on 2026-08-30, passed a complete Zstandard
integrity test.

The smaller configuration-level recovery set is stored under
`~/lab/private-backups/observability/<date>/` and therefore enters the TrueNAS
backup hub's Mac-config leg and the encrypted IDrive e2 pipeline. The Prometheus archive
contains `/etc/prometheus` and the observability systemd units. The Grafana
archive additionally contains `/etc/grafana`, the provisioned dashboard JSON,
SQLite database, service override and initial administrator recovery
credential. Treat both as sensitive: `pve.yml` contains the read-only Proxmox
API token and the Grafana archive contains authentication state. Keep the
directory and archives owner-only readable and never commit an archive or its
extracted files.

Restore into an isolated temporary directory first. Confirm that
`prometheus.yml`, `pve.yml` and every service unit are present, inspect file
ownership, and validate the Prometheus configuration with `promtool` before
placing files into `/etc`. Reinstall the exact pinned binaries/exporter
environment, restore configuration, reload systemd and start one component at
a time. For Grafana, confirm `grafana.ini`, provisioning YAML, dashboard JSON
and `grafana.db` are present before restoring them with the service stopped.
Validate all Prometheus targets, Grafana's `/api/health` response and the
provisioned data source before returning the dashboard to use.

## NetBox DCIM

LXC 111 is included automatically by the enabled all-guests Proxmox
snapshot job (Layer 1). Because NetBox's Docker Compose stack
(`netbox`, `netbox-worker`, `postgres`, `redis`, `redis-cache`) stores all
of its data — including the Postgres database — as Docker volumes on the
guest's own local filesystem rather than on external/NFS-backed storage, a
snapshot-mode `vzdump` of the whole LXC captures a complete, consistent
point-in-time copy without any special per-component handling, the same
guarantee every other snapshotted guest in this repo already relies on.
There is currently no separate configuration-level recovery set under
`~/lab/private-backups/` for NetBox the way Prometheus/Grafana and NUT
have one — the whole deployment is reproducible from `/opt/netbox` on the
guest (a plain `git clone` of `netbox-community/netbox-docker` plus the
generated `env/*.env` files and `.env`/`docker-compose.override.yml`), so
the LXC-level archive is the only backup this service currently has, by
design rather than by gap.

**Layer 2/3 status: resolved 2026-09-02.** LXC 111 was added to the old
Backup Synology pull's filter on 2026-09-01 but that live DSM task was
never actually updated to match before the whole mechanism was retired.
It's covered now by construction instead: the TrueNAS backup hub's
Proxmox-leg VMID scope (100–109, 111) explicitly includes it — confirmed
live in the redesign project's Milestone 2 evidence (`rsync --list-only`
listed LXC 111's archive already present) — so it gets the same daily
off-host pull and encrypted off-site protection as every other in-scope
guest, no separate NetBox-specific step needed.

**Secrets:** `env/netbox.env`, `env/postgres.env`, `env/redis.env` and
`env/redis-cache.env` under `/opt/netbox/` on the guest contain the
Postgres password, Redis passwords, Django `SECRET_KEY` and API token
pepper — all freshly generated at install time, mode 600, root-owned.
`/root/.netbox-superuser-password` and `/root/.netbox-api-token` are the
same sensitivity. None of these are backed up anywhere except as part of
the whole-guest Proxmox archive; there is no separate copy in
`~/lab/private-backups` to keep in sync, unlike Prometheus/Grafana's
`pve.yml` pattern.

**`/root/.netbox-api-token` reissued 2026-09-04.** The file previously held a
legacy 40-character v1-format token that no longer matched any token in the
database, so the API rejected it with `403 {"detail":"Invalid v1 token"}`.
NetBox 4.6 issues **v2 tokens**, which are stored hashed: only a 12-character
`key` plus an HMAC digest is retained, and the secret is recoverable only at
creation. The file now holds a complete v2 bearer value in the form
`nbt_<key>.<secret>`, used as `Authorization: Bearer $(cat
/root/.netbox-api-token)`.

The reissued token (NetBox token id 9) is deliberately **read-only**
(`write_enabled=False`), since its intended consumers are health checks and
inventory reads. Verified on creation: `GET /api/dcim/devices/` returns 200,
`PATCH` returns 403. Because the secret is unrecoverable after creation, a
lost file means minting a replacement, not reading the value back out.

Two older tokens (ids 2 and 3) remain from install time — both `admin`,
write-enabled and non-expiring, with no description and no known consumer.
Pruning one or both is an open hygiene item, deliberately not done here
because an out-of-repo consumer cannot be ruled out.

**Restore procedure:** restore the LXC from its most recent Proxmox
archive (or the isolated-guest validation pattern used elsewhere in this
document — new VMID, `onboot=0`, network disconnected, inspect before any
start). Because this is a whole-container snapshot rather than a
config-only recovery set, a restored LXC should come back with Docker,
the netbox-docker checkout, and all secrets already in place — verify with
`cd /opt/netbox && docker compose ps` (all five services should report
healthy within a few minutes) and a login test, rather than
re-provisioning from scratch. A from-scratch rebuild (fresh LXC, fresh
`git clone`, fresh secrets) is possible but would lose all entered
inventory data, since nothing outside the guest currently holds a copy of
the Postgres database specifically — treat that path as last-resort, not
routine.

**Upgrade procedure:** NetBox is pinned to `docker.io/netboxcommunity/netbox:v4.6-5.0.2`
in `/opt/netbox/.env`, not `:latest` — matching this repo's pinned-release
convention. To upgrade: take a Proxmox snapshot of LXC 111 first (cheap,
fast rollback path), update the `VERSION` value in `.env` to the target
tag, `docker compose pull`, then `docker compose up -d`. NetBox runs its
own database migrations automatically on container start — watch
`docker compose logs -f netbox` through that process before considering
the upgrade complete, the same way the initial install's migrations were
observed rather than assumed to finish quickly.

## Proxmox guest backups

Proxmox stores `vzdump` archives on the `backups` directory storage at `/mnt/backups`. The mount is a separate 4 TB Seagate ST4000LM024 disk (`/dev/sda1`, ext4). This protects the guests from loss of the Proxmox system disk, but the disk remains physically local to the Proxmox host and is not an off-site copy.

One enabled job backs up all guests daily at 02:30 using snapshot mode and Zstandard compression. Retention is:

- 7 daily copies
- 4 weekly copies
- 6 monthly copies

Two overlapping jobs were disabled on 2026-08-08 after the audit showed redundant same-day archives and missing pruning policies. The jobs remain present but disabled for easy review; disabling them did not delete existing archives.

The newest LXC 100 and LXC 101 archives passed complete `zstd -t` integrity tests. Preview retention before relying on an updated policy:

```sh
pvesm prune-backups backups \
  --dry-run 1 \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6
```

The 2026-08-08 dry run retained the newest archive for each day and marked only four same-day duplicates for removal. Normal pruning will occur after a successful scheduled backup. Do not manually delete the known-good newest archives.

The external disk remains the first local recovery tier. Retained guest archives are now mirrored to TrueNAS (the backup hub) and included in the client-side-encrypted IDrive e2 relay described above.

## Repository credential audit — 2026-08-10

The private Git repository was cloned locally over authenticated SSH and audited without printing candidate secret values.

Checks performed:

- Confirmed the local checkout was clean and synchronized with `origin/main`.
- Searched tracked filenames for private keys, environment files, raw configuration exports, backup archives and credential-related names.
- Scanned the current tracked tree for high-confidence private-key, AWS, GitHub, Tailscale and credential-bearing RTSP URL patterns.
- Scanned every reachable Git commit for the same high-confidence patterns.
- Scanned the current tree for broader password, token, secret, API-key, authentication-key and camera-credential assignment patterns.

Results:

- No suspicious tracked filenames were found.
- No high-confidence secret patterns were found in the current tree.
- No high-confidence secret patterns were found in Git history.
- No credential-assignment patterns were found in the current tree.
- Raw appliance exports, camera credentials, reusable tokens and private keys remain outside Git based on this audit.

This pattern-based audit reduces risk but does not replace credential rotation after any suspected disclosure or GitHub provider-side secret scanning when available.

## Configuration-backup retention policy

Adopted 2026-08-10 for small configuration and recovery archives:

- Daily configurations: retain 7 copies.
- Weekly configurations: retain 4 copies.
- Monthly configurations: retain 12 copies.
- Pre-change recovery checkpoints: retain for at least 90 days.
- Important known-good baselines: retain until a newer baseline has been validated and documented.
- Never delete the only verified copy of any essential recovery artifact.
- Do not enable automatic deletion until automated copying, verification and restore testing are working.
- Keep sensitive archives encrypted or access-controlled throughout their retention period.

This policy covers configuration exports and small recovery archives, not media libraries or Frigate recordings. Proxmox guest archives retain their separately configured policy of 7 daily, 4 weekly and 6 monthly copies.

## Restore validation record — 2026-08-10

Two recovery paths were tested without interrupting production services.

### Homepage configuration and service restore

Source archive:

- Synology path: `Backup/HomeLab-Backups/2026-08-08/homepage-config-20260808-162831.tgz`
- Checksum manifest: `SHA256SUMS.txt`

Validated procedure:

1. Verify the archive against the saved SHA-256 manifest.
2. List the archive before extraction and confirm that all entries remain beneath `homepage/`.
3. Extract into a newly created temporary directory.
4. Parse the restored YAML files without displaying their contents.
5. Transfer the verified archive to a mode-`0600` temporary file on Docker LXC 100.
6. Verify the transferred archive against the original checksum.
7. Extract it outside `/opt/homepage`.
8. Inspect only the Compose service structure, environment-variable names, port and volume definitions.
9. Start a temporary container named `homepage-restore-test` using the existing local image, no restart policy, restored configuration and loopback-only `127.0.0.1:3001` publishing.
10. Confirm the temporary container becomes healthy and returns HTTP 200 locally.
11. Remove the temporary container, extracted files and transferred archive.

Results:

- SHA-256 verification: passed.
- Archive extraction: passed.
- Restored YAML syntax: passed.
- Temporary restored container: `running / healthy`.
- Local HTTP response: `200`.
- Production `homepage` container on TCP 3000: remained running and unchanged.
- Cleanup: completed.

Planning estimate: allow approximately 10–15 minutes for a configuration-level test when the archive and image are locally available, excluding operator pauses. A production recovery may take longer for diagnosis, transfer and post-restore dashboard checks.

### Proxmox LXC guest restore

Source archive:

- `backups:backup/vzdump-lxc-101-2026_08_10-02_30_36.tar.zst`
- Original guest: LXC 101, `unifi-os-server`
- Temporary restore guest: LXC 901

Validated procedure:

1. Confirm the target guest ID is unused and `local-lvm` has sufficient capacity.
2. Run a complete `zstd --test` against the archive.
3. Inspect the embedded guest configuration with `pvesm extractconfig`.
4. Restore to a new guest ID on `local-lvm`, with automatic start disabled and a unique MAC requested.
5. Verify the restored guest is stopped and `onboot` is disabled.
6. Explicitly replace the restored network definition with `ip=manual,link_down=1`; never start a duplicate guest with the production IP address.
7. Mount the stopped guest filesystem with `pct mount`.
8. Confirm the recovered OS metadata, hostname, systemd structure and application-data filesystem are readable.
9. Unmount the filesystem.
10. Destroy only the temporary guest and confirm its temporary logical volume is removed.

Results:

- Zstandard archive integrity: passed.
- Restore to new `local-lvm` volume: passed.
- Restored guest state: stopped.
- Automatic start: disabled.
- Network: unique MAC, no IP configuration and link down before any possible start.
- Restored hostname: `unifi-os-server`.
- Restored filesystem usage: approximately 5.6 GiB.
- Offline filesystem validation and unmount: passed.
- Production LXC 101: remained running and unchanged.
- Temporary guest 901 and `vm-901-disk-0`: removed successfully.

The restore command preserved the backed-up IP address and gateway even though a network override was supplied. Treat post-restore inspection and an explicit disconnected network configuration as mandatory before starting any restored duplicate.

Planning estimate: allow approximately 15–30 minutes for an offline LXC restore test of this size, excluding operator pauses. The archive extraction itself may be much faster on local storage, but safety inspection, network isolation, validation and cleanup are part of the recovery time.

## Recovery order

1. Restore OPNsense routing, firewall, DHCP and DNS.
2. Restore the Arista and UniFi Layer 2 path.
3. Restore Proxmox and LXC 100 networking.
4. Restore Homepage, Pi-hole and the Tailscale subnet router.
5. Validate local access before testing remote Tailscale access.
6. Validate each backup after major configuration changes and before deleting the previous known-good copy.

## Authentik and Nginx Proxy Manager

Before changing Authentik forward auth or NPM proxy host #2, take a consistent
NPM database backup and export the host's current API representation and
`advanced_config`. Protect these artifacts as credentials may be present. Do
not commit the SQLite database, API tokens, Cloudflare token or Authentik
secrets to Git.

Preserve Authentik's database and `/opt/authentik/compose.yml` using the
application's supported backup procedure, recording the deployed Authentik
version. A Proxmox guest backup is useful but does not replace an
application-consistent database backup.

After restoration, validate DNS through OPNsense and both Pi-holes, the
wildcard certificate, NPM syntax, the unauthenticated Authentik redirect, the
password/passkey flow and the final NPM login. See
[the authorization runbook](08-Authorization.md) for the tested order and
targeted rollback procedure.

## Critical-Service Recovery Coverage — 2026-08-20

This matrix reconciles operational monitoring, same-site protection and tested
recovery evidence. A service does not require an individual destructive restore
when its recoverability is inherited from a tested platform archive and its
configuration is separately documented or exported.

| Component | Monitoring | Same-site protection | Restore evidence or recovery status |
|---|---|---|---|
| OPNsense | Doctor checks Internet, WAN state and service reachability; configuration drift is monitored | Automated configuration export, checksum and TrueNAS backup-hub mirror | Configuration recovery is documented; a live firewall replacement restore remains intentionally untested because it would disrupt the network |
| Arista core switch | Doctor checks expected links, temperature, PSU state and interface-error baselines; configuration drift is monitored | Automated running-configuration and state export with verified mirror | Configuration replacement is documented; destructive production restore is intentionally deferred |
| Proxmox host | Doctor checks guests, storage, memory and swap; Beszel supplies history; TLS expiry and configuration drift are monitored | Host configuration export plus retained guest archives on local backup storage and the TrueNAS backup hub | Multiple isolated guest restores prove archive usability; complete bare-metal host recovery remains a documented manual procedure |
| Docker LXC 100 | Doctor checks SSH and hosted service endpoints; Beszel monitors the host and containers | Current LXC archive retained locally and checksum-mirrored to TrueNAS | Homepage application recovery was tested independently; Proxmox LXC recovery was validated using an isolated disposable guest |
| UniFi LXC 101 | Doctor checks controller reachability | Current LXC archive plus UniFi application backups, mirrored off-host | Isolated LXC restoration and recovered UniFi database inspection succeeded |
| TrueNAS | Doctor checks pools, NFS, bond health and management access; certificate expiry is monitored | System configuration export (`config.save`, via CLI/API or the guided browser flow) is included in the protected infrastructure set; ZFS protects local media integrity | Configuration recovery is documented; media is intentionally excluded from encrypted off-site backup because of size and replaceability. Export is currently manual/one-off, not scheduled |
| Jellyfin (on TrueNAS) | No dedicated Doctor check yet | **Incomplete** — only three manual, one-off `Media/ix-apps` snapshots exist (two migration-project checkpoints plus one general checkpoint, 2026-09-01); no recurring snapshot schedule and no off-site relay coverage for the application database (playlists, collections, users, watch state) | Not tested; see the "Jellyfin" section above for the 2026-09-01 incident that exposed this gap and the recommended follow-up |
| Pi-hole primary and secondary | Doctor performs public, local and blocked-domain DNS tests through both resolvers | Primary inherits Docker LXC protection; secondary inherits TrueNAS application/configuration protection; Teleporter exports are documented | Functional recovery validation is performed through the redundant resolver pair; either resolver can carry DNS while the other is rebuilt |
| Frigate VM 102 | Doctor checks VM/service state, NFS mount and recording freshness; Beszel tracks host metrics | Current VM archive and private checksum-verified Frigate configuration backup, mirrored off-host | VM-level recovery is available; recordings remain intentionally excluded because they are high-volume and nonessential to infrastructure recovery |
| Home Assistant VM 103 | Doctor checks Core and backup age, plus `check_home_assistant_backup_truenas` for the native-backup leg | Encrypted native backups to local storage and a dedicated TrueNAS SMB share (redirected from the Backup Synology 2026-09-10) plus current mirrored VM archives | Isolated VM 903 restored and booted HAOS, Supervisor and Core successfully; the TrueNAS redirect was verified with a real triggered backup landing correctly on both locations |
| Main Synology (`gowest`) | Doctor checks DSM reachability | `homes`/`Family Documents` mirrored to the TrueNAS backup hub daily (NFS export + TrueNAS-side cron), with encrypted off-site protection via the relay. `gowest` is a source only — no backup data lands on it | Byte-exact verified against source (2026-09-07); real restore proven via the TrueNAS backup hub's dual-restore gate. Its own former Hyper Backup jobs (`Synology Drive Backup`, `Media Backup`) are retired/stopped, see `Backup-Architecture-Redesign.md` |
| Backup Synology (`.42`) | Doctor's `check_home_assistant_backup_truenas` and TCP checks will show it unreachable — expected, tracked in `Backup-Synology-Decommission.md` | **Retired 2026-09-09.** Powered down for a 14-day observation period (ends 2026-09-23) before its disks are considered for reuse in TrueNAS. Everything it protected has a live TrueNAS-hub replacement except `Media Backup`'s stored data, deliberately left in place, untouched, undecided | Every replacement leg's restore was proven before this unit was touched — see `Backup-Synology-Decommission.md` Milestone 3. This row will be removed after the observation period per that project's Milestone 4 |
| Aster Agent LXC 104 | Doctor checks guest, service and API health | Current LXC archive retained locally and checksum-mirrored to TrueNAS; named production snapshot retained locally | Earlier isolated restore as LXC 972 booted the retained Hermes rollback services; Aster boot persistence was validated in place |
| Legacy Ollama VM 105 | Doctor checks guest state according to its intended operating mode | Current VM archive retained locally and checksum-mirrored to TrueNAS | Isolated restore as VM 973 reached its login prompt successfully |
| Aster llama.cpp LXC 110 | Doctor checks guest/inference health, local archive age, bounded TrueNAS task configuration/run freshness and mirrored archive age | Named production snapshot, current local archives and a dedicated daily TrueNAS mirror following Proxmox retention; explicitly excluded from the capacity-limited IDrive tier | Isolated archive restore as stopped, network-isolated LXC 980 verified both active model blobs and service layout; do not start a second GPU-mapped guest during production service |
| Authentik LXC 106 | Doctor checks service reachability through the configured endpoint | Current LXC archive retained locally and checksum-mirrored to TrueNAS | Platform-level recovery inherits the validated Proxmox LXC restore process; Authentik configuration is documented separately |
| Reverse Proxy LXC 107 | Doctor checks NPM service reachability and TLS dependencies | Current LXC archive retained locally and checksum-mirrored to TrueNAS | Platform-level recovery inherits the validated Proxmox LXC restore process; proxy and Authentik recovery order is documented |
| Forgejo LXC 108 | Doctor checks service reachability; Beszel records host health | Current LXC archive retained locally and checksum-mirrored to TrueNAS; GitHub remains a synchronized off-site Git remote | Isolated restore as LXC 978 verified the active Forgejo service, SQLite database and `jason/homelab.git`, then the test guest was removed |
| Observability LXC 109 | Prometheus self-monitors and all seven initial scrape jobs are health-checked; Doctor integration follows after Grafana stabilizes | Protected configuration archive plus the retained all-guests LXC snapshot; both enter the existing Synology/off-site pipeline | Configuration archive extracted and checked in isolation; first LXC archive passed complete Zstandard integrity testing |
| NetBox LXC 111 | Doctor's `check_netbox` covers all five container health states and the login-page response | Local Proxmox archive plus TrueNAS backup-hub off-host mirror (VMID 111 is explicitly in scope) and encrypted off-site relay; by design there is no separate config-level recovery set, since the whole deployment is reproducible from `/opt/netbox` on the guest | Not yet isolated-restore tested; deployment is new (2026-09-01) |
| Backup Relay LXC 112 | Doctor's `check_idrive_relay` covers guest/timer/service state and post-success log freshness | Local Proxmox archive only — deliberately not on the off-site relay's own scope (it relays other guests' backups, not itself) | Not yet isolated-restore tested; deployment is new (2026-09-07) |
| NUT server (Lenovo, bare metal) | Doctor checks `nut-server`/`nut-monitor` state, all three UPS units' `ups.status` and battery charge, and config-backup age | `lab backup nut` pulls the config set (`ups.conf`, `nut.conf`, `upsd.users`, `upsmon.conf`, SSH hardening, network config) via a narrow NOPASSWD sudoers rule, landing in the TrueNAS backup hub's Mac-config leg and encrypted IDrive e2 off-site relay, same as other appliance configs | Live driver/server configuration validated via `upsc`; a full bare-metal OS reinstall has not been tested, only documented as a recovery procedure |
| Reolink camera | Doctor tests HTTP, RTSP and ONVIF reachability; Frigate proves recording flow | No recording archive is required; Frigate configuration preserves the integration settings | Camera replacement or reset is a documented reconfiguration task rather than a backup restore |

### Accepted recovery boundaries

- Full destructive restores of the production firewall, switch, TrueNAS and both
  Synology appliances are not justified solely to prove procedures that already
  have verified exports, documented recovery steps and representative restore
  evidence.
- Media libraries and Frigate recordings are intentionally excluded from
  encrypted off-site protection because their size exceeds their recovery value.
- Aster LXC 110 model archives receive local snapshots/archives and a recurring
  TrueNAS mirror but are intentionally excluded from the 1 TB encrypted off-site
  tier. LXC 104 holds the smaller application and knowledge state and remains
  protected off-site.
- Aster LXC 104 and legacy Ollama VM 105 have verified same-site/off-host archives,
  isolated restore tests and encrypted off-site protection through the selected
  `homelab-proxmox-guests` tree.
- TrueNAS (the backup hub) is a recovery repository, not the only copy of
  essential configuration or guest data. Neither Synology is a backup
  destination any longer — `gowest` is a source only, and the Backup
  Synology is retired.
