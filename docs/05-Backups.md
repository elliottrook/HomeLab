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

Proxmox guest archives are pulled daily at 03:30, after the 02:30 Proxmox backup job, into `Backup/HomeLab-Backups/automated/proxmox-guests`. Proxmox account `homelab-backup` has a locked password and no administrative group membership. Its authorized key is source-restricted to the Backup Synology and forced through read-only `rrsync` rooted at `/mnt/backups/dump`. The mirror includes only LXC 100, LXC 101, QEMU 102 and QEMU 103 backup archives. Newly deployed Hermes LXC 104 and Ollama VM 105 are not yet confirmed in this filtered mirror. A checksum-mode dry run must be empty before success is recorded in:

- `proxmox-pull-latest.status`
- `proxmox-pull-last-success.txt`
- `logs/proxmox-pull-latest.log`

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

## Hermes Agent and Ollama Lab pilot

Hermes LXC 104 and Ollama VM 105 are experimental Lab VLAN 70 workloads. Verify
that the enabled all-guests Proxmox job includes both guests. LXC 104 is the
higher recovery priority because it contains agent configuration and provider
setup; add its archive to the Backup Synology mirror and encrypted off-site
selection before relying on it. VM 105 may be treated as reproducible only after
its Ubuntu/Ollama installation, service override and custom model definition are
fully documented and tested from a clean restore.

Do not commit Hermes tokens, OAuth/provider state, Ollama chat data or any model
configuration containing credentials. The backup status of both guests remains
an explicit open item as of 2026-08-19.

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
