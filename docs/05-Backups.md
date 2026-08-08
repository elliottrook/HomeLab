# Backups

Back up OPNsense, Proxmox, UniFi, Arista, TrueNAS and Synology configurations.

## Handling rules

- Keep exported configurations in encrypted or access-controlled storage.
- Do not commit passwords, password hashes, API keys, Tailscale authentication keys, private SSH keys or raw appliance exports to Git.
- Sanitized examples and documented procedures may be committed to this repository.
- Verify that each archive is readable before relying on it, and record the application version used to create it.
- Copy staged archives off the source host so a single host failure cannot destroy both the service and its backup.

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

Confirm `http://home.internal:3000`, the management tiles and the four SSH launch links. A Homepage restart is not a substitute for a configuration backup.

## Pi-hole

Create a Pi-hole Teleporter export from **Settings > Teleporter**. Store it with the date and Pi-hole version. Teleporter is preferred to copying the live persistent directory because `gravity.db` and `pihole-FTL.db` can change while the container is running. After a restore, validate public resolution, local split DNS and blocking:

```sh
dig +short @192.168.1.20 example.com
dig +short @192.168.1.20 home.internal
dig +short @192.168.1.20 doubleclick.net
```

Expected results are public addresses, `192.168.1.20`, and a blocking response such as `0.0.0.0`, respectively. OPNsense remains the DHCP-advertised resolver, so the current Mac Mini pilot can be rolled back without a network-wide outage.

## Tailscale

Record the following without storing authentication keys or reusable tokens:

- `homelab-gateway` machine identity and Tailscale version
- Advertised route: `192.168.1.0/24`
- Approved route state in the admin console
- Split-DNS route for `internal` through `192.168.1.1`
- Identity-specific access grant for the trusted LAN
- Explicit exclusion of IoT `192.168.30.0/24` and Guest `192.168.40.0/24`

Keep a private export or controlled copy of the tailnet policy. After recovery, test Homepage and one SSH target from a device using cellular data with Wi-Fi disabled. Do not create a WAN port-forward as a recovery shortcut.

An operational-state snapshot can be staged from LXC 100 with `tailscale version`, `tailscale status` and `tailscale debug prefs`, redirected to a mode-600 file. This snapshot identifies tailnet devices and the account, so transfer it to protected storage, verify its checksum, and remove the temporary LXC copy. It supplements rather than replaces the private control-plane policy copy.

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

The external disk is still in the same physical system. A future backup phase should replicate the latest guest archives to protected NAS or genuinely off-host storage.

## Recovery order

1. Restore OPNsense routing, firewall, DHCP and DNS.
2. Restore the Arista and UniFi Layer 2 path.
3. Restore Proxmox and LXC 100 networking.
4. Restore Homepage, Pi-hole and the Tailscale subnet router.
5. Validate local access before testing remote Tailscale access.
6. Validate each backup after major configuration changes and before deleting the previous known-good copy.
