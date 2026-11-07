# Aster Games deployment packet

Status: Stream A server deployment completed and recovery-graduated on
2026-11-07. The post-infrastructure hold is active. Stop on the project's
non-waivable conditions, material drift, or scope expansion.

This packet turns the repository candidate into server infrastructure only. It
does not open the AsterTV v3 gate, expose the broker to an appliance, enable
RomM device installs, or create Kodi/AsterTV source.

## Read-only facts captured 2026-11-06

- Proxmox 9.2.20 has about 52.4 GiB available RAM and 551 GiB available on
  `local-lvm`; VMID 129 is unused.
- TrueNAS 25.10.5 has about 13.9 TiB available but only 2.6 GiB available RAM,
  so the stateful application stack belongs in a new Proxmox LXC rather than on
  the already constrained NAS Docker host.
- Prowlarr 2.6.5.5623 and SABnzbd 5.1.3 are healthy on TrueNAS at
  `192.168.20.40`, ports 9696 and 8080, and share `/mnt/Media/data`.
- `192.168.20.38` is absent from NetBox and did not answer two ICMP probes. This
  is candidate evidence only; allocation must recheck NetBox, ICMP, and the
  neighbor table immediately before mutation.

## Bounded change 1 — storage and NFS boundary

Target: TrueNAS `Media` pool.

Intended change:

- create `Media/Games`, mounted at `/mnt/Media/Games`, with LZ4 compression,
  atime off, exec off, and a 2 TiB quota;
- create `/mnt/Media/data/usenet/complete/retro-games` as the dedicated SABnzbd
  completed category path;
- export only those two roots to Proxmox `192.168.50.10`, read/write,
  root/all-squashed to UID/GID 568;
- add a daily 30-snapshot policy to `Media/Games`;
- take no recursive permission action and touch no existing media.

Expected effect: zero service interruption; two empty paths become available to
the later LXC. Validation checks dataset properties, exact exports, write/remove
with one synthetic file as UID/GID 568, and unchanged existing exports.

Rollback: remove the empty test file, NFS shares, snapshot task, empty staging
directory, and empty dataset. Stop if either path unexpectedly contains data.

## Bounded change 2 — inactive LXC

Target: Proxmox, candidate VMID 129, VLAN 20 candidate address
`192.168.20.38/24`.

Immediately recheck VMID, NetBox, ICMP, neighbor state, template, capacity, and
NFS exports. Then create an unprivileged Debian 13 LXC with 4 cores, 6 GiB RAM,
1 GiB swap, a 96 GiB `local-lvm` root disk, `nesting=1,keyctl=1`, VLAN tag 20,
gateway `192.168.20.1`, DNS `192.168.20.20`, and boot disabled until the base
configuration is reviewed. Let Proxmox generate the MAC, then record it rather
than predicting it.

Mount TrueNAS NFS roots on the Proxmox host using `hard`, NFSv4.2,
`nosuid,nodev,noexec`, then bind them into the LXC:

- library -> `/srv/aster-games/library`;
- staging -> `/media/usenet/complete/retro-games`.

Expected effect: a stopped, isolated guest exists; no current service changes.
Validation checks unprivileged status, exact config, mount flags, ownership, and
that no unexpected listener exists.

Rollback: stop and destroy only VMID 129 and its new root disk, remove only its
two host mount units/directories, and retain the storage from change 1 until its
separate rollback decision.

## Bounded change 3 — base runtime and inactive stack

Target: LXC 129 only.

Install Docker Engine/Compose from the reviewed Debian-compatible source,
create service UID/GID 568, `/opt/aster-games`, `/srv/aster-games/{state,dats}`,
and `/etc/aster-games/secrets`, and copy the hash-verified repository candidate.
Create unique secrets source-locally; never print or commit them. Create scoped
RomM client tokens only after RomM's first authenticated setup.

Render Compose with UI and broker bind addresses still `127.0.0.1`. Start the
database/cache first, then RomM, ROMarr, and broker. Do not add Prowlarr/SABnzbd
credentials yet.

Expected effect: loopback-only services start inside one new guest; existing
ARR and AsterTV services are untouched. Validation runs container health,
static validator, unit tests, listener inspection, reboot recovery, and
content-silent Doctor output.

Rollback: stop Compose, restore/destroy only the new guest from its pre-service
checkpoint, and leave storage empty.

## Bounded change 4 — private human administration

Target: NPM, Authentik, private DNS/firewall, and LXC 129.

Bind RomM 8080 and ROMarr 6868 only to `192.168.20.38`; keep broker 8099 on
loopback. Create private split-DNS/NPM routes for `games.elliottrook.com` and
`romarr.elliottrook.com`, restrict backend ingress to NPM, require Authentik,
retain each application's own authentication, and add no public DNS or Internet
route.

Expected effect: authorized administrators can reach two HTTPS UIs; other
clients cannot reach direct backend ports. Validation checks TLS, unauthenticated
redirect, Authentik login, app login, direct-port denials from representative
VLANs, and unchanged unrelated routes.

Rollback: remove only the two new proxy/auth/DNS/firewall objects and return UI
binds to loopback.

## Bounded change 5 — ARR integration and synthetic proof

Target: Prowlarr, SABnzbd, ROMarr, and RomM.

Create dedicated scoped credentials and the SABnzbd category `retro-games`
whose completed path is `/media/usenet/complete/retro-games`. Configure ROMarr
through its authenticated settings with those private endpoints, a scoped RomM
token, `/roms`, and `/srv/aster-games/dats`. Start with scheduled acquisition
disabled and use one redistributable synthetic/public-domain fixture.

Expected effect: only that fixture crosses search/download, staging, DAT
classification, import, and RomM scan. It must not affect existing ARR
categories or libraries.

Rollback: disable ROMarr schedules, revoke the three new credentials, remove
the dedicated SABnzbd category, quarantine/remove only the fixture, and restore
the empty library snapshot.

## Bounded change 6 — operations and recovery

Target: NetBox, Proxmox backup, Doctor, Beszel, wiki, and derived Aster mirror.

Register the exact LXC/MAC/IP/services, add the guest to protected backup,
register content-silent health/capacity/backup checks, perform the isolated
restore contract, and publish sanitized operating documentation. The mirror
receives no titles, paths below approved roots, credentials, or account data.

Expected effect: the server platform becomes observable and recoverable.
Rollback removes only new monitoring/inventory presentation objects; backup
copies remain until retention expiry unless separately approved for deletion.

## Post-infrastructure hold

These changes passed on 2026-11-07. Stop. Do not enable broker remote ingress,
device installs, AsterTV tokens, or Kodi/fleet work. Resume AsterTV work only
after the separate v3 deployment and owner-acceptance evidence opens the
project gate.

