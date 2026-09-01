# NetBox DCIM / Rack & Asset Management Project

> Status: Proposed
>
> Project owner: Jason
>
> Last updated: 2026-09-01

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
  stale silently.
- [ ] Confirm NetBox's resource requirements against current Proxmox
  capacity headroom (see `docs/03-Hardware-Inventory.md`).
- [ ] Decide placement, version, and deployment method (see above).
- [ ] Decide the markdown-vs-NetBox source-of-truth question explicitly and
  record the decision here.

## Milestone 2 — Deployment

- [ ] Deploy the LXC, install NetBox, validate a private-only login.
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
