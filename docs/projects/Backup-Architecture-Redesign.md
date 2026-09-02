# Backup Architecture Redesign

> Status: Active
>
> Project owner: Jason
>
> Last updated: 2026-09-02

## Authorization

**Per-project authorization granted 2026-09-02** (see `CLAUDE.md`,
"Per-project authorization" section): Claude may execute this project's
state-changing steps — TrueNAS dataset/rsync/snapshot configuration, the
new Proxmox LXC and its `rclone` setup, credential generation — without
asking before each individual step. This does not waive, for any action
taken under it:

- a rollback route documented before the action, not after;
- the least invasive change that meets the step's objective, preserving
  the lab's existing security/privacy posture everywhere else;
- stopping and asking about anything genuinely unanticipated;
- and, specific to this project, the **Milestone 4 dual-restore gate**:
  no existing Hyper Backup job may be retired until a real file has been
  recovered from both the TrueNAS ZFS snapshot and the IDrive e2 off-site
  copy. This gate is not something the authorization can waive — it is
  itself a condition of the authorization, not a step it lets Claude skip.

Every state-changing step taken under this authorization is logged in the
Evidence log at the bottom of this document as it happens, matching this
repository's standard project-tracking convention.

## Purpose

Replace the current Hyper Backup-centric, Synology-to-Synology backup
architecture with one that separates three concerns Hyper Backup currently
bundles into one product on underpowered hardware: **transport** (moving
bytes), **local version history** (recovering from an accidental
delete/corruption), and **off-site protection** (surviving loss of the
whole site). Each concern moves to the component actually suited for it:

```
Synology (gowest)  --lightweight rsync-->  TrueNAS
  production data                          local backup dataset
                                            + ZFS snapshot retention
                                                    |
                                                    | rclone (read-only
                                                    | source access)
                                                    v
                                            Dedicated Proxmox LXC
                                                    |
                                                    | rclone + crypt
                                                    v
                                            IDrive e2 (encrypted,
                                            versioned off-site)
```

## Why this exists

Both Synology units have been observed becoming unstable specifically when
Hyper Backup runs — and especially when both are active participants
simultaneously (one running a Hyper Backup task, the other as its target).
Diagnosis this session ruled out several simpler explanations before
landing here:

- Not a network/MTU issue — path MTU confirmed clean (1500 end-to-end).
- Not raw disk I/O — a local `dd` write test on `gowest` hit 30.5 MB/s,
  perfectly healthy.
- Not resource-leak/uptime-related — a full reboot of `gowest` did not
  change the failure pattern at all.
- Confirmed destination-specific and load-specific: identical payloads
  transfer cleanly to other Servers VLAN 20 hosts; only sustained
  high-processing loads against the Synology units (Hyper Backup's
  versioning/dedup/compression engine, not plain file copies) trigger
  instability.

Working hypothesis: both Synology units are underpowered for Hyper
Backup's processing overhead, and the problem compounds when both run it
concurrently. A secondary, untested-but-plausible contributing factor:
both Synology units share the same UPS (`proxmox-ups`, see
`docs/03-Hardware-Inventory.md`) — worth keeping in mind, though not a
blocker for this redesign, since the new architecture's target (TrueNAS)
sits on a separate UPS (`nas-ups`) regardless of which explanation turns
out to be primary.

Separately, this is also the right moment for this change: Plex's media
library was removed from `gowest` as part of the completed
[Plex-to-Jellyfin media migration](completed%20projects/Plex-to-Jellyfin-Media-Migration.md),
freeing real capacity there, and the Backup Synology's role in the backup
architecture is being retired outright rather than repaired — its
low-power hardware turned out to be poorly suited to what Hyper Backup
demanded of it, and Jason intends to repurpose it for something that
actually fits its power envelope. That repurposing is **explicitly out of
scope for this project** — a separate decision for later.

## Authoritative baseline

- [x] Current three-layer architecture is documented in `docs/05-Backups.md`
  (Local Proxmox vzdump / Backup Synology same-site pull / Backup Synology
  → IDrive e2 off-site via Hyper Backup).
- [x] Backup Synology is currently offline (active incident, same document)
  and is being removed from the backup architecture permanently, not
  restored to its old role.
- [x] `gowest` (main Synology, `192.168.20.41`) becomes an rsync **source**
  only — production data, not a backup destination.
- [x] TrueNAS (`192.168.20.40`, Servers VLAN 20) is on a separate UPS
  (`nas-ups`) from both Synology units (`proxmox-ups`).
- [ ] TrueNAS's exact current free capacity and CPU/RAM headroom —
  **needs a fresh live check in Milestone 1**. The `Media` pool showed
  15.6 TiB free on 2026-08-30, but the Plex-to-Jellyfin migration wrote a
  substantial amount of data into that same pool since then; do not trust
  the old figure.
- [ ] IDrive e2 bucket versioning/retention support — **not yet confirmed**.
  The existing bucket (Oregon-2, `s3.us-west-4.idrivee2.com`) is used by
  the current Hyper Backup task; whether its configuration already
  supports the version retention this design requires, or whether a new
  bucket/configuration is needed, is a Milestone 1 discovery item.
- [ ] Exact scope of what each existing Hyper Backup job protects —
  **not yet inventoried precisely**. In particular, `Synology Drive
  Backup` protects `SynologyDrive` package/application configuration
  (Team Folder, sharing, quota, retention settings) in addition to plain
  files under `homes`/`Family Documents` — a raw filesystem rsync will
  not automatically capture that unless the relevant `@appdata` paths are
  deliberately included. This must be nailed down before any existing job
  is retired, not assumed equivalent.

## Architecture decisions

- **`gowest` is a source, never a destination.** No backup data lands on
  either Synology going forward.
- **Local replication is plain rsync over SSH, not Hyper Backup.** This
  matches what was already proven stable on this hardware for months
  before Hyper Backup was introduced into the same path — it is a
  reversion to a known-good pattern, not a new risk.
- **Local version history is TrueNAS ZFS snapshots, not Hyper Backup's own
  versioning/dedup engine.** Snapshot-based retention has near-zero
  marginal CPU cost (copy-on-write) versus Hyper Backup's catalogue and
  deduplication overhead — the resource profile this redesign exists to
  avoid.
- **Off-site transport is a dedicated, minimal Proxmox LXC running
  `rclone`, not Hyper Backup and not either Synology.** All CPU-heavy work
  (encryption, network transfer, integrity checking) moves to hardware
  with real headroom, following the same isolated-single-purpose-LXC
  pattern already used for Observability and NetBox.
- **The off-site LXC reads from TrueNAS's backup dataset read-only.** It
  needs to read the backup to send it off-site; it does not need
  permission to alter TrueNAS's copy. Its IDrive e2 credentials are a
  fresh, narrowly-scoped key limited to the backup bucket — not a reuse of
  the existing Hyper Backup task's key. Same least-privilege pattern this
  repo already applies everywhere else (the original `homelab-backup`
  restricted account, NetBox's dedicated API token, etc.).
- **Off-site encryption via `rclone crypt`, not blanket compression.**
  Family documents/photos/media are dominated by already-compressed
  formats (JPEG/HEIC, video, PDFs); recompressing them costs CPU for
  little benefit. Compression is a per-dataset decision if a specific
  source turns out to be compressible, not a default.
- **Off-site must have its own version/deletion retention, not just a
  mirror.** A bare `rclone sync` faithfully propagates
  corruption/accidental deletion from TrueNAS to IDrive e2. This design
  requires either IDrive e2's own object versioning (if the bucket
  supports it) or an `rclone` configuration that preserves
  replaced/deleted objects rather than destroying them — confirmed in
  Milestone 1/2, not assumed.
- **No existing Hyper Backup job is retired until a real restore has been
  proven from both layers of its replacement** — an older or deliberately
  deleted file recovered from a TrueNAS ZFS snapshot, *and* the same
  recovered from the IDrive e2 off-site copy. This is a hard gate, not a
  nice-to-have.
- **Dedicated restricted account for the TrueNAS→gowest rsync pull**, not
  Jason's personal SSH key — matching the least-privilege automation
  pattern already established for the original Backup Synology's
  `homelab-backup` account, rather than reusing an interactive admin
  credential for unattended automation.

## Scope

- Inventory the exact protected scope of all three current Hyper Backup
  jobs (`Mini Atlas Offsite`, `Synology Drive Backup`, `Media Backup`).
- Design and create the TrueNAS backup dataset(s) and ZFS snapshot
  retention schedule.
- Configure a native TrueNAS rsync task pulling from `gowest` over SSH,
  using a dedicated restricted account (not Jason's personal key).
- Deploy a new, minimal, unprivileged Proxmox LXC running `rclone` with a
  `crypt` remote, read-only access to the TrueNAS backup dataset, and a
  freshly generated, narrowly-scoped IDrive e2 credential.
- Validate version retention at both layers (TrueNAS snapshots and IDrive
  e2) with a real recovered-file test before touching any existing job.
- Add the new components to HomeLab Doctor, backup-age monitoring, and
  failure alerting, matching existing per-service patterns.
- Retire the three existing Hyper Backup jobs one at a time, only after
  their replacement coverage is proven equivalent.
- Update `docs/05-Backups.md` to describe the new architecture as current.

## Out of scope

- Deciding or implementing the Backup Synology's repurposed role — a
  separate decision for Jason, tracked outside this project.
- Migrating `Media Backup` (Plex-era task) contents beyond confirming
  whether it's still needed post-migration — the Plex-to-Jellyfin project
  already retired Plex source media; this project does not re-open that
  decision, only accounts for whatever backup coverage, if any, is still
  required for what remains.
- Any change to how the second Synology (if it still holds unique
  production data unrelated to backups) serves its own files — this
  project only concerns backup transport, not production file serving.
- Broader monitoring/alerting architecture changes beyond adding the new
  components to the existing HomeLab Doctor / failure-alert patterns.

## Milestone 1 — Inventory and discovery

- [ ] Record the exact source paths, application-config paths, and
  destination scope of all three current Hyper Backup jobs.
- [ ] Live-check TrueNAS's current pool free capacity, CPU, and RAM
  headroom — do not reuse the 2026-08-30 figures.
- [ ] Confirm the IDrive e2 bucket's current versioning/retention
  configuration; decide whether it already meets this design's
  requirement or whether a new bucket/configuration is needed.
- [ ] Decide the TrueNAS dataset layout and naming for the backup landing
  zone.
- [ ] Confirm the next available Proxmox VMID and a free Servers VLAN 20
  address for the new off-site relay LXC, the same way every other guest
  in this repo has been placed — verified live, not assumed.

### Gate

Do not create any TrueNAS dataset, LXC, or credential until the exact
scope of what's being replaced is confirmed in writing here.

## Milestone 2 — TrueNAS local replication and snapshot retention

- [ ] Create the TrueNAS backup dataset(s) decided in Milestone 1.
- [ ] Create a dedicated, restricted SSH account/key for the rsync pull
  from `gowest` (least-privilege, source-address-scoped where DSM
  supports it — not Jason's personal key).
- [ ] Configure the native TrueNAS rsync task (SSH-based, pull) against
  that account.
- [ ] Configure a ZFS periodic snapshot task with an explicit retention
  schedule (proposed starting point: daily snapshots retained 14 days,
  weekly retained 8 weeks, monthly retained 6 months — confirm or adjust
  before finalizing).
- [ ] Run the task, confirm data lands correctly and matches source
  (count/checksum comparison, not just "it ran without error").
- [ ] Confirm snapshots are actually being created and retained per
  schedule.

### Gate

A full rsync pull has completed, been verified against the source, and at
least one ZFS snapshot has been confirmed present before proceeding.

## Milestone 3 — Off-site relay LXC

- [ ] Create the new Proxmox LXC: unprivileged, minimal resource
  allocation sized to actual need (not copied from a larger guest by
  default — check real footprint the way Observability and NetBox were
  sized this session).
- [ ] Install `rclone` via its official, checksum-verified release —
  matching this repo's pinned-release convention, not `:latest`/rolling.
- [ ] Configure the IDrive e2 remote with a freshly generated,
  narrowly-scoped access key limited to the backup bucket — never a reuse
  of the existing Hyper Backup task's credential.
- [ ] Configure an `rclone crypt` remote layered on top, with a freshly
  generated encryption password/salt, stored only on the guest
  (root-only, mode 600) and in the standard protected recovery location —
  never printed to chat or committed to Git.
- [ ] Grant the LXC read-only access to the TrueNAS backup dataset (NFS
  export scoped read-only, or equivalent) — it must not be able to alter
  TrueNAS's copy.
- [ ] Schedule the `rclone` sync/copy job with logging and a bandwidth
  limit if warranted.

### Gate

A real sync to IDrive e2 has completed and been spot-checked for integrity
before proceeding to the validation milestone.

## Milestone 4 — Validation (hard gate before any cutover)

- [ ] Deliberately modify or delete a test file in the TrueNAS backup
  dataset's source path, confirm it can be recovered from a ZFS snapshot.
- [ ] Confirm the same file's *older* version (not just current state) can
  be recovered from the IDrive e2 off-site copy specifically — proving
  version retention exists off-site, not just a mirror.
- [ ] Add HomeLab Doctor checks for the new rsync task's freshness, the
  snapshot schedule's health, and the `rclone` job's success/failure,
  matching the existing `check_backup_age`/`check_reported_backup`
  pattern.
- [ ] Confirm failure-only alerting is wired for the new components,
  matching the existing pattern (no email on success, actionable email on
  failure).

### Gate

Both the local (ZFS) and off-site (IDrive e2) restore tests must pass
before any existing Hyper Backup job is touched. This is the single most
important gate in this project — do not skip it under schedule pressure.

## Milestone 5 — Cutover and documentation

- [ ] Retire the three existing Hyper Backup jobs one at a time — not all
  at once — confirming after each that its replacement coverage is
  genuinely equivalent (per Milestone 1's inventory) before moving to the
  next.
- [ ] Update `docs/05-Backups.md` to describe the new architecture as
  current, retiring the old three-layer description appropriately.
- [ ] Add the new LXC to `configs/devices.conf`/`configs/services.conf`
  and, if the NetBox DCIM project's inventory is still being maintained,
  to NetBox as well.
- [ ] Record the Backup Synology's backup-role retirement as complete;
  explicitly flag its repurposing as a separate, not-yet-decided
  follow-up for Jason.
- [ ] Update this project's status to `Complete` only after every prior
  gate has passed and documentation is current.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| A Hyper Backup job protects application state a raw rsync won't capture | Milestone 1's explicit per-job inventory before any retirement; `Synology Drive Backup`'s `SynologyDrive` app-config path specifically called out |
| Off-site copy faithfully mirrors corruption/deletion from the source | Milestone 4's hard gate requires proving version retention off-site, not just local, before any cutover |
| New rsync/rclone automation reuses an interactive admin credential instead of a scoped one | Dedicated restricted accounts required by design for both the TrueNAS pull and the IDrive e2 relay |
| TrueNAS capacity assumed from stale figures | Milestone 1 requires a live capacity check, not reuse of the 2026-08-30 reading |
| New off-site LXC given more access to TrueNAS than it needs | Read-only access by design; it can read the backup dataset, not alter it |
| Cutover happens before replacement coverage is actually proven | Milestone 5's jobs are retired one at a time, only after Milestone 4's dual-restore gate passes for each |

## Definition of done

The redesign is complete when: production Synology data reaches TrueNAS
via lightweight rsync with no observed instability; TrueNAS ZFS snapshots
provide local version history; a dedicated, read-only-scoped LXC relays an
encrypted, versioned copy to IDrive e2; a real file has been recovered
from both the local snapshot and the off-site copy; monitoring and
failure alerting cover every new component; all three legacy Hyper Backup
jobs are retired; and `docs/05-Backups.md` reflects the new architecture
as current.

## Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-09-02 | 0 (design) | Diagnosed Backup Synology + gowest instability under Hyper Backup load this session (network/disk/reboot ruled out as causes); synthesized a three-way design discussion (Claude + a second AI's proposal, refined with Jason) into this project | Recorded above |
| 2026-09-02 | 0 (authorization) | Per-project authorization granted by Jason, with the Milestone 4 dual-restore gate explicitly preserved as a condition of the grant, not something it waives | Recorded above |
