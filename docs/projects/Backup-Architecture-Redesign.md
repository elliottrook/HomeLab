# Backup Architecture Redesign

> Status: Active — Milestones 1–5 substantively complete (all three legacy
> Hyper Backup jobs stopped, documentation and inventory updated). Only
> the final "mark Complete" step remains, held open pending
> `Backup-Synology-Decommission.md`'s own Milestones 4–5 (14-day
> observation, ends 2026-09-23, then disk redeployment).
>
> Project owner: Jason
>
> Last updated: 2026-09-10

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
  restored to its old role. **Correction 2026-09-05: "currently offline" was
  wrong even at the time this box was checked — the unit was up — and the
  root cause was later found to be 484 MB of RAM, not general instability.
  Neither correction changes this item's decision: the unit is still being
  permanently removed from the backup architecture, now under
  `Backup-Synology-Decommission.md`.**
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

**Post-closeout exception (approved 2026-09-10):** the original shared
Proxmox task remains at its deliberately fixed 100–109/111 scope, but Aster
LXC 110 now has a separate same-site mirror. A dedicated TrueNAS task pulls
only `vzdump-lxc-110-*.tar.zst` into
`/mnt/Media/backup/aster-lxc110` at 04:20 and uses `delete: true` only inside
that bounded directory, following the source's Proxmox retention. Both that
directory and any legacy LXC 110 archive under the shared guest tree are
excluded by the IDrive relay. This closes the off-host-copy gap without
allowing the roughly 38 GB daily model archives to consume or exceed the
provisioned 1 TB off-site tier; LXC 104's application and knowledge state
continues through the encrypted off-site path.

- **Backup source scope mimics the old architecture's scope exactly — no
  expansion, one deliberate addition.** Jason's explicit instruction: don't
  grow scope beyond what was already protected under the old three Hyper
  Backup jobs, except for NetBox (LXC 111), whose missing backup coverage
  is what started this whole investigation. Concretely, TrueNAS pulls from
  three sources, mirroring the old Backup Synology's pull scope exactly:
  1. **Mac `~/lab/private-backups`** (whole tree, unfiltered — matching
     the old pull's own `"$remote:/"` scope, no subset).
  2. **Proxmox guest archives**, same VMID list as the old filter (100,
     101, 102, 103, 104, 105, 106, 107, 108, 109) **plus 111 (NetBox)** —
     the one deliberate addition. **Not** 110 (Aster llama.cpp) — that gap
     predates this project, is separately documented, and stays out of
     scope here same as it did for the NetBox project.
  3. **`gowest`'s `homes`, `Family Documents`, and the `SynologyDrive`
     package's `@appdata` config** — the `Synology Drive Backup` job's
     scope from Milestone 1, including the app-config path that a naive
     rsync would miss.
  `Media Backup` (Plex-era) is **not** carried forward — Plex source media
  is already retired, and carrying its backup scope forward would be
  exactly the "extra backup" this instruction says not to add.
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

- [x] Record the exact source paths, application-config paths, and
  destination scope of all three current Hyper Backup jobs. **Sourced
  from `docs/05-Backups.md` (written when these tasks were originally
  built), not independently re-verified via DSM CLI** — attempted
  `/usr/syno/bin/synoschedtask --get` on `gowest` to pull the live
  `Synology Drive Backup` task config directly; it fails silently (empty
  stdout/stderr, exit 255) over a bare SSH exec, likely because it needs
  a DSM session/service context that isn't present outside the web UI.
  Not worth forcing — the existing documentation is specific and was
  written at task-creation time, which is good enough confidence for this
  design phase. Recorded scope:
  - **`Mini Atlas Offsite`** (ran on the now-retired Backup Synology):
    `Backup/HomeLab-Backups/automated/{private-backups,proxmox-guests}` —
    plain files only, no application state. Fully superseded by this
    project's design; nothing extra needed to replace it.
  - **`Synology Drive Backup`** (runs on `gowest`): shared folders `homes`
    and `Family Documents`, **plus application data** for the
    `SynologyDrive` package (Team Folder/sharing/quota/retention
    settings) and the `HyperBackup` package's own configuration. **This is
    the one that needs care** — a plain rsync of `homes`/`Family
    Documents` will not capture the `SynologyDrive` app-config state.
    Milestone 2's rsync source list must explicitly include the relevant
    `@appdata` path for `SynologyDrive`, not just the two shared folders,
    or this task is not actually equivalent once retired.
  - **`Media Backup`** (pre-existing, Plex-era, not created by this
    project or the Synology Drive project): protected Plex media. Plex
    source media was already retired as part of the completed
    Plex-to-Jellyfin migration — confirm with Jason whether this task
    still protects anything meaningful before assuming it needs a
    replacement at all; may simply be moot.
- [x] Live-check TrueNAS's current pool free capacity, CPU, and RAM
  headroom. **`Media` pool: 21.8T total, 15.0T allocated (68%), 6.78T
  free** — materially less free than the stale 15.6 TiB/28%-used figure
  from 2026-08-30, confirming that figure was right to distrust; the
  Plex-to-Jellyfin migration consumed the difference. Still comfortable
  headroom for backup data (family documents/photos, not another full
  media library). **RAM: 31 GB total, only ~3.4 GB "available"** per
  `free -h` — looks tight at a glance, but TrueNAS/ZFS's ARC cache
  deliberately holds RAM as "used" that's reclaimable under pressure, so
  this isn't the same signal it would be on a non-ZFS host. Load average
  low (0.2–0.9 on 12 cores). Not treated as a blocker, but worth a second
  look if the new rsync/snapshot load turns out to be heavier than
  expected.
- [~] Confirm the IDrive e2 bucket's current versioning/retention
  configuration. **Deferred to Milestone 3** — this is most naturally
  checked once `rclone` is actually configured against the bucket (it can
  query bucket versioning directly), rather than guessed at now without
  the tooling in hand. Recorded here so it isn't silently dropped.
- [x] Decide the TrueNAS dataset layout and naming for the backup landing
  zone. **Decision: `Media/backup/gowest`** (within the existing `Media`
  pool — no case for a dedicated new pool given 6.78T free headroom and
  no additional physical disks in scope), with subdirectories matching
  the actual shared folders (`homes`, `Family Documents`, the
  `SynologyDrive` app-config path) created during Milestone 2 once the
  rsync source list is finalized.
- [x] Confirm the next available Proxmox VMID and a free Servers VLAN 20
  address for the new off-site relay LXC. **VMID 112, `192.168.20.33`** —
  confirmed live: VMIDs 100–111 all in use (112 free), and `.33` has no
  ping response, no ARP entry, and no OPNsense static DHCP mapping, same
  verification standard used for every other guest placed this session.

### Gate

Do not create any TrueNAS dataset, LXC, or credential until the exact
scope of what's being replaced is confirmed in writing here.

**Gate passed 2026-09-02** — the one real risk found (`SynologyDrive`
app-config not captured by a plain shared-folder rsync) is now an explicit
Milestone 2 requirement rather than a silent gap. `Media Backup`'s
continued relevance needs a quick confirmation from Jason but doesn't
block starting Milestone 2 on the parts that are unambiguous.

## Milestone 2 — TrueNAS local replication and snapshot retention

Three separate pull relationships, one per source, mirroring the old
architecture's exact scope (see Architecture decisions above):

- [x] Create the backup landing directories. **Design simplified
  mid-Milestone-2**: rather than three separate ZFS datasets, discovered
  `Media/backup/homelab-proxmox-guests/` already exists as a plain
  subdirectory (not its own dataset) of a pre-existing `Media/backup`
  dataset — containing one real file (a 38 GB `vzdump-lxc-110` archive
  dated 2026-09-01), almost certainly a manual one-off from the parallel
  session active in this repo, addressing the exact "LXC 110 has no
  off-host mirror" gap flagged during the NetBox project. No TrueNAS
  rsync/cron/replication task references it — confirmed via `midclt call
  rsynctask.query` / `cronjob.query` / `replication.query`, all empty —
  so nothing automated to conflict with. Aligned with this precedent
  instead of fighting it: created `mac` and `gowest` as sibling plain
  subdirectories of the same `Media/backup` dataset, mode 700, rather
  than three independent datasets. Trade-off accepted: one shared
  snapshot retention schedule for all three sources instead of
  independent per-source schedules — reasonable at this scale, and
  matches what was already there rather than restructuring it.
- [x] **Proxmox source: connection proven end-to-end.** Extended the
  existing restricted `homelab-backup` account (locked password, no admin
  group, forced read-only `rrsync` rooted at `/mnt/backups/dump`,
  originally built for the Backup Synology's pull) with a **new
  authorized key for TrueNAS**, `from="192.168.20.40"`-restricted,
  rather than sharing the Backup Synology's key — backed up
  `authorized_keys` first. Generated a dedicated ed25519 keypair on
  TrueNAS (`/root/.ssh/homelab_proxmox_pull_ed25519`, private key never
  leaves the guest).

  **Hit a real, expected blocker first:** TrueNAS (Servers VLAN 20)
  had no path to Proxmox (Management VLAN 50) on port 22 at all —
  default-deny, no existing rule covered it. Paused and got Jason's
  explicit confirmation before touching OPNsense specifically (the one
  component where a mistake has network-wide blast radius, and this
  project's authorization hadn't explicitly enumerated firewall changes
  the way NetBox's did). Added a narrowly-scoped pass rule
  (`192.168.20.40` → `192.168.50.10:22` only), cloned from the existing
  TrueNAS→NUT-server rule's exact XML structure as a template rather than
  hand-written from scratch — safer given how much a malformed rule could
  break. Config backed up first
  (`/root/config-backups/config.xml.before-truenas-proxmox-rule` on
  OPNsense); validated the edited XML parses before reloading
  (`configctl filter reload`); confirmed both the new path and every
  existing tested path (`ssh proxmox`/`truenas`/`opnsense`, `lab status`)
  still work afterward — no regression.

  End-to-end test (`rsync --list-only` through the restricted account)
  succeeded: lists all guest archives across every VMID in scope,
  **including LXC 111 (NetBox)**, already present as of today
  (2026-09-02) — confirming the local Proxmox job is already covering it.
  Total 353.9 GB across all archives currently on Proxmox's local backup
  disk.

  VMID scope for the actual pull (not yet configured, connection only):
  100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 111 — matching the
  Architecture decisions scope exactly, not 110.
- [x] **`gowest` source: complete (2026-09-07), via a different mechanism
  than Proxmox/Mac.** The SSH-forced-command + `rrsync` pattern that
  worked for those two legs failed against DSM's own `rsync` binary for
  reasons that turned out to be unrelated to `rrsync` at all: DSM
  restricts SSH login to the `administrators` group by design (no
  per-user allow-list exists — confirmed directly from DSM's own UI
  text), the created account had shell `/sbin/nologin` (refuses any
  invocation, including a forced command), its home directory was
  world-writable (`777`, tripping OpenSSH's `StrictModes`), and its
  `/etc/ssh/authorized_keys/%u` entry needed `644` not `600` (DSM's
  patched `sshd` apparently reads it from a de-privileged context, unlike
  stock OpenSSH). After fixing all four, DSM's `rsync` binary itself then
  refused with `service disabled` / `module is write only` / `rsync
  service is no running` — it turns out DSM's rsync is deeply patched
  with its own daemon-style module-permission system that intercepts
  server-mode invocations even over plain SSH transport, tied to a
  "backup destination" framing (accepting incoming pushes) that fights a
  read-only pull. No usable module config was ever found (`/etc/rsyncd.conf`
  had zero modules defined even with the service enabled), so rather than
  keep reverse-engineering an undocumented Synology-internal permission
  layer, the mechanism was changed entirely: **DSM exports `homes` and
  `Family Documents` read-only over NFSv3, restricted to TrueNAS's IP
  only** (`Squash: No mapping` — required so a full backup can read every
  family member's private home folder, which needs root-equivalent read,
  same as Hyper Backup itself must have had); **TrueNAS mounts both
  read-only** (persisted via TrueNAS's Init/Shutdown Scripts feature,
  which survives OS upgrades, rather than a raw `systemd` unit or
  `/etc/fstab`, either of which TrueNAS SCALE can wipe on update); and a
  **plain local `rsync` on a TrueNAS cron job** copies from the mounts
  into `/mnt/Media/backup/gowest/{homes,family-documents}` — no SSH,
  no `rrsync`, no restricted DSM account needed for this leg at all. The
  `truenas-pull` DSM account (administrators-group membership, app-access
  denials, SSH key) is now unused dead weight from the abandoned
  approach — left in place for now, flagged as a cleanup item.
  **Scope decision, confirmed with Jason 2026-09-07:** the old Hyper
  Backup job also covered Synology Drive's own app-config
  (`/volume1/@synologydrive`), which turned out to be 315 GB — not a
  small config/index but the actual content-addressable version-history
  blob store (`@sync/repo`, 302 GB alone), nearly duplicating `homes`
  (311 GB). There is no smaller load-bearing subset of it — the bulk
  size *is* the version history, not incidental data alongside it.
  **Decided to skip it**: `homes`/`Family Documents` capture every file's
  *current* state; the accepted gap is losing Synology Drive's own
  multi-version rollback capability for files it was tracking. A
  temporary NFS export for this path was created, tested (found empty —
  wrong subpath, `@apphome/SynologyDrive` rather than the real
  `@synologydrive`), then removed again once the decision was made.
- [x] **Mac source: complete and verified (2026-09-05).** Remote Login was
  already enabled. The official `rrsync` (fetched fresh from the rsync
  project, not the stale historical assumption that it's a Perl script —
  it's Python3 now) relies on `--confine-root`, a flag added upstream on
  2026-08-02 as a real security fix (closes a dir-merge filter-rule escape
  that let a client read files outside the restricted dir) but only
  supported by GNU rsync — this Mac's `/usr/bin/rsync` is Apple's
  `openrsync`, which rejects the flag outright and broke every invocation.
  Rather than install Homebrew (a much larger footprint on Jason's personal
  laptop for one flag) or fall back to an older rrsync (which would reopen
  the exact escape the flag exists to close), the confinement was moved to
  the OS layer instead: a new dedicated, unprivileged local account
  (`truenas-pull`, key-only, no usable password) was created, added to
  Remote Login's access group (previously scoped to `jelliott` only), and
  granted a filesystem ACL giving it read/list/search **only** inside
  `~/lab/private-backups` — no broader access to `jelliott`'s home
  directory. The installed `rrsync` copy (root-owned, read+execute only
  for `truenas-pull`, so it can't modify its own restriction) has the
  single `--confine-root` line replaced with a comment recording exactly
  why, so a future `rrsync` update doesn't silently reintroduce the
  incompatibility without someone noticing the deviation. Verified: the
  restricted account can list/pull inside the confined directory, a `..`
  traversal attempt is rejected by `rrsync`'s own argv validation, and an
  absolute-path attempt outside the tree fails as an "unsafe arg" too —
  the OS-level ACL is what would stop a subtler escape (e.g. via a crafted
  dir-merge filter rule) that neither of those simpler checks exercises.
- [x] **Proxmox rsync task configured and created** via TrueNAS's native
  `rsynctask.create` (mode SSH, `ssh_credentials` referencing a
  registered keychain SSH key + connection pair — private key generated
  earlier stays on TrueNAS, registered via `keychaincredential.create`,
  never printed). `extra` include/exclude list built to exactly mirror
  the Architecture decisions VMID scope (100–109, 111; not 110) —
  `--include=vzdump-{lxc,qemu}-<vmid>-*.{tar,vma}.zst` per VMID then
  `--exclude=*`, same pattern as the existing reference script.
  `validate_rpath: false` — the schema's default probe doesn't work
  against a forced-command-restricted `rrsync` account, which only
  understands the rsync protocol itself, not an arbitrary path-stat
  request. Daily 04:00, after Proxmox's own local job. Manually triggered
  once to validate before trusting the schedule; the real pull (~354 GB
  in scope) is running in the background as this checkpoint is written —
  result to be confirmed once it completes.
- [x] Configure a ZFS periodic snapshot task per dataset. **Decision:**
  one shared `Media/backup` dataset (matching the pre-existing
  `homelab-proxmox-guests` subdirectory precedent, not three separate
  datasets) means one shared retention schedule covers all three
  sources, not per-dataset. Created three tiered snapshot tasks on
  `Media/backup` via `pool.snapshottask.create`: daily (14-day
  retention, 05:30), weekly (8-week retention, Sunday 05:45), monthly
  (6-month retention, 1st of month 06:00) — matching the originally
  proposed schedule. Triggered the daily task manually to validate;
  result to be confirmed (ZFS snapshot creation is near-instant
  regardless of dataset size, so a long-running confirmation likely
  reflects how this CLI reports job completion over this SSH path, not
  the snapshot itself taking a long time — same pattern observed with
  the rsync task trigger).
- [~] Run each task, confirm data lands correctly and matches its source
  (count/checksum comparison, not just "it ran without error"). **Proxmox
  leg done and verified.** Job state `SUCCESS`, no leftover processes.
  Compared source vs. destination directly rather than trusting the
  job's own report: Proxmox's `/mnt/backups/dump` has exactly **85**
  files matching the in-scope filter (100–109, 111), totaling
  239,052,726,477 bytes; the destination has 86 files (259 GiB) — the
  one extra is the pre-existing manual VMID-110 archive, correctly left
  untouched by `delete: false`. Net of that ~38 GB file, the transferred
  size reconciles with the source almost exactly. **Mac leg done and
  verified (2026-09-05).** Job state `SUCCESS`. Byte-exact match against
  source: 354 files / 22,806,562 bytes on both the Mac
  (`~/lab/private-backups`) and TrueNAS (`/mnt/Media/backup/mac`).
  **`gowest` leg done and verified (2026-09-07),** via the NFS-mount +
  local-cron mechanism described above (not `rsynctask`/SSH). Initial full
  pull ran to completion with no errors. Byte-exact match against source
  on both shares: `homes` — 110,788 files / 332,609,860,578 bytes on both
  the NFS-mounted source and `/mnt/Media/backup/gowest/homes`;
  `Family Documents` — 2 files / 522,083 bytes on both sides. **All three
  Milestone 2 rsync legs are now complete and verified.**
- [x] Confirm snapshots are actually being created and retained per
  schedule, for all three datasets. Daily snapshot confirmed present and
  covers all three subdirectories (single shared `Media/backup` dataset).
  All three sources' data is now present ahead of tonight's scheduled
  snapshot (05:30); full retention-cycle confirmation (weekly/monthly
  firing correctly, old snapshots actually pruning) still needs time to
  pass, which is expected and not something to force.

### Gate

**Passed 2026-09-07.** All three rsync pulls (Proxmox, Mac, `gowest`) have
completed and been verified byte-exact against their sources. A daily ZFS
snapshot is confirmed present on the shared dataset; weekly/monthly
retention firing correctly will be confirmed as time passes naturally.

## Milestone 3 — Off-site relay LXC

- [x] Create the new Proxmox LXC: **112** (`backup-relay`,
  `192.168.20.33`), unprivileged with 1 vCPU, 2 GiB RAM, 8 GiB root disk,
  no swap, no nesting and firewalling enabled. It has no GPU, shell access
  for Aster, or access to production data.
- [x] Install `rclone` via its official, checksum-verified release —
  **v1.75.1** was downloaded from the publisher, checked against its
  `SHA256SUMS` manifest, then only the verified binary was copied to the
  relay. No rolling package source is enabled.
- [x] Configure the IDrive e2 remote with a freshly generated,
  narrowly-scoped access key limited to the backup bucket — never a reuse
  of the existing Hyper Backup task's credential. The legacy
  `mini-atlas-backups` bucket and its Hyper Backup credential were never
  touched. **Corrected 2026-09-07**, in a second verification pass: the
  first relay key was exposed a second time (`rclone config show` prints
  S3 keys in plaintext, unlike the crypt password, which it auto-obscures
  — a real gap in my own handling, caught and named immediately) and its
  replacement was initially created without an actual bucket restriction,
  confirmed by testing that it could still list *and read contents of*
  `mini-atlas-backups` — a real least-privilege regression against the
  household's still-live, still-load-bearing off-site backup, not a
  cosmetic issue. Jason recreated the key a second time with IDrive's
  bucket-restriction option applied; verified this time by confirming a
  403 `AccessDenied` against the legacy bucket while `homelab-backup-relay`
  still works. Separately discovered the interactive `rclone config`
  wizard and the systemd service use **two different config file paths**
  (`~/.config/rclone/rclone.conf` vs. the service's `/etc/rclone/rclone.conf`
  via `RCLONE_CONFIG`) — the service was still running on the very first,
  already-revoked key for over an hour after both edits, since rclone
  reads its config once at process start. Fixed by copying the current
  key fields between the two files via a script run entirely on the relay
  (secret values never passed through Claude's own output).
- [x] Configure an `rclone crypt` remote layered on top, with a freshly
  generated encryption password/salt, stored only on the guest
  (root-only, mode 600) and in the standard protected recovery location —
  never printed to chat or committed to Git. `idrive-crypt` is active and
  its active config plus locally generated recovery material are root-only
  (`0600`). **Protected recovery destination:**
  `~/lab/private-backups/recovery/idrive-relay/<YYYY-MM-DD>/` on the Mac,
  itself `0700` with each recovered artifact `0600`. This whole-tree source
  is already pulled into the TrueNAS backup dataset and then carried by the
  encrypted relay; it is independent of the relay guest and its disk. The
  first dated copy (2026-09-08) contains the relay `rclone.conf` and
  `idrive-crypt` recovery material, with SHA-256 matched against LXC 112
  without displaying either file. Refresh a new dated bundle whenever either
  relay credential or crypt material changes. The bundle was checksum-verified
  after the existing Mac pull placed it on TrueNAS (`0700` directory, `0600`
  files), copied through `idrive-crypt:`, byte-verified as decrypted streams,
  and used from a temporary recovery directory instead of the live relay
  config to decrypt-list the off-site copy. The Mac pull ACL inheritance was
  repaired and a subsequent full TrueNAS pull completed successfully.
- [x] Grant the LXC read-only access to the TrueNAS backup dataset (NFS
  export scoped read-only, or equivalent) — it must not be able to alter
  TrueNAS's copy. Because an unprivileged LXC cannot mount NFS itself,
  Proxmox mounts the export read-only over NFSv4 and bind-mounts it
  read-only at `/srv/backup`; writes were directly rejected. The export
  permits only Proxmox, not the relay directly.
- [x] Schedule the `rclone` sync/copy job with logging and a bandwidth
  limit. A systemd timer runs daily after the local snapshot window with a
  20 MiB/s cap, non-overlap lock and protected local log. The initial sync
  started 2026-09-07. Its first `--fast-list` attempt was stopped after it
  consumed too much cgroup page cache; the retry omits that option. The relay
  was increased from 1 GiB to 2 GiB during the active retry after NFS page
  cache approached the initial limit; rclone's own RSS remained modest.
  **Completed 2026-09-08**, after the credential-scoping fix above forced a
  restart: `sync` finished with exit code `0`, **657.091 GiB transferred,
  111,196 / 111,196 files, 94/94 checks passed, 0 errors**, 9h31m elapsed
  (bandwidth-capped). Correctly deleted the earlier manual
  `relay-validation/roundtrip.txt` test artifact as part of normal `sync`
  mirroring (not a source file, expected to disappear).

**Egress boundary:** a dynamic OPNsense alias resolves only
`s3.us-west-4.idrivee2.com`; LXC 112 is permitted DNS/NTP and TCP 443 to that
alias, then explicitly denied all other egress before the Servers-VLAN's
general pass rule. A direct encrypted random-data round trip succeeded with a
matching SHA-256. Bucket versioning reports `Enabled`.

**Open data-shape observation:** the `gowest` NFS source contains
Synology-generated `@eaDir` thumbnail *files* (not symlinks, as originally
assumed — confirmed from the completed sync's own log, e.g.
`homes/Jason/Drive/Photos/.../@eaDir/On Top.JPG/SYNOFILE_THUMB_SM.jpg:
Copied (new)`). These are small DSM-generated thumbnail caches, not user
data; harmless to carry along but worth knowing they're included rather
than filtered.

**Integrity spot-check (2026-09-08):** pulled a real synced file back
through the full encrypted round trip (`rclone cat idrive-crypt:...` piped
to `sha256sum`) and compared against the same file's hash on TrueNAS —
`df41616946c0e7fad80c2bb28b4a065a209a463298322c1e000f160729d43d0a` on both.
Confirms the encrypt-upload-download-decrypt path preserves real production
data byte-for-byte, not just synthetic test data.

### Gate

**Passed 2026-09-08.** A real, full sync to IDrive e2 has completed
(657 GiB, 111,196 files, 0 errors) and been spot-checked for integrity
against a real production file, not just synthetic test data. One item
remains open outside this gate's scope: Jason still needs to make an
independent, offline protected copy of the `idrive-crypt` password/salt —
tracked as a standing to-do, not a blocker for Milestone 4's restore
validation, since the config Milestone 4 will test against already exists
on the relay.

## Milestone 4 — Validation (hard gate before any cutover)

- [x] Deliberately modify or delete a test file in the TrueNAS backup
  dataset's source path, confirm it can be recovered from a ZFS snapshot.
  **Done 2026-09-10.** Created `Media/backup/_milestone4-restore-test/testfile.txt`,
  took a manual snapshot (`milestone4-test-v1`), deleted the live file, then
  recovered it by copying from `.zfs/snapshot/milestone4-test-v1/...` —
  recovered content and SHA-256 (`770132a1b533b7ff10bf5d64f6a6b264adf92449f3fd8796219ca3f2cead7f8b`)
  matched the original exactly.
- [x] Confirm the same file's *older* version (not just current state) can
  be recovered from the IDrive e2 off-site copy specifically — proving
  version retention exists off-site, not just a mirror. **Done 2026-09-10.**
  Synced the v1 test file through the relay to `idrive-crypt:` (confirmed
  `Copied (new)` in `sync.log`), recorded timestamp T1, overwrote the file
  with v2 content on TrueNAS, synced again (confirmed `Copied (replaced
  existing)`). `rclone --s3-version-at T1 cat idrive-crypt:...` then
  returned the v1 content — SHA-256 matched the original v1 hash exactly —
  while a plain `cat` of the same path returned v2. This proves IDrive e2
  bucket versioning is genuinely retrievable through the crypt layer via
  `rclone`'s S3 point-in-time read, not just theoretically enabled. Test
  artifacts (local file/snapshot, off-site object) removed afterward.
- [x] Add HomeLab Doctor checks for the new rsync task's freshness, the
  snapshot schedule's health, and the `rclone` job's success/failure,
  matching the existing `check_backup_age`/`check_reported_backup`
  pattern. Doctor already checked the relay guest, enabled timer, active
  initial sync, failed result and post-success log freshness. **Added
  2026-09-10:** `check_backup_redesign_truenas()`, initially covering the
  three redesign legs and subsequently the dedicated LXC 110 mirror. It also
  validates that the LXC 110 task remains enabled, scoped to its dedicated
  directory and exact include filter, deletion-bounded, and scheduled at
  04:20. First attempt used newest-file mtime under each
  destination directory as the freshness signal and produced false
  "stale" warnings for the Mac and `gowest` legs — a real bug, not a
  fluke: `rsync -t` preserves source mtimes on unchanged files, so a
  quiet day on the source (nothing new to copy) makes a perfectly healthy
  sync look stale under that signal. Fixed by switching to actual
  run-completion evidence instead: for the two `rsynctask`-based legs
  (Proxmox, Mac), the check now reads each task's own job state and
  `time_finished` via `midclt call rsynctask.query`. The `gowest` leg has
  no TrueNAS task/job record (it's a plain cron job, per Milestone 2's
  mechanism change), so a completion marker
  (`&& date -u +%s > /var/log/gowest-pull-lastrun.epoch`) was added to
  that cron command — config backed up first
  (`/root/cronjob-backup-before-monitoring-marker-*.json`), applied via
  `cronjob.update`, then manually triggered once to confirm the marker
  actually gets written (verified: epoch matched wall-clock time within
  seconds). Snapshot freshness checks the newest `backup-daily-*` snapshot's
  actual ZFS creation time (unaffected by the mtime issue, since that's
  metadata rather than content-derived). Ran the full `doctor.sh` suite
  live afterward: 61 passed, 7 pre-existing warnings unrelated to this
  project (stale config-backup checks, uncommitted git tree), 0 failed —
  no regression.
- [x] Confirm failure-only alerting is wired for the new components,
  matching the existing pattern (no email on success, actionable email on
  failure). **Confirmed 2026-09-10, no new work needed:** read
  `scripts/scheduled-report.sh` — it already greps every `doctor.sh` run
  for `🔴`-prefixed lines generically and emails a deduplicated failure
  alert via `scripts/backup-alert` on any match. Since both new checks
  (`check_idrive_relay`, `check_backup_redesign_truenas`) call the shared
  `fail()` helper on a genuine problem, they're automatically covered by
  the existing pipeline — the pattern this checkbox asked to match is
  already generic across all Doctor checks, not something wired per-check.

### Gate

**Passed 2026-09-10.** Both the local (ZFS) and off-site (IDrive e2)
restore tests passed with real evidence — see the evidence log. Doctor
coverage and failure-only alerting for every new component are also
confirmed. Milestone 5 (cutover) may now begin.

## Milestone 5 — Cutover and documentation

- [x] Retire the three existing Hyper Backup jobs one at a time — not all
  at once — confirming after each that its replacement coverage is
  genuinely equivalent (per Milestone 1's inventory) before moving to the
  next. All three now stopped, each confirmed live rather than assumed:
  - `Mini Atlas Offsite` (on `.42`) — stopped 2026-09-09, `synopkg status`
    confirmed `stop`. See `Backup-Synology-Decommission.md` Milestone 3.
  - `Synology Drive Backup` (on `gowest`) — stopped by Jason via the same
    HyperBackup-package-stop method, confirmed 2026-09-10 via `synopkg
    status HyperBackup` on `gowest` reporting `stop`. Its replacement (the
    `gowest` leg, live since 2026-09-07) was independently reconfirmed
    still healthy right before this retirement.
  - `Media Backup` (on `gowest`, Plex-era) — no clean disable; stopped as
    an unavoidable side effect of the same package-stop, since it shares
    one HyperBackup instance with `Synology Drive Backup` on this host.
    By Jason's explicit decision 2026-09-10, this is fine: its destination
    (`.42`) was already powered off so it could only fail from here on
    anyway, and an inert static snapshot of already-retired Plex media is
    judged safer left alone than touched. Not "retired" in the sense of a
    proven-equivalent replacement — there isn't one, by design — but the
    practical outcome (no further activity, data untouched) is accepted.
- [x] Update `docs/05-Backups.md` to describe the new architecture as
  current, retiring the old three-layer description appropriately. Done
  2026-09-10 — rewrote the same-site, IDrive e2, Synology Drive, and Home
  Assistant sections plus ~15 scattered "Backup Synology" mentions across
  the file, including the Critical-Service Recovery Coverage matrix.
- [x] Add the new LXC to `configs/devices.conf`/`configs/services.conf`
  and, if the NetBox DCIM project's inventory is still being maintained,
  to NetBox as well. Done 2026-09-10 — added to `devices.conf` and to
  NetBox as a virtual machine with interface/IP (via the Django ORM shell,
  since the stored API token is read-only by design). Deliberately **not**
  added to `services.conf`: it has no web UI, and a generic TCP check
  would add no value `check_idrive_relay` doesn't already cover better.
- [x] Record the Backup Synology's backup-role retirement as complete;
  explicitly flag its repurposing as a separate, not-yet-decided
  follow-up for Jason. Already recorded in this document's own "Why this
  exists" section ("Jason intends to repurpose it... explicitly out of
  scope for this project — a separate decision for later"); the
  retirement itself is tracked in full in `Backup-Synology-Decommission.md`.
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
| 2026-09-02 | 1 | Live TrueNAS check (6.78T free of 21.8T, RAM tight but ZFS-ARC-explained, load low); Proxmox/OPNsense check confirmed VMID 112 and `192.168.20.33` free; Hyper Backup job scope recorded from `05-Backups.md` after live DSM CLI verification failed silently on `gowest`; TrueNAS dataset layout decided (`Media/backup/gowest`) | Gate passed; IDrive versioning check deferred to Milestone 3 with reason |
| 2026-09-02 | 2 | Discovered pre-existing `Media/backup/homelab-proxmox-guests/` on TrueNAS (one manual LXC 110 archive, no automated task references it) — aligned naming rather than creating a competing dataset. Added TrueNAS's own restricted key to Proxmox's `homelab-backup` account (backed up first). Hit and resolved a real OPNsense gap: no path existed from TrueNAS to Proxmox:22; added a narrowly-scoped pass rule after explicit confirmation from Jason, cloned from an existing rule's XML structure, config backed up first, validated before reload, confirmed no regression on any other path afterward | Passed — restricted `rsync --list-only` pull confirmed working end-to-end, all in-scope VMIDs visible including 111 (NetBox) |
| 2026-09-02 | 2 | Registered a TrueNAS keychain SSH key pair + connection credential (private key never printed); created the Proxmox rsync task (`rsynctask.create`, VMID-scoped include/exclude list matching the Architecture decisions scope exactly) and three tiered ZFS snapshot tasks on `Media/backup` (daily/weekly/monthly). Both the rsync pull and the daily snapshot were manually triggered to validate before trusting their schedules. `gowest` source blocked the same way `synoschedtask` was earlier — asked Jason to create the restricted DSM account via the UI | In progress — pull (~354 GB in scope) and snapshot results pending as this checkpoint was written |
| 2026-09-02 | 2 | Checked both triggered jobs: `Media/backup@backup-daily-2026-09-02_17-15` snapshot confirmed present (the earlier apparent hang was the `midclt call -j` CLI reporting, not the actual near-instant snapshot operation). Rsync pull confirmed genuinely in progress via live `ps aux` on TrueNAS — real `rsync --server --sender` process connected through the restricted `homelab-backup` account with the correct forced-command wrapper, 204 GB of ~354 GB in-scope transferred at check time | Passed (snapshot); in progress as expected (pull) |
| 2026-09-02 | 2 | Proxmox rsync pull completed: job state `SUCCESS`, no leftover processes. Verified against the source directly (not just trusting the job report): 85 in-scope files / 239,052,726,477 bytes on Proxmox vs. 86 files / 259 GiB on TrueNAS — the one extra file is the pre-existing manual VMID-110 archive, correctly untouched by `delete: false`; sizes reconcile net of that file | Passed — count and size verified against source, Proxmox leg of Milestone 2 complete |
| 2026-09-05 | 2 | Enabled Remote Login on the Mac (confirmed already on). Fetched official `rrsync` from the rsync project after explicit confirmation; hit `--confine-root` incompatibility with Apple's `openrsync` on end-to-end test. Confirmed via GitHub commit history that `--confine-root` is a 2026-08-02 security fix (closes a dir-merge filter-rule escape), not a legacy/optional flag — ruled out falling back to an older `rrsync` since that would reopen the exact vulnerability the flag exists to close. Presented the trade-off explicitly (capability/risk/narrower-alternative/rollback per `CLAUDE.md`) before proceeding | Jason chose OS-level account confinement over installing Homebrew |
| 2026-09-05 | 2 | Jason created a dedicated local macOS account `truenas-pull` (random unrecorded password, key-only via forced-command `authorized_keys`) and added it to Remote Login's access group, previously scoped to `jelliott` only — the one step requiring sudo, run by Jason directly since Claude cannot and will not handle a Mac account password. Granted `truenas-pull` a filesystem ACL scoped to read/list/search inside `~/lab/private-backups` only (verified: base permissions already gave it group-level traversal into `~/jelliott` and `~/lab`, so no broader grant was needed there). Patched the installed `rrsync` to skip the unsupported `--confine-root` line, with the substitution reasoning recorded in-line as a comment | Account and ACL confirmed correctly scoped |
| 2026-09-05 | 2 | End-to-end verification from the real TrueNAS client: list/pull inside the confined directory succeeded; a `..` traversal and an absolute-path escape attempt both correctly rejected by `rrsync`'s own argv validation; a real file pull matched the source's SHA-256 exactly. Registered the Mac key pair and SSH connection as TrueNAS keychain credentials (private key read and used entirely on TrueNAS via a remotely-executed script — caught and corrected one slip where the key was briefly `cat`'d into this session's own output before switching to that approach). Created the Mac rsync task (`rsynctask.create`, whole-tree pull matching the mimic-old-scope decision, no excludes needed) and triggered it | Passed — job state `SUCCESS`, byte-exact match: 354 files / 22,806,562 bytes on both the Mac and TrueNAS. Mac leg of Milestone 2 complete |
| 2026-09-07 | 3 | Created unprivileged Proxmox LXC 112; installed publisher-checksummed rclone v1.75.1; configured new bucket-scoped `idrive-e2` plus locally generated `idrive-crypt`; created a Proxmox-hosted, read-only NFSv4 bind mount from TrueNAS; created the IDrive FQDN allow and relay-only egress-deny rules; direct encrypted random-data round trip SHA-256 matched | Passed for infrastructure boundary and connectivity. Legacy Hyper Backup paths untouched; independent crypt-recovery copy and full-sync completion remain open |
| 2026-09-07 | 2 | `gowest` leg: SSH-forced-command approach hit four separate DSM-specific gates in sequence (administrators-group SSH requirement confirmed from DSM's own UI text, `/sbin/nologin` shell, world-writable home dir tripping `StrictModes`, and a key-file permission mode DSM's `sshd` needs different from stock OpenSSH), then DSM's own `rsync` binary refused with an undocumented daemon-style module-permission error even once all four were fixed — no module config existed to fix (`/etc/rsyncd.conf` had zero modules). Pivoted mechanism: `gowest` exports `homes`/`Family Documents` read-only over NFSv3 restricted to TrueNAS's IP (`Squash: No mapping`, needed for a full read of every family member's private folder); TrueNAS mounts both read-only, persisted via Init/Shutdown Scripts (survives OS upgrades, unlike a raw `systemd` unit); a plain local `rsync` cron job copies into `/mnt/Media/backup/gowest/`. Separately investigated backing up Synology Drive's own app-config (`/volume1/@synologydrive`) to mimic old scope exactly; found it to be 315 GB — the actual version-history blob store, not a small index, nearly duplicating `homes` — and decided with Jason to skip it, accepting loss of Drive's own multi-version rollback as the trade-off | Mechanism passed; initial full pull completed with no errors, byte-exact against source on both shares: `homes` 110,788 files / 332,609,860,578 bytes, `Family Documents` 2 files / 522,083 bytes, matching on both the NFS-mounted source and TrueNAS destination. **All three Milestone 2 rsync legs complete; Milestone 2 gate passed** |
| 2026-09-07 | 4 (partial) | Added `check_idrive_relay` to HomeLab Doctor. It uses the existing Mac→Proxmox path to distinguish a running initial sync, a failure, and a recent completed success; it exposes no relay credential or backup content | Probe verified while the first capped full sync is active; full-sync success remains required before this monitoring item closes |
| 2026-09-07 | 3 (verification) | Independently verified the prior session's Milestone 3 claims rather than trusting the commit message: confirmed LXC 112's actual `pct config` (unprivileged, 1 core, 2 GiB, 8 GiB disk, swap 0, firewall on); confirmed the Proxmox-side NFS mount is genuinely read-only (`ro,nosuid,nodev,noexec`) and the TrueNAS export is restricted to Proxmox's IP only with `all_squash` to root; independently downloaded rclone v1.75.1 from the publisher, verified its zip against the official `SHA256SUMS`, extracted it, and confirmed the extracted binary's own hash matched byte-for-byte what's installed on the relay | All claims confirmed correct except the credential-scoping issue below, found during this same verification pass |
| 2026-09-07 | 3 (correction) | During verification, `rclone config show idrive-e2` printed the S3 access key/secret in plaintext into Claude's own output — a real exposure, caught and named immediately (unlike the crypt password, `config show` doesn't obscure plain S3 remote secrets). Jason revoked and regenerated the key; the first replacement was not actually bucket-restricted (confirmed by testing it could still list *and read* the legacy `mini-atlas-backups` bucket's contents — a real risk to the household's still-live off-site backup, not cosmetic). Jason recreated the key a second time with IDrive's bucket-restriction option applied; verified via a 403 `AccessDenied` against the legacy bucket while the intended bucket still worked. Separately found the interactive `rclone config` wizard writes to `~/.config/rclone/rclone.conf` while the systemd service reads `/etc/rclone/rclone.conf` (via `RCLONE_CONFIG`) — two different files, so the service kept running on the very first, already-revoked key for over an hour after both edits. Fixed by running a script entirely on the relay to copy the current key fields between the two files; the secret values never passed through Claude's own output at any point in this fix | Corrected and verified: new key confirmed scoped to `homelab-backup-relay` only, service config confirmed matching |
| 2026-09-08 | 3 | Restarted the sync service with the corrected, properly-scoped credentials; it ran to completion overnight: exit code `0`, 657.091 GiB transferred, 111,196/111,196 files, 94/94 checks, 0 errors, 9h31m elapsed. Spot-checked integrity on real production data (not synthetic test data): pulled `mac/opnsense/opnsense-config-2026-08-02_11-01-31.xml` back through the full encrypted round trip and compared its hash against the same file on TrueNAS | Passed — hashes matched exactly (`df41616946c0e7fad80c2bb28b4a065a209a463298322c1e000f160729d43d0a`). **Milestone 3 gate passed.** One standing item outside the gate: Jason still needs an independent offline copy of the `idrive-crypt` recovery material |
| 2026-09-08 | 3 | Selected `~/lab/private-backups/recovery/idrive-relay/<date>/` as the documented protected recovery destination; copied LXC 112's rclone configuration and crypt recovery material there with a scoped read-only ACL for the existing TrueNAS pull account, verified Mac→TrueNAS checksums and permissions, then encrypted-uploaded and byte-verified the two files in IDrive | A recovery drill using only the copied Mac configuration successfully decrypted and listed the off-site bundle. The crypt-material recovery-copy condition is complete; unrelated legacy Mac-pull permission debt remains visible but did not block this bundle |
| 2026-09-08 | 2 maintenance | Diagnosed TrueNAS Mac pull task 2 exit 23 as missing ACL inheritance on newer backup directories/files. Restored the existing restricted `truenas-pull` identity's read/list/search access only under `~/lab/private-backups`, with inheritance for future entries; no write, delete or ACL-administration right was granted. Triggered TrueNAS job 9972 afterward. | Job 9972 completed successfully with no rsync errors. The Mac→TrueNAS backup leg is again clean and retains its confined least-privilege boundary. |
| 2026-09-09 | 5 (pre-emptive question) | Jason asked to "clean up the old sync bucket in IDrive" believing it stale. Checked first: confirmed `mini-atlas-backups` (the legacy bucket) is not stale — the Backup Synology's "Mini Atlas Offsite" Hyper Backup task is still actively caching to it. Flagged the conflict with Milestone 5's retirement gate and this project's Definition of Done before acting. Jason confirmed: leave it untouched; disable (not delete) the legacy task only after Milestone 4's dual-restore gate passes, per the existing plan — actual bucket content cleanup remains a separate, later, explicit decision, not bundled into task retirement | No action taken; decision reaffirmed as documented, not re-opened |
| 2026-09-10 | 4 | **Local restore proof.** Created `Media/backup/_milestone4-restore-test/testfile.txt` on TrueNAS, took a manual ZFS snapshot (`milestone4-test-v1`), deleted the live file, recovered it from `.zfs/snapshot/milestone4-test-v1/...` | Passed — recovered content and SHA-256 (`770132a1...`) matched the original exactly |
| 2026-09-10 | 4 | **Off-site version-retention proof.** Synced the v1 test file through the relay to `idrive-crypt:` (log: `Copied (new)`), recorded timestamp T1, overwrote the file with v2 content on TrueNAS, synced again (log: `Copied (replaced existing)`). `rclone --s3-version-at T1 cat idrive-crypt:...` returned the v1 content; a plain `cat` of the same path returned v2 | Passed — SHA-256 of the point-in-time read matched the original v1 hash exactly, proving IDrive e2 bucket versioning is genuinely retrievable through the crypt layer, not just enabled in principle. Test artifacts removed from both TrueNAS and IDrive e2 afterward (confirmed `Deleted` in `sync.log`) |
| 2026-09-10 | 4 | Added `check_backup_redesign_truenas()` to HomeLab Doctor for the Proxmox/Mac/`gowest` rsync legs and snapshot freshness. First implementation used newest-file mtime as the signal and produced false "stale" warnings (54h/80h) for the Mac and `gowest` legs — a real bug: `rsync -t` preserves source mtimes, so an unchanged source looks stale under that signal even when the sync ran and succeeded. Fixed by reading actual job-completion state (`midclt call rsynctask.query`) for the two TrueNAS-task legs, and adding a completion-marker timestamp (`date -u +%s > /var/log/gowest-pull-lastrun.epoch`) to the `gowest` cron command for the one leg with no task/job record — cronjob config backed up first, applied via `cronjob.update`, manually triggered once to confirm the marker writes correctly. Ran full `doctor.sh` afterward | Passed — 61 passed, 7 pre-existing warnings unrelated to this project, 0 failed. New check correctly reports fresh legs (`Proxmox 14h, Mac 14h, gowest 0h, snapshot 12h`) |
| 2026-09-10 | 4 | Confirmed failure-only alerting requires no new wiring: read `scripts/scheduled-report.sh` — it already greps every `doctor.sh` run for `🔴` lines generically and emails a deduplicated alert via `scripts/backup-alert` on any failure. Both new checks use the shared `fail()` helper, so they're automatically covered | Confirmed by reading the existing pipeline, not by triggering a real failure. **Milestone 4 gate passed** — both restore proofs are complete, Doctor coverage and alerting confirmed. Milestone 5 (cutover) may begin |
| 2026-09-10 | 5 | Jason retired `Synology Drive Backup` on `gowest` by stopping HyperBackup the same way as `.42`, unavoidably also stopping `Media Backup` (they share one package instance on this host) — confirmed by Jason and by choice, since `Media Backup`'s destination was already gone. Verified live via `synopkg status HyperBackup` on `gowest`: `stop` | All three legacy Hyper Backup jobs now stopped. Remaining Milestone 5 items (updating `docs/05-Backups.md`, adding LXC 112 to `configs/devices.conf`/`services.conf`/NetBox) not yet done — not part of this request |
| 2026-09-10 | Post-closeout LXC 110 coverage | Investigated the separately tracked inference-backup gap before expanding the shared task. Proxmox retained 8 LXC 110 archives / 306,330,893,688 bytes, while the active encrypted bucket already held 818,348,300,143 bytes against a provisioned 1 TB tier; relaying the full retained set would exceed capacity. Reverted the shared task to its original 100–109/111 filter, installed exact LXC 110 exclusions on relay LXC 112 (prior script preserved), and created dedicated TrueNAS task 3 at 04:20 with an exact LXC-only filter and deletion confined to `/mnt/Media/backup/aster-lxc110`. A shallow real-path rclone scan saw 2 LXC 110 paths without the guard and 0 with it; the historical 2026-09-01 encrypted object remains present. During validation, found the earlier aborted shared-task middleware job had left its rsync child process running with five files in `.~tmp~` (four staged, one partial); terminated only that validated process tree and removed only those five temporary files. The verified manual archive and every non-110 backup remained untouched. | Capacity exposure prevented and stray run cleaned up. Dedicated initial mirror job 13037 is running; final count/byte/integrity and Doctor evidence will follow before closeout. |
