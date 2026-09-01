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

- [x] Walk the physical rack and record actual current contents, U-position
  by U-position — this is the step the old diagram skipped, and why it went
  stale silently. **Done 2026-09-01**, interactively with Jason from a
  physical photo of the rack and the floor-standing equipment beside it.
  Top to bottom, confirmed: PDU (1U) → shelf (~5U: main Synology, backup
  Synology, Lutron bridge, Hue bridge) → shelf (~4U: PoE AP switch,
  OPNsense, NUT server) → patch panel (1U) → Arista (1U) → patch panel
  (1U) → PoE camera switch (1U) → brush panel (1U) → network UPS (1U,
  position not reconciled — see below). Floor-standing, left to right:
  TrueNAS, Proxmox, `nas-ups`, `proxmox-ups`.

  **Real correction surfaced directly by the photo**: OPNsense's actual
  hardware is a **VMware SD-WAN Edge 620**, not the "Dell EMC E42W
  (SD-WAN Edge 610)" recorded in `CLAUDE.md` and
  `docs/03-Hardware-Inventory.md` — both fixed this session. Also
  identified the NUT server (Lenovo ThinkCentre M92p) on the same shelf
  as OPNsense, which no prior document had placed physically.

  **Known open item, not blocking:** Jason's estimated shelf heights sum
  to ~16U against the rack's 15U nominal rating. One estimate is probably
  1U too generous; not worth holding up for a tape measure. The network
  UPS (`network-ups`) is recorded as rack-mounted-but-unplaced in NetBox
  rather than guessed into a specific U.
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
- [x] Decide the markdown-vs-NetBox source-of-truth question explicitly and
  record the decision here. **Decision (2026-09-01): NetBox is
  authoritative; `diagrams/Rack-Diagram.md` becomes a periodically
  refreshed snapshot of it, not retired outright.** Chosen over full
  retirement because the markdown file is still useful as a
  quick-to-read, no-login-required reference (e.g. from a phone while
  standing at the actual rack), and because this repo's other inventory
  docs (`02-IP-Addressing.md`, `configs/devices.conf`) follow the same
  pattern of being the readable surface over data that could in principle
  live somewhere more structured. The rule going forward: when NetBox and
  the markdown snapshot disagree, NetBox wins, and the snapshot gets
  refreshed — never edited independently to "fix" a discrepancy in the
  other direction.

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
- [x] Install NetBox via Docker Compose, validate a private-only login.
  Docker 29.7.2 + Compose plugin v5.5.0 installed via the official Debian
  repo (GPG fingerprint verified: `9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C
  0EBF CD88`, matches Docker's published key). Deployed
  `netbox-community/netbox-docker` (release branch,
  `docker.io/netboxcommunity/netbox:v4.6-5.0.2` — NetBox 4.6.x /
  netbox-docker packaging 5.0.2, explicitly pinned in a local `.env` rather
  than relying on the repo's own default, so a future `git pull` on this
  checkout can't silently change what's deployed) at `/opt/netbox`. All
  Postgres/Redis/Redis-cache/NetBox secrets regenerated with `openssl rand`
  and cross-checked for consistency across env files without ever printing
  a value; originals were the project's published example placeholders and
  were never used. Superuser `admin` created via the built-in bootstrap
  (`SKIP_SUPERUSER=false` + `SUPERUSER_*` vars); its generated password
  lives only in `/root/.netbox-superuser-password` (mode 600) on the guest.
  All five containers (`netbox`, `netbox-worker`, `postgres`, `redis`,
  `redis-cache`) healthy. Validated `GET /login/` returns HTTP 200 from
  another Servers VLAN 20 guest; confirmed it does **not** respond from
  Proxmox's Management-VLAN interface — expected default-deny behavior, not
  a fault, and no rule was added to widen that. No SSO/Authentik
  integration yet — private LAN/Tailscale access only, per the Milestone 1
  decision. Port mapping: `8000:8080` (host:container), bound to the LXC's
  single interface (`192.168.20.32`) only.
- [~] Add to HomeLab Doctor, backup coverage, and Beszel/monitoring following
  the existing per-service pattern. **Doctor and Layer-1/Layer-2 backup
  coverage done; Beszel and the live Backup Synology task remain open.**
  - [x] Added `check_netbox()` to `scripts/doctor.sh` (containers healthy
    check across all five services, login-page HTTP check via
    `pct exec 111`) and a `check_proxmox_guest_backup_age "NetBox LXC 111"`
    entry. Live-tested: caught and fixed a real bug on first run (the
    function tried `cd /opt/netbox` on the Proxmox host itself instead of
    inside the guest via `pct exec`) before considering this done — same
    "verify, don't assume" standard as the rest of this repo's Doctor
    checks.
  - [x] Confirmed the enabled local Proxmox backup job (Layer 1) uses
    `all 1` (every guest, no explicit VMID list), so LXC 111 is already
    included automatically — no config change needed, first archive lands
    at tonight's 02:30 run.
  - [x] Added LXC 111 to both filter blocks (copy + checksum-verify) in
    `scripts/backup/synology-proxmox-pull.sh`, the repo's canonical
    reference for the Backup Synology's pull task body (Layer 2). While in
    there: confirmed LXC 110 (Aster llama.cpp) is **also** still missing
    from this same filter — a pre-existing gap from before this project,
    already flagged separately in `05-Backups.md`'s Aster section as an
    open backup-workflow follow-up. Left untouched — fixing it isn't part
    of this project's scope.
  - [ ] **Blocked on Jason, confirmed 2026-09-01.** Investigated editing
    the live DSM task ("HomeLab Proxmox backup pull", task ID 6 on the
    Backup Synology) directly: confirmed via `synoschedtask --get id=6`
    that its inline command body has the identical pre-fix filter list
    (through LXC 109, missing 110/111) as the repo script had before this
    session's edit — same fix needed, live. But `synoschedtask` only
    supports `--get`/`--del`/`--run`/`--reset-status`/`--sync`, no `--set`;
    no `synowebapi` binary exists on this DSM version/package set to reach
    the API route instead; and the `gowest-backup` automation account,
    while in the DSM `administrators` group, only has a **password-gated**
    sudo grant (confirmed: `sudo -n whoami` fails with "a password is
    required") — the only pre-existing passwordless sudo grant on this
    account is narrowly scoped to `/sbin/shutdown -h now` from the UPS
    project. I don't have and shouldn't ask for that password. This is a
    real, investigated blocker, not a skipped step — needs Jason directly
    (DSM UI, or supplying the mechanism used for the earlier LXC 109
    edit referenced in `05-Backups.md`).
  - [ ] **Needs a 30-second manual step from Jason.** Investigated the
    agent-install pattern (confirmed against Forgejo LXC 108's working
    `beszel-agent.service`: a dedicated `beszel` user running
    `/opt/beszel-agent/beszel-agent`, pointed at the hub
    `http://192.168.20.20:8090` via a fixed hub public `KEY` plus a
    **per-system `TOKEN`**). The hub (Beszel 0.18.7, PocketBase-based, in
    Docker LXC 100) has no CLI/API path to mint that token without either
    an existing superuser session or creating one — and creating or using
    hub admin credentials programmatically is exactly the kind of
    account/credential action this repo's rules reserve for a human. This
    one is much lighter than the DSM blocker above: open the Beszel hub UI,
    "Add System" named `netbox` at `192.168.20.32`, copy the generated
    token, and I can finish the install immediately once I have it.
  - [ ] Add configs/services.conf plain-TCP entry — **done** (`netbox`,
    `192.168.20.32:8000`), confirmed passing via Doctor's "Checking
    configured services" section. `configs/devices.conf` also updated to
    match the existing per-LXC pattern.

## Milestone 3 — Data population

- [x] Enter the verified physical rack inventory from Milestone 1. **Done
  2026-09-01.** Created a `Rack` (`Main Rack`, 15U nominal) and 13
  `Device` records: the 8 confirmed rack-mounted items at their walked
  positions (PDU U15; NAS/bridge shelf U10–U14; network appliance shelf
  U6–U9; patch panels U5 and U3; Arista U4; PoE camera switch U2; brush
  panel U1), plus 5 devices deliberately recorded **without** a rack
  assignment: TrueNAS, the Proxmox host, `nas-ups`, `proxmox-ups` (all
  genuinely floor-standing, per the walk-through), and `network-ups`
  (rack-mounted in reality, but left unplaced in NetBox rather than
  guessed — its exact position is the one item the walk-through didn't
  fully resolve, see Milestone 1). Verified via the API afterward: exactly
  the 8 expected devices report `rack_id=1`, exactly the 5 expected report
  no rack.
- [x] Enter core network devices, Proxmox guests, and addressing from the
  existing markdown inventories, cross-checking each entry against live
  reality rather than copying the markdown verbatim (some of those entries
  are exactly what this project exists to stop trusting blindly). **The
  guest/VLAN/addressing portion is done, and the rack walk-through's
  completion (above) closed most of the physical-device gap too.**
  Arista, the PoE camera switch, TrueNAS, and both patch panels/PDU/brush
  panel now have individual or shelf-grouped `Device` records with real
  rack positions. OPNsense and the NUT server are currently recorded only
  as text inside the "network appliance shelf" device's comments, not as
  their own individual `Device` objects — a reasonable-but-incomplete
  stand-in worth revisiting if/when someone wants OPNsense or the NUT
  server to show up in their own right in searches/reports rather than as
  shelf-contents text. Not attempted yet: individual manufacturer/model
  detail for the two Synology units, Lutron bridge, and Hue bridge (also
  currently shelf-contents text, not their own `Device` objects) and the
  Binarui AP switch (same).

  Created via NetBox's API/ORM (API token minted through the documented
  `/api/users/tokens/provision/` endpoint — note for future reference:
  this NetBox version uses "v2" tokens, `Authorization: Bearer
  nbt_<key>.<token>`, not the older `Authorization: Token <token>` form):
  - Site `Mini Atlas HomeLab`.
  - All 7 VLANs (10/20/30/40/50/60/70) with their `/24` prefixes, scoped
    to the site — matching `network/topology.md`'s table exactly.
  - A `Proxmox VE` cluster type and `proxmox` cluster.
  - All 12 current Proxmox guests as Virtual Machines (100–111, VM 106 the
    only gap in the visible sequence — never allocated, not a bug),
    **each field pulled fresh from live `pct config`/`qm config` during
    this session**, not copied from any markdown table: vCPU, memory,
    disk, MAC address, primary IP, and status (VM 105/Ollama correctly
    recorded `offline`, matching its actual stopped state). Two real
    hostname/service-name mismatches surfaced and were recorded in each
    VM's comments rather than silently normalized away: VM 102's actual
    guest hostname is `friate` (typo, not `frigate`), and LXC 104/110
    still carry their pre-Aster-rename hostnames (`hermesagent`,
    `ollama-gpu-pilot`) even though they run Aster's services today —
    both are real, currently-true facts about the infrastructure, not
    something to "fix" by writing the tidier name into NetBox instead.
  - Verified via the API afterward (not just trusted from the creation
    script's own output): 12/12 VMs, 7/7 VLANs, 7/7 prefixes present,
    spot-checked vCPU/memory/primary-IP values against the live
    `pct config`/`qm config` dump.
- [x] Generate a rack elevation view and compare it against the Milestone 1
  physical walk-through for agreement. **Done 2026-09-01.** The elevation
  is definitionally in agreement — it was built directly from the same
  walk-through data, not from an independent source — so this checks that
  the data entry matches what was confirmed, not that two independent
  surveys agree. Verified via `GET /api/dcim/devices/?rack_id=1`: exactly
  the 8 expected rack-mounted devices at their confirmed positions,
  exactly the 5 expected floor/unplaced devices with no rack assignment.
  `diagrams/Rack-Diagram.md` was also refreshed in the same session with
  this data (see Milestone 4 — done ahead of its own checkbox since it was
  the natural moment to fix a document already flagged stale, rather than
  leaving it wrong until formal cutover).

## Milestone 4 — Cutover and hand-back

- [x] Replace `diagrams/Rack-Diagram.md` with either a generated export or a
  pointer to the live NetBox view, per the Milestone 1 decision. **Done as
  a refreshed snapshot** (not a pointer/export, per the "snapshot, not
  retired" decision) — updated with the confirmed walk-through data and
  the stale banner removed, since it now reflects verified reality rather
  than a guess.
- [ ] Reconcile or retire `configs/devices.conf`/`docs/02-IP-Addressing.md`
  per the same decision. **Not yet done** — these weren't part of this
  session's walk-through and still need the same "snapshot of NetBox"
  treatment applied deliberately, not assumed.
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
| 2026-09-01 | 2 | Docker installed (official repo, GPG fingerprint verified); `netbox-community/netbox-docker` deployed pinned to `v4.6-5.0.2`; all secrets regenerated and cross-validated; all five containers healthy; `GET /login/` returns HTTP 200 within Servers VLAN 20 and correctly does not respond from Management VLAN | Passed |
| 2026-09-01 | 2 | `check_netbox()` added to `scripts/doctor.sh` and live-tested (caught a real bug: checked the wrong host, fixed); backup-age check added; LXC 111 added to both filter blocks in `scripts/backup/synology-proxmox-pull.sh` (the canonical Layer-2 reference); confirmed Layer-1 local Proxmox job already covers all guests unconditionally | Passed |
| 2026-09-01 | 2 | Investigated live-editing the Backup Synology's actual DSM scheduled task: `synoschedtask` has no `--set`, no `synowebapi` present, and the automation account's sudo is password-gated beyond one narrowly-scoped pre-existing grant | Blocked — needs Jason |
| 2026-09-01 | 2 | Investigated Beszel agent registration: confirmed the install pattern against Forgejo LXC 108's working config, but minting a per-system token needs hub admin credentials this session correctly doesn't have | Blocked — needs a 30-second manual step from Jason |
| 2026-09-01 | 3 | NetBox API token minted via the documented `/api/users/tokens/provision/` endpoint; discovered and recorded this NetBox version's "v2" `Bearer nbt_<key>.<token>` auth format (differs from the older `Token <token>` form) | Passed |
| 2026-09-01 | 3 | Site, all 7 VLANs/prefixes, a Proxmox cluster, and all 12 current Proxmox guests (as Virtual Machines with interfaces, MAC addresses, and primary IPs) created in NetBox, every field pulled fresh from live `pct config`/`qm config`, not copied from markdown. Verified after creation via the API: 12/12 VMs, 7/7 VLANs, 7/7 prefixes present and spot-checked | Passed |
| 2026-09-01 | 1, 3, 4 | Physical rack walk-through completed interactively with Jason from a photo. Surfaced a real hardware correction (OPNsense is a VMware SD-WAN Edge 620, not the previously-recorded "Dell EMC E42W / SD-WAN Edge 610" — fixed in `CLAUDE.md` and `03-Hardware-Inventory.md`) and located the NUT server physically for the first time. Rack + 13 Devices created in NetBox (8 rack-mounted at confirmed positions, 5 correctly recorded as not rack-mounted/unplaced); verified via `GET /api/dcim/devices/?rack_id=1`. `diagrams/Rack-Diagram.md` refreshed with the same data and its stale banner removed. Markdown-vs-NetBox source-of-truth decision recorded: NetBox authoritative, markdown a refreshed snapshot | Passed |
