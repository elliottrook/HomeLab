# Backups

Back up OPNsense, Proxmox, UniFi, Arista, TrueNAS and Synology configurations.

## Handling rules

- Keep exported configurations in encrypted or access-controlled storage.
- Do not commit passwords, password hashes, API keys, Tailscale authentication keys, private SSH keys or raw appliance exports to Git.
- Sanitized examples and documented procedures may be committed to this repository.
- Verify that each archive is readable before relying on it, and record the application version used to create it.
- Copy staged archives off the source host so a single host failure cannot destroy both the service and its backup.

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

## Automated same-site protection

The Backup Synology at `192.168.20.42` pulls rather than receives pushed data, so scheduled work does not depend on a mounted Mac SMB share.

Configuration recovery sets are pulled daily at 21:00 from the Mac source `~/lab/private-backups` into `Backup/HomeLab-Backups/automated/private-backups`. The task uses a dedicated Synology-held SSH key restricted on the Mac to the Backup Synology source address. It performs an additive rsync copy followed by a checksum-mode dry run. Success and diagnostic state is recorded in:

- `synology-pull-latest.status`
- `synology-pull-last-success.txt`
- `logs/synology-pull-latest.log`

Proxmox guest archives are pulled daily at 03:30, after the 02:30 Proxmox backup job, into `Backup/HomeLab-Backups/automated/proxmox-guests`. Proxmox account `homelab-backup` has a locked password and no administrative group membership. Its authorized key is source-restricted to the Backup Synology and forced through read-only `rrsync` rooted at `/mnt/backups/dump`. The canonical filtered mirror includes LXC 100, LXC 101, QEMU 102, QEMU 103, LXC 104, QEMU 105 and LXCs 106–109. The live DSM task has matching copy and checksum filters for all ten protected guests. A checksum-mode dry run must be empty before success is recorded in:

- `proxmox-pull-latest.status`
- `proxmox-pull-last-success.txt`
- `logs/proxmox-pull-latest.log`

The canonical replacement body for the DSM scheduled task is tracked as
`scripts/backup/synology-proxmox-pull.sh`. It includes matching copy and
verification filters for all ten protected guests. The LXC 109 filter is
deployed in the enabled live DSM scheduled task. On 2026-08-31, the two
retained LXC 109 archives were copied to the Backup Synology and a focused
checksum-mode comparison completed with zero differences.

Both production tasks write `0` only after copy and verification succeed. On failure they invoke the Mac over the existing restricted SSH path, where `scripts/backup-alert` uses Apple Mail to send an actionable email. Successful runs deliberately send no email. The manual `lab backup synology-copy [--dry-run]` command remains available as an operator-controlled fallback; it is not part of `lab backup all` and is not the unattended production path.

Private keys, authorized-key material, host-key files, email credentials and backup contents remain outside Git.

## Encrypted IDrive e2 off-site backup

The Backup Synology runs Hyper Backup task `Mini Atlas Offsite` against a private IDrive e2 S3-compatible bucket in Oregon-2. The task uses the region-specific endpoint `s3.us-west-4.idrivee2.com` and a bucket-scoped read/write access key that may delete objects for retention pruning but may not delete the bucket. Access and secret keys are not recorded in this repository.

Selected sources are limited to:

- `Backup/HomeLab-Backups/automated/private-backups`
- `Backup/HomeLab-Backups/automated/proxmox-guests`

Frigate recordings, media libraries and unrelated NAS data are excluded. The provisioned capacity is 1 TB; the earlier approximate 500 GB planning assumption was superseded by the provider's current minimum plan.

Hyper Backup settings:

- Daily schedule: 22:00, after the 21:00 configuration pull
- Integrity check: Sunday at 04:00
- Transfer compression: enabled
- Client-side encryption: enabled
- Rotation: enabled, maximum 23 versions
- Customized retention: daily for the newest week, weekly through the newest month and monthly thereafter
- Task notifications: enabled

The encryption password and exported private recovery key are stored separately from the Synology in encrypted, backed-up recovery storage. Loss of both makes the repository unrecoverable. Do not store either in Git, the IDrive bucket or an unencrypted Downloads folder.

Validated 2026-08-11:

- Initial encrypted upload completed without an error notification.
- Backup Explorer opened and displayed readable configuration data.
- An LXC 100 archive recovered through Hyper Backup matched the same-site Synology source exactly by SHA-256.
- A second Hyper Backup run created a new version and included the 2026-08-11 archives for LXC 100, LXC 101 and QEMU 102.
- Backup Explorer showed two versions at 00:48 and 12:19; file-change detail logging was intentionally left disabled, so per-file cloud-transfer records are not expected in the same-site pull logs.

Recovery procedure:

1. Install Hyper Backup on a supported Synology system.
2. Relink the existing S3 task using the Oregon-2 endpoint, private bucket and separately stored bucket-scoped credentials.
3. Supply the client-side encryption password or import the separately stored recovery key.
4. Use Backup Explorer to select the required version and inspect or download individual files before restoring production data.
5. For a guest archive, compare the recovered file's SHA-256 digest with a trusted manifest or surviving verified copy before using `pct restore` or `qmrestore`.
6. Restore a guest under a new ID with automatic start disabled and networking isolated; inspect it before any start, following the validated guest procedure below.

Review IDrive e2 service, pricing, recovery performance and capacity by 2027-08-11. Backblaze B2 remains the documented provider fallback, and the S3-compatible design preserves the option of a trusted remote self-hosted target.

## Synology Drive same-site backup

The main Synology (`192.168.20.41`) runs Hyper Backup task `Synology Drive
Backup` against the Backup Synology (`192.168.20.42`, share `Backup`,
destination folder `GoWest_2.hbk`) — the same destination repository already
used by the pre-existing `Media Backup` task (Plex media only; that task was
not otherwise touched by this work). Before this task existed, there was no
backup coverage at all for user data on the main NAS.

Selected sources:
- Shared folder `homes` (personal My Drive folders for every family account)
- Shared folder `Family Documents` (the shared Team Folder)
- Application data: `SynologyDrive` (Team Folder/sharing/quota/retention
  settings) and `HyperBackup` (the backup tool's own configuration)

Hyper Backup settings:
- Daily schedule: 00:00
- Integrity check: Monday 04:00
- Rotation: enabled, keep the most recent 30 versions
- Client-side encryption: not enabled — a deliberate choice, since this is a
  same-LAN NAS-to-NAS backup rather than an off-site one, so encryption in
  transit/at rest is a lower-priority tradeoff here than for the IDrive e2
  off-site backup above (which is encrypted)

Capacity: the backed-up data currently totals ~121 GB, against 1.4 TB free on
the Backup Synology at the time this task was created — comfortable, but this
destination has less headroom than the main NAS overall and is shared with
Plex's media backup, so it's the more time-sensitive one to periodically
recheck as data grows. Full detail, including the discovery that led to
creating this task, is in
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
daily, retain three copies and write to both local storage and the dedicated
Backup Synology `HomeAssistant-Backups` share over SMB. Backups are encrypted;
the emergency kit is retained separately in the AES-256 `Mini Atlas Recovery
Keys.dmg` stored in backed-up iCloud Drive.

Recovery coverage now includes both paths:

1. Home Assistant native backups are available both locally and on the Backup
   Synology for application-aware recovery;
2. the 2026-08-13 VM 103 archive was restored as temporary VM 903 with its NIC
   link disabled, `onboot=0` and a unique MAC. HAOS, Supervisor and Core booted
   successfully without an IP address; VM 903 and its disks were then removed.

HomeLab Doctor checks VM 103 presence and its Proxmox backup age. The existing
Synology pull reporting verifies completion of the off-host guest mirror.

Do not store Home Assistant backup archives in Git. They may contain integration
credentials, device identifiers and household data.

## Aster local-agent service and legacy rollback

Aster LXC 104, llama.cpp GPU LXC 110 and legacy Ollama VM 105 are isolated Lab
VLAN 70 workloads. The Aster application and systemd source are also stored in
Git under `services/aster-agent`; API keys remain only in protected guest
environment files and must never be committed.

The earlier Hermes/Ollama recovery evidence remains valid for the rollback path.
The enabled 02:30 all-guests Proxmox job covered LXC 104 and VM 105, and fresh
local archives for those two guests were verified on 2026-08-19. Both were added to the
Backup Synology's filtered pull and checksum-verified on 2026-08-20. Isolated
restores were then validated: Hermes booted with its dashboard and gateway
processes active, and Ollama reached its Debian login prompt with networking
disabled. LXC 104 has the higher restore priority because it contains the agent
configuration and provider setup, while VM 105 contains the tested Ollama
service and custom model profile. Because Hyper Backup selects the complete
`automated/proxmox-guests` tree, both mirrored archive sets are included in the
encrypted off-site backup without separate per-guest selection.

Named `aster-production-20260831` snapshots now protect the deployed LXC 104
and LXC 110 state locally. HomeLab Doctor confirmed a 16-hour-old LXC 110 archive
on 2026-08-31. Its Backup Synology mirror and isolated restore have not yet been
proven and remain backup-workflow follow-ups; a Proxmox snapshot is a rollback
point, not a substitute for those checks.

Do not commit Aster API keys, Hermes tokens, OAuth/provider state, Ollama chat
data or any model configuration containing credentials. Local backup coverage is confirmed;
the Backup Synology mirror and isolated restore validation are confirmed as of
2026-08-20, and the mirrored archives are covered by the encrypted off-site task.

## NUT / UPS Server (Lenovo)

The Lenovo utility host (`nut-server`, `192.168.50.25`) runs NUT on bare
metal, so its recoverable state is a handful of small config files rather
than a Proxmox guest archive. Pull a fresh copy after any change to NUT,
SSH or network configuration, from the Mac (not from an existing SSH
session into `nut-server` itself, so nothing lingers on the source host):

```sh
printf "Sudo password for jason@nut-server: "
read -rs NUT_SUDO_PASS
echo

STAMP_DIR=~/lab/private-backups/nut/$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p "$STAMP_DIR"

echo "$NUT_SUDO_PASS" | ssh nut "sudo -S cat /etc/nut/ups.conf" 2>/dev/null > "$STAMP_DIR/ups.conf"
echo "$NUT_SUDO_PASS" | ssh nut "sudo -S cat /etc/nut/nut.conf" 2>/dev/null > "$STAMP_DIR/nut.conf"
echo "$NUT_SUDO_PASS" | ssh nut "sudo -S cat /etc/nut/upsd.users" 2>/dev/null > "$STAMP_DIR/upsd.users"
echo "$NUT_SUDO_PASS" | ssh nut "sudo -S cat /etc/nut/upsmon.conf" 2>/dev/null > "$STAMP_DIR/upsmon.conf"
echo "$NUT_SUDO_PASS" | ssh nut "sudo -S cat /etc/ssh/sshd_config.d/hardening.conf" 2>/dev/null > "$STAMP_DIR/sshd-hardening.conf"
ssh nut "cat /etc/network/interfaces" > "$STAMP_DIR/network-interfaces.txt"
ssh nut "hostnamectl" > "$STAMP_DIR/hostnamectl.txt"

unset NUT_SUDO_PASS
chmod 600 "$STAMP_DIR"/*
```

This lands directly in `~/lab/private-backups/nut/<timestamp>/`, which is
already inside the existing daily Backup Synology pull (21:00) and the
encrypted IDrive e2 off-site task — no separate automation was needed.
HomeLab Doctor's `check_nut` reports live NUT/UPS health, and
`check_backup_age "NUT" ...` reports how stale this config backup is.

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
truenas-config-<timestamp>.db` (mode `600`), which lands in the existing
daily Backup Synology pull and encrypted IDrive e2 off-site task. The
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

**Recommended follow-up, not yet actioned:** add `Media/ix-apps` (or
specifically Jellyfin's named config volume within it) to a recurring
snapshot schedule and to the existing Backup Synology pull / encrypted
off-site pipeline, following the same pattern already used for Home
Assistant and the other applications in this document. This needs an
explicit decision on schedule and mechanism before implementation — not
made unilaterally as part of documenting current state.

## Prometheus / Grafana observability

LXC 109 is included automatically by the enabled all-guests Proxmox snapshot
job. Its first archive, created on 2026-08-30, passed a complete Zstandard
integrity test.

The smaller configuration-level recovery set is stored under
`~/lab/private-backups/observability/<date>/` and therefore enters the existing
Backup Synology pull and encrypted IDrive e2 pipeline. The Prometheus archive
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

The external disk remains the first local recovery tier. Retained guest archives are now mirrored to the Backup Synology and included in the client-side-encrypted IDrive e2 task described above.

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
| OPNsense | Doctor checks Internet, WAN state and service reachability; configuration drift is monitored | Automated configuration export, checksum and Backup Synology mirror | Configuration recovery is documented; a live firewall replacement restore remains intentionally untested because it would disrupt the network |
| Arista core switch | Doctor checks expected links, temperature, PSU state and interface-error baselines; configuration drift is monitored | Automated running-configuration and state export with verified mirror | Configuration replacement is documented; destructive production restore is intentionally deferred |
| Proxmox host | Doctor checks guests, storage, memory and swap; Beszel supplies history; TLS expiry and configuration drift are monitored | Host configuration export plus retained guest archives on local backup storage and the Backup Synology | Multiple isolated guest restores prove archive usability; complete bare-metal host recovery remains a documented manual procedure |
| Docker LXC 100 | Doctor checks SSH and hosted service endpoints; Beszel monitors the host and containers | Current LXC archive retained locally and checksum-mirrored to the Backup Synology | Homepage application recovery was tested independently; Proxmox LXC recovery was validated using an isolated disposable guest |
| UniFi LXC 101 | Doctor checks controller reachability | Current LXC archive plus UniFi application backups, mirrored off-host | Isolated LXC restoration and recovered UniFi database inspection succeeded |
| TrueNAS | Doctor checks pools, NFS, bond health and management access; certificate expiry is monitored | System configuration export (`config.save`, via CLI/API or the guided browser flow) is included in the protected infrastructure set; ZFS protects local media integrity | Configuration recovery is documented; media is intentionally excluded from encrypted off-site backup because of size and replaceability. Export is currently manual/one-off, not scheduled |
| Jellyfin (on TrueNAS) | No dedicated Doctor check yet | **Incomplete** — only three manual, one-off `Media/ix-apps` snapshots exist (two migration-project checkpoints plus one general checkpoint, 2026-09-01); no recurring snapshot schedule and no Backup Synology/off-site mirror for the application database (playlists, collections, users, watch state) | Not tested; see the "Jellyfin" section above for the 2026-09-01 incident that exposed this gap and the recommended follow-up |
| Pi-hole primary and secondary | Doctor performs public, local and blocked-domain DNS tests through both resolvers | Primary inherits Docker LXC protection; secondary inherits TrueNAS application/configuration protection; Teleporter exports are documented | Functional recovery validation is performed through the redundant resolver pair; either resolver can carry DNS while the other is rebuilt |
| Frigate VM 102 | Doctor checks VM/service state, NFS mount and recording freshness; Beszel tracks host metrics | Current VM archive and private checksum-verified Frigate configuration backup, mirrored off-host | VM-level recovery is available; recordings remain intentionally excluded because they are high-volume and nonessential to infrastructure recovery |
| Home Assistant VM 103 | Doctor checks Core and backup age | Encrypted native backups to local and Synology storage plus current mirrored VM archives | Isolated VM 903 restored and booted HAOS, Supervisor and Core successfully |
| Main Synology | Doctor checks DSM reachability; Hyper Backup reports task failures | Versioned Hyper Backup repository on the Backup Synology with encrypted off-site protection for essential recovery material | Repository browsing and recovery access were validated; a full destructive NAS restore is intentionally not performed |
| Backup Synology | Doctor checks DSM and the freshness/status of both automated pull jobs | Stores checksum-verified configuration and Proxmox mirrors; essential recovery material is independently protected in IDrive e2 | Recovery sets and restricted pull paths were validated; loss of the appliance requires rebuilding the pull tasks from documented configuration |
| Aster Agent LXC 104 | Doctor checks guest, service and API health | Current LXC archive retained locally and checksum-mirrored to the Backup Synology; named production snapshot retained locally | Earlier isolated restore as LXC 972 booted the retained Hermes rollback services; Aster boot persistence was validated in place |
| Legacy Ollama VM 105 | Doctor checks guest state according to its intended operating mode | Current VM archive retained locally and checksum-mirrored to the Backup Synology | Isolated restore as VM 973 reached its login prompt successfully |
| Aster llama.cpp LXC 110 | Doctor checks guest and inference-service health | Named production snapshot and current local archive retained; off-host mirror remains to be confirmed | Boot persistence was validated in place; isolated archive restore remains pending |
| Authentik LXC 106 | Doctor checks service reachability through the configured endpoint | Current LXC archive retained locally and checksum-mirrored to the Backup Synology | Platform-level recovery inherits the validated Proxmox LXC restore process; Authentik configuration is documented separately |
| Reverse Proxy LXC 107 | Doctor checks NPM service reachability and TLS dependencies | Current LXC archive retained locally and checksum-mirrored to the Backup Synology | Platform-level recovery inherits the validated Proxmox LXC restore process; proxy and Authentik recovery order is documented |
| Forgejo LXC 108 | Doctor checks service reachability; Beszel records host health | Current LXC archive retained locally and checksum-mirrored to the Backup Synology; GitHub remains a synchronized off-site Git remote | Isolated restore as LXC 978 verified the active Forgejo service, SQLite database and `jason/homelab.git`, then the test guest was removed |
| Observability LXC 109 | Prometheus self-monitors and all seven initial scrape jobs are health-checked; Doctor integration follows after Grafana stabilizes | Protected configuration archive plus the retained all-guests LXC snapshot; both enter the existing Synology/off-site pipeline | Configuration archive extracted and checked in isolation; first LXC archive passed complete Zstandard integrity testing |
| NUT server (Lenovo, bare metal) | Doctor checks `nut-server`/`nut-monitor` state, all three UPS units' `ups.status` and battery charge, and config-backup age | Manually-pulled config set (`ups.conf`, `nut.conf`, `upsd.users`, `upsmon.conf`, SSH hardening, network config) lands directly in the same Backup Synology pull and encrypted IDrive e2 off-site tree as other appliance configs | Live driver/server configuration validated via `upsc`; a full bare-metal OS reinstall has not been tested, only documented as a recovery procedure |
| Reolink camera | Doctor tests HTTP, RTSP and ONVIF reachability; Frigate proves recording flow | No recording archive is required; Frigate configuration preserves the integration settings | Camera replacement or reset is a documented reconfiguration task rather than a backup restore |

### Accepted recovery boundaries

- Full destructive restores of the production firewall, switch, TrueNAS and both
  Synology appliances are not justified solely to prove procedures that already
  have verified exports, documented recovery steps and representative restore
  evidence.
- Media libraries and Frigate recordings are intentionally excluded from
  encrypted off-site protection because their size exceeds their recovery value.
- Aster LXC 104 and legacy Ollama VM 105 have verified same-site/off-host archives,
  isolated restore tests and encrypted off-site protection through the selected
  `automated/proxmox-guests` tree.
- The Backup Synology is a recovery repository, not the only copy of essential
  configuration or guest data.
