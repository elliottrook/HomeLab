# NetBox DCIM / Rack & Asset Management Project

> Status: Active
>
> Project owner: Jason
>
> Last updated: 2026-09-01

## Authorization

**Per-project authorization granted 2026-09-01** (see `CLAUDE.md`, "Per-project
authorization" section): Claude may execute this project's state-changing
steps — LXC creation, package installs, firewall rules for the new host —
without asking before each individual step. This does not waive, for any
action taken under it:

- a rollback route documented before the action, not after;
- the least invasive change that meets the step's objective, preserving the
  lab's existing security/privacy posture everywhere else;
- stopping and asking about anything genuinely unanticipated;
- or the physical rack walk-through, which no authorization can substitute
  for — that step still requires Jason directly.

Every state-changing step taken under this authorization is logged in the
Evidence log at the bottom of this document as it happens, matching this
repository's standard project-tracking convention.

## Purpose

Replace the hand-maintained rack diagram (`diagrams/Rack-Diagram.md`, now
stale after a partial physical rack rebuild) and the hand-maintained device
tables (`configs/devices.conf`, `docs/02-IP-Addressing.md`) with a
self-hosted [NetBox](https://netboxlabs.com/oss/netbox/) instance: real rack
elevation views generated from actual inventory data, plus IPAM that can
become the authoritative source for addressing instead of a manually synced
markdown table.

This directly addresses two repeat findings from the 2026-09-01 repository
audit: the rack diagram drifting out of sync with physical reality, and
`configs/devices.conf`/`docs/02-IP-Addressing.md` periodically missing
entries that exist elsewhere. A generated, data-backed view can't drift the
same way a hand-maintained one does.

## Scope

- Deploy NetBox as a new, isolated, unprivileged Proxmox LXC on Servers
  VLAN 20 (matching the placement pattern used for Observability/LXC 109).
- Model the physical rack (15U, current real contents — requires an on-site
  inventory pass, since the existing diagram can't be trusted as a starting
  point) as NetBox rack elevation data.
- Model core network devices, Proxmox guests, and the addressing already
  documented in `docs/02-IP-Addressing.md`/`configs/devices.conf` as NetBox
  DCIM/IPAM records.
- Decide and document NetBox's relationship to the existing markdown
  inventories: full replacement, or NetBox-as-source-of-truth with the
  markdown files becoming generated/exported summaries. Do not let two
  authoritative inventories exist at once.
- Add NetBox to the standard operational set: HomeLab Doctor health check,
  backup coverage, monitoring.

## Out of scope

- Full IT-asset-management features NetBox offers beyond DCIM/IPAM (circuits,
  power, tenancy, contracts) unless a specific need emerges later.
- Automatic discovery/scanning of the network to populate NetBox — initial
  population is a manual, verified data-entry pass against real hardware,
  not a trust-the-scanner import.
- Migrating Proxmox/OPNsense/Arista configuration to be *driven by* NetBox
  (e.g. NetBox-as-IPAM-source-of-truth feeding DHCP) — this project is
  documentation/visibility only, not a change to how addressing is actually
  assigned.

## Architecture decisions to make in Milestone 1

- Exact LXC placement: VMID (next available after 110) and address (likely
  the next `192.168.20.x` after Observability's `.31`, but confirm against
  OPNsense/DHCP reservations before creating it — do not assume).
- NetBox version and deployment method (official Docker Compose vs. a
  from-source install) — follow whichever the repo's existing pattern favors
  for similarly-scoped services (checksum-verified pinned releases, not
  `:latest`).
- Whether NetBox sits behind Authentik (native OIDC support exists) from day
  one or is LAN/Tailscale-only initially, consistent with the repo's staged
  SSO rollout pattern in `docs/09-Service-Authorization-Onboarding.md`.

## Milestone 1 — Physical inventory and design

- [ ] Walk the physical rack and record actual current contents, U-position
  by U-position — this is the step the old diagram skipped, and why it went
  stale silently. **Blocked on Jason** — no authorization can substitute for
  this step.
- [x] Confirm NetBox's resource requirements against current Proxmox
  capacity headroom. Live check 2026-09-01: host had only ~2.6 GB genuinely
  free (33.6 GB total, 21.8 GB used across existing guests; the "additional
  planned RAM" in `03-Hardware-Inventory.md` has not landed yet). Along the
  way, found Observability (LXC 109) was allocated 4096 MB but using only
  ~484 MB live — reduced its cap to 2048 MB (live `pct set`, no restart, all
  six of its services confirmed still active afterward; rollback is
  `pct set 109 -memory 4096`). Noted for the record: LXC memory settings are
  cgroup ceilings, not host reservations, so this didn't literally free host
  RAM — it was a hygiene fix (removes an unbounded-growth risk), not a
  capacity unlock. NetBox is sized the same way (2048 MB) on the reasoning
  that its real footprint should land in the same few-hundred-MB-to-~1GB
  range as Observability's comparable Python/Postgres-adjacent stack, well
  inside the host's actual ~2.6 GB live headroom.
- [x] Decide placement, version, and deployment method. VMID 111, hostname
  `netbox`, `192.168.20.32/24` (confirmed free 2026-09-01: no DHCP
  reservation, no active lease, no ARP entry, no ping response), Servers
  VLAN 20, Debian 13.6 (matching the template already used for LXC 109/110).
  Deployment method: Docker Compose via the official `netbox-community/netbox-docker`
  project, following the same pattern already established for Authentik
  (LXC 106) and the Reverse Proxy (LXC 107) — a dedicated single-purpose LXC
  running Compose, `nesting=1,keyctl=1` features enabled for Docker support,
  matching those two guests' config exactly. Chosen over a from-source
  install because NetBox's own documentation treats Docker Compose as the
  primary supported path, and building it from source would mean
  hand-maintaining Postgres/Redis/Gunicorn/nginx version compatibility
  ourselves for no real benefit at this scale.
- [ ] Decide the markdown-vs-NetBox source-of-truth question explicitly and
  record the decision here.

## Milestone 2 — Deployment

- [x] LXC 111 created and started 2026-09-01: 2 vCPU, 2048 MB RAM, 512 MB
  swap, 32 GB disk, unprivileged, `onboot=1`, `nameserver 192.168.20.20`,
  `searchdomain internal`, net0 on `vmbr0` tag 20 mirroring LXC 109's
  pattern. Verified: correct IP bound, DNS resolution works, `apt-get
  update` reached both `deb.debian.org` and `security.debian.org`
  successfully. (Gateway ICMP ping fails, but so does it for the existing
  healthy LXC 109 — confirmed as normal for this network, not a fault.)
  **Rollback:** `pct stop 111 && pct destroy 111` — safe at this stage,
  container holds no data yet.
- [ ] Install NetBox via Docker Compose, validate a private-only login.
- [ ] Add to HomeLab Doctor, backup coverage, and Beszel/monitoring following
  the existing per-service pattern.

## Milestone 3 — Data population

- [ ] Enter the verified physical rack inventory from Milestone 1.
- [ ] Enter core network devices, Proxmox guests, and addressing from the
  existing markdown inventories, cross-checking each entry against live
  reality rather than copying the markdown verbatim (some of those entries
  are exactly what this project exists to stop trusting blindly).
- [ ] Generate a rack elevation view and compare it against the Milestone 1
  physical walk-through for agreement.

## Milestone 4 — Cutover and hand-back

- [ ] Replace `diagrams/Rack-Diagram.md` with either a generated export or a
  pointer to the live NetBox view, per the Milestone 1 decision.
- [ ] Reconcile or retire `configs/devices.conf`/`docs/02-IP-Addressing.md`
  per the same decision.
- [ ] Document NetBox operations (backup, restore, upgrade) in the standard
  repo locations.

## Definition of done

The physical rack and core device/address inventory are represented in
NetBox, verified against physical reality rather than against the old
markdown files, and there is exactly one documented source of truth for each
— either NetBox or markdown, never both silently.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-01 | 1 | Live Proxmox capacity check: 33.6 GB total / 21.8 GB used / 2.6 GB free; Observability LXC 109 found using ~484 MB of its 4096 MB cap | Recorded above |
| 2026-09-01 | 1 | Observability LXC 109 memory cap reduced 4096→2048 MB via live `pct set`; all six services (`prometheus`, `grafana-server`, `pve-exporter`, `nut-exporter`, `graphite-exporter`, `truenas-graphite-ingress`) confirmed active afterward | Passed |
| 2026-09-01 | 1 | `192.168.20.32` confirmed free: no OPNsense DHCP static mapping or active lease, no ARP entry, no ping response | Passed |
| 2026-09-01 | 2 | LXC 111 created (Debian 13.6, 2 vCPU/2048 MB/512 MB swap/32 GB disk, unprivileged, `nesting=1,keyctl=1`), started, network/DNS/`apt-get update` all verified working | Passed |
