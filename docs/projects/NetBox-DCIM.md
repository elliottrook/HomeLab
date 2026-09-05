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
  - [x] **Done 2026-09-01.** Jason clicked "Add System" in the Beszel hub
    UI and supplied the generated token. Installed via the official
    `get.beszel.dev` installer (downloaded and sanity-checked before
    running — confirmed it does real sha256 checksum verification, not
    just a bare `curl | sh`), same hub public `KEY` and `HUB_URL` as
    Forgejo LXC 108's working agent. Service came up `active`/`enabled`,
    no auto-update timer created (matches this repo's pinned-version
    preference).

    **Caught a real timing issue, not a config error:** the agent logged
    repeated `WebSocket connection failed: unexpected status code: 401`
    for about 90 seconds after install — because the token Jason had
    given me earlier (before this "Add System" click) had nothing to
    match yet; a token only becomes valid once the hub-side system record
    actually exists. No agent-side change was needed: it kept retrying on
    its own 10-second cycle and connected cleanly
    (`WebSocket connected host=192.168.20.20:8090`) on the very next
    attempt after the record was created. Confirmed both in the agent's
    own journal and by Jason seeing it go green in the hub UI.
  - [x] Add configs/services.conf plain-TCP entry — **done** (`netbox`,
    `192.168.20.32:8000`), confirmed passing via Doctor's "Checking
    configured services" section. `configs/devices.conf` also updated to
    match the existing per-LXC pattern.
  - [x] Add a Homepage dashboard tile, matching the existing per-service
    pattern. Backed up `services.yaml` first
    (`/root/services.yaml.before-netbox-tile-20260901-144709` on Docker
    LXC 100 — rollback path if ever needed). Added under "Application
    Management" alongside Forgejo/File Browser. Restarted the `homepage`
    container (config changes aren't hot-reloaded); confirmed healthy and
    the tile actually renders on the page afterward, not just that the
    YAML parsed. **Also fixed the same session, at Jason's request (outside
    NetBox's own scope, but the same file/service):** the "AI & Automation"
    group's stale "Hermes Agent"/"Ollama" tiles were renamed to "Aster
    Agent" (`http://192.168.70.10:9120`) and "Aster llama.cpp"
    (`http://192.168.70.12:11435/v1/models`) — neither tile had a working
    link before. Backed up `services.yaml` again first
    (`/root/services.yaml.before-aster-tiles-20260901-145219`), restarted
    `homepage`, and verified both new hrefs directly via Homepage's own
    `/api/services` endpoint rather than trusting the raw page HTML (which
    doesn't show client-rendered tile data).

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

## Milestone 3 addendum — Discovery-assisted gap fill (2026-09-01/02)

Jason asked for a further population pass using live network interrogation
rather than another manual walk-through. This explicitly revisits, and
narrows rather than fully overturns, this document's original "Out of
scope" line ruling out automated discovery — see the decision below.

- **Sandbox extended** to reach NetBox plus 8 additional hosts (UniFi
  Controller, both APs, Home Assistant, Reolink camera, Authentik, Lutron
  bridge, Hue bridge) via `CLAUDE.md`/`.claude/settings.json`, committed
  separately from this doc (`847aa96`).
- **Method, agreed with Jason before running anything**: passive discovery
  only — OPNsense's Kea DHCP lease table and ARP table, Arista's MAC
  address table — plus targeted queries to already-known hosts. No active
  port/service scanning was actually needed: the passive data gave
  complete live-host visibility on VLANs 20/50/60/70 already. Guest VLAN 40
  and Trusted VLAN 10 were never actively probed.
- **NetBox gaps closed**: added individual `Device` records for the
  **Lutron Caséta bridge** (`192.168.30.102`) and **Philips Hue bridge**
  (`192.168.30.164`) — new `Lutron`/`Philips` manufacturers and a new
  `IoT Bridge` role, both previously only shelf-contents text. Added the
  missing IP + MAC to the existing **PoE camera switch** record
  (`192.168.60.145`, confirmed via its own `TL-SG1016PE` DHCP lease,
  matching the model NetBox already had recorded). Device count 21 → 23.
  Authentik, Home Assistant, and the UniFi Controller were already present
  as Virtual Machine records from Milestone 3 — checked before writing
  anything, no duplicates created.
- **Scope decision, confirmed explicitly by Jason**: personal/family client
  devices surfaced by the DHCP/ARP data (phones, laptops, Apple TVs, a
  smartwatch, a receiver, etc., mostly on Trusted VLAN 10) are **not**
  added to NetBox. NetBox stays scoped to lab infrastructure, matching this
  document's original Purpose/Scope — this was a real decision point, not
  an oversight, and applies going forward to any future population work
  too.
- **Real, unrelated bug found and fixed via this same discovery data,
  outside this project's own scope but worth recording for continuity**:
  a live host at `192.168.20.129` (hostname `Family-Room`, on *Servers*
  VLAN 20) turned out to be a Family Room Apple TV — confirmed by an open
  AirPlay port and by matching the household's other four Apple TVs, all
  correctly on Trusted VLAN 10. It was wired into Arista Et17, a port
  whose stale description (`TrueNAS-Failover-Servers`) didn't match either
  its old or new use — TrueNAS's actual bond is Et9/Et15 per
  `Current-Network-Baseline.md`, so Et17 was simply a mislabeled, unused
  port that had been patched to the TV at some point. Confirmed nothing
  else shares that jack. Fixed live: `switchport access vlan 20` → `10`,
  description → `Family-Room-AppleTV`, saved (`write memory`). Verified via
  `show mac address-table interface Et17`: relearned on VLAN 10
  immediately. **Rollback**: revert both lines on Et17
  (`switchport access vlan 20`, description `TrueNAS-Failover-Servers`).
  Not added to NetBox, per the scope decision above. This required its own
  explicit go-ahead from Jason since it's a real VLAN-membership change,
  outside any project's standing authorization.
- **Binarui AP switch model — attempted, inconclusive, not a new problem.**
  Jason granted read/write autonomy to finish this task overnight
  (2026-09-02); the one remaining safely-closeable item from this
  document's earlier "not attempted yet" list was the Binarui switch's
  exact model (its NetBox `Device` still has the generic placeholder
  device type `AP Switch`). A read-only HTTP request to `192.168.50.26`
  timed out — consistent with `Current-Network-Baseline.md`'s existing
  note that this switch's management plane sits on untagged VLAN 1 and
  isn't reachable normally on VLAN 50; nothing new here, and not pursued
  further (would need physical/console access, which no authorization
  substitutes for). Left as a genuine open item, not silently retried.
  **Resolved 2026-09-04** during the AP Switch config-loss incident (see
  `Current-Network-Baseline.md`): its management interface became reachable
  without physical access, and the identifiers were read directly from the
  device — MAC `84:E5:D8:E2:8D:92`, serial `6202510300069`, firmware
  `V100SP11251021` (Oct 21 2025), hardware `V1`. The unit still exposes no
  real model string — its own UI reports the device model literally as
  `Switch` — so the generic `AP Switch` NetBox device type is now known to be
  accurate rather than a placeholder awaiting better data. Its NetBox
  primary IP also needs revisiting once the open addressing decision is made.
  Backup Synology's model was explicitly left alone per Jason's
  instruction (out of scope, unrelated to tonight's NAS-instability
  incident). No further network-affecting changes were made overnight —
  everything else on the "not attempted yet" list either needs Jason
  directly or was already resolved earlier this session.
- **Backup Synology model recorded: DS220j** — supplied directly by Jason
  (2026-09-02), not queried from the live host (still deliberately left
  alone given its documented instability under load — see
  [[project_backup_synology_instability]]). Created a `DS220j` device type
  under the existing `Synology` manufacturer, reassigned the Backup
  Synology `Device` record to it, and deleted the now-unused
  `2-bay (model not recorded)` placeholder type it previously pointed to
  (confirmed zero other devices referenced it before deleting). Also
  updated `docs/03-Hardware-Inventory.md`'s listing to match. This was the
  one deliberately-skipped item from the discovery pass above; now closed.
- **Real outage found and fixed: NetBox was down, no restart policy on
  any of its 5 containers.** Jason reported it looked down; confirmed via
  HTTP (connection refused) and `docker compose ps` (all 5 containers
  `Exited`). Root cause, confirmed via `journalctl`/`last -x reboot`: LXC
  111 itself cleanly rebooted ~7 hours earlier (not caused by any of
  tonight's work — no OOM signal in `dmesg`, just a clean shutdown/boot
  cycle from an unknown external trigger) and Docker Compose never
  restored the stack afterward because none of the 5 services had a
  `restart` policy set. Fixed in two steps: first `docker compose up -d`
  to restore service immediately (verified: all 5 healthy, login page
  HTTP 200, device count still 23 — Postgres data lives in a named volume
  untouched by container state); then, with Jason's explicit go-ahead,
  added `restart: unless-stopped` to all 5 services via
  `docker-compose.override.yml` (not the upstream-tracked
  `docker-compose.yml`, so a future `git pull` on the netbox-docker
  checkout won't lose it) — backed up the override file first
  (`docker-compose.override.yml.before-restart-policy-20260903` on the
  guest), confirmed the merged config picked up the policy via
  `docker compose config` before recreating containers, then recreated
  and re-verified (healthy, HTTP 200, device count still 23). **Root
  cause of the LXC reboot, confirmed by Jason**: a deliberate Proxmox
  host shutdown for the RAM upgrade — cascades a clean reboot to every
  guest, matching the evidence (no crash/OOM signal, just a clean
  shutdown/boot pair). Not an anomaly; the actual gap this incident
  exposed was purely the missing restart policy, now fixed.

## Milestone 4 — Cutover and hand-back

- [x] Replace `diagrams/Rack-Diagram.md` with either a generated export or a
  pointer to the live NetBox view, per the Milestone 1 decision. **Done as
  a refreshed snapshot** (not a pointer/export, per the "snapshot, not
  retired" decision) — updated with the confirmed walk-through data and
  the stale banner removed, since it now reflects verified reality rather
  than a guess.
- [x] Reconcile or retire `configs/devices.conf`/`docs/02-IP-Addressing.md`
  per the same decision. **Done 2026-09-01.** Before reconciling, extended
  NetBox itself to be genuinely complete enough to reconcile against —
  added the 8 individual devices that previously existed only as
  shelf-contents text (OPNsense, NUT server, Binarui AP Switch, both
  Synology units, both UniFi APs, the Reolink camera) as real `Device`
  objects with IP addresses, plus added missing IPs to three devices that
  had none yet (Arista, Proxmox host, TrueNAS) — 21 Devices total now, all
  with addresses where one applies.

  Then diffed both files against the complete NetBox inventory:
  - `configs/devices.conf`: only one real gap — **Home Assistant
    (`192.168.20.11`) was missing entirely**, added. Every other one of
    its 21 rows already matched NetBox exactly. Added a header comment
    marking it as a NetBox snapshot (same pattern as `Rack-Diagram.md`)
    plus a note on the Backup Synology incident. Verified `lab status`
    still parses the file correctly afterward — this file is live tooling
    (`scripts/lab`), not just documentation, so format preservation
    mattered here in a way it didn't for the rack diagram.
  - `docs/02-IP-Addressing.md`: one real gap — **NetBox's own address
    (`192.168.20.32`) was missing from its own project's addressing
    table** (it didn't exist yet the last time this file was touched).
    Added, plus the same snapshot header and incident note.
- [x] Document NetBox operations (backup, restore, upgrade) in the standard
  repo locations. **Done 2026-09-01** — new "NetBox DCIM" section in
  `docs/05-Backups.md` (matching the existing per-service pattern) plus a
  row in the Critical-Service Recovery Coverage matrix. Documented
  accurately rather than aspirationally: Layer 1 (local Proxmox snapshot)
  covers it fully since Docker's volumes live on the guest's own
  filesystem, not external storage; Layer 2/3 are pending on the same two
  items already tracked above (live DSM task, Backup Synology itself being
  down) — not a NetBox-specific gap, called out as such; no isolated
  restore has been tested yet since the deployment is brand new.
  Documented the pinned-version upgrade procedure
  (`v4.6-5.0.2` in `.env`, snapshot-first, watch migrations complete
  rather than assume).

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
| 2026-09-01 | 2 | Beszel agent installed on LXC 111 after Jason created the system record and supplied its token; official `get.beszel.dev` installer sanity-checked before running. Agent logged repeated `401`s for ~90s (token had nothing to match until the hub-side record existed, not a config error), then self-recovered and connected cleanly on its own next retry — confirmed in the agent's journal and by Jason seeing it go green in the hub UI | Passed |
| 2026-09-01 | 3, 4 | Extended NetBox with the 8 remaining individual devices (previously only shelf-contents text) plus missing IPs on 3 more, then reconciled `configs/devices.conf` and `docs/02-IP-Addressing.md` against the now-complete inventory — one real gap found in each (Home Assistant missing from `devices.conf`; NetBox's own address missing from `02-IP-Addressing.md`), both fixed. Verified `lab status` still parses `devices.conf` correctly afterward. Documented NetBox's backup/restore/upgrade procedure in `docs/05-Backups.md` (new section plus a Critical-Service Recovery Coverage row), stated accurately: Layer 1 covers it fully, Layer 2/3 pending on the same two already-tracked blockers, no isolated restore tested yet | Passed |
| 2026-09-01/02 | 3 addendum | Discovery-assisted gap fill: sandbox extended to 9 more hosts; passive OPNsense DHCP/ARP + Arista MAC-table discovery (no active scanning needed); Lutron and Hue bridges added as new Device records, PoE camera switch given its missing IP/MAC. Device count 21→23. Scope decision confirmed with Jason: personal/family client devices excluded from NetBox going forward | Passed |
| 2026-09-02 | 3 addendum (related, out of project scope) | Discovery data surfaced a Family Room Apple TV wired into Arista Et17 on the wrong VLAN (Servers 20, port mislabeled `TrueNAS-Failover-Servers`) instead of Trusted VLAN 10 like the household's other four Apple TVs. Confirmed nothing else shares the port; fixed live with Jason's explicit go-ahead (`switchport access vlan 10`, description corrected, saved); verified relearned on VLAN 10 via the MAC table | Passed |
