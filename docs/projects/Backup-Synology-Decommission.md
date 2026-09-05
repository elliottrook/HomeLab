# Backup Synology Decommission and Storage Redeployment

> Status: Active — Milestone 1
>
> Project owner: Jason
>
> Last updated: 2026-09-05

## Authorization

**Not yet granted.** This project starts under the repository default in
`CLAUDE.md`: ask before every meaningful action. Jason may grant a
per-project authorization later; until then every state-changing step needs
its own approval.

Two conditions are **not** waivable by any authorization granted later,
because they are conditions of the project rather than steps within it:

- **The off-site continuity gate (Milestone 3).** The Backup Synology is
  today the *only* path to off-site storage. It may not be powered down,
  and its disks may not be touched, until a replacement off-site copy exists
  and a real file has been recovered from it.
- **The disk-destruction gate (Milestone 5).** Redeploying the DS220j's
  disks into TrueNAS destroys their contents. That step requires explicit
  per-action approval on the day, regardless of any standing authorization,
  and only after the observation period in Milestone 4 has passed.

## Purpose

Retire the Backup Synology (`gowest-backup`, DS220j, `192.168.20.42`),
redeploy its disks into TrueNAS, and leave the lab with backup coverage that
is equal or better than today's — including a working off-site copy.

## Why this exists

The DS220j is not slow, it is **starved**. Measured live 2026-09-05:

| Host | Model | RAM total | RAM available | Load |
|---|---|---:|---:|---|
| `gowest-backup` | DS220j | **484 MB** | 189 MB | 0.13 |
| `gowest` | DS920+ | 7,792 MB | 5,285 MB | 5.05 |

Hyper Backup performs deduplication, compression, versioning and encryption
on the destination. Doing that against multi-terabyte jobs in under half a
gigabyte of RAM is what produces the observed hangs. No network or
configuration change addresses this; the hardware is simply undersized for
the role it holds.

**Two problems were previously conflated and are now separated:**

1. **DS220j hangs under Hyper Backup load** — RAM starvation. Real, unfixed,
   and the reason for this project.
2. **VLAN 10 clients failing against the main NAS** — asymmetric routing
   caused by the NAS's dual-homing. **Fixed 2026-09-05**, documented in
   `Current-Network-Baseline.md`. This never affected `.41 → .42` Hyper
   Backup traffic, which is same-subnet and never traversed OPNsense.

Conflating these two made the Synology units look generally unreliable. Only
one of them actually is, and only in the destination role.

## Relationship to `Backup-Architecture-Redesign`

This project is the **successor** to the item that project explicitly placed
out of scope:

> "Deciding or implementing the Backup Synology's repurposed role — a
> separate decision for Jason, tracked outside this project."

It does **not** re-open that project's architecture decisions. Those stand:

- **TrueNAS is the backup hub.** `gowest` is a source, never a destination.
- **Local replication is plain rsync over SSH**, not Hyper Backup.
- **Off-site is a minimal Proxmox LXC running `rclone` with a `crypt`
  remote** to IDrive e2 — not Hyper Backup from a Synology.

A proposal to make the main Synology the backup hub with Hyper Backup pushing
to IDrive was considered on 2026-09-05 and **rejected**: it would reintroduce
the exact destination-role processing load that starves the DS220j, onto a
NAS that also serves Immich, Drive and media. Being an rsync *source* is
light; being a Hyper Backup *destination* is not.

**Hard dependency:** `Backup-Architecture-Redesign` must reach its
Milestone 4 validation gate before Milestone 3 here can begin. Until its
`gowest` source, Mac source and off-site relay legs are live and proven, the
DS220j still holds coverage that nothing else replaces.

## Authoritative baseline (verified live 2026-09-05)

Not copied from documentation — read from the running systems.

**What the Backup Synology uniquely holds:**

| Path | Size | Newest content |
|---|---|---|
| `/volume1/Backup/GoWest_1.hbk` — "Media Backup" | 5.7 TB | 2026-08-30 ⚠️ 6 days stale |
| `/volume1/Backup/GoWest_2.hbk` — "Synology Drive Backup" | 103 GB | 2026-09-05 00:01 |
| `/volume1/Backup/HomeLab-Backups/automated/` | 6.1 MB | 2026-09-05 04:41 |
| `/volume1/HomeAssistant-Backups` | 551 MB | not yet inventoried |

**What it uniquely does:** it is the **only** host pushing off-site.
Hyper Backup task "Mini Atlas Offsite" → `s3.us-west-4.idrivee2.com`, bucket
`mini-atlas-backups`, target `GoWest_Backup_1.hbk`, `enable_data_encrypt=true`,
last cache activity 2026-09-04 23:35. The main Synology has **no** S3 target
configured — its two Hyper Backup jobs both land on `.42`.

**What already replaces part of it:** TrueNAS
`/mnt/Media/backup/homelab-proxmox-guests`, 341 GB, 119 archives, daily 04:00
rsync pull, newest 2026-09-05 02:43. Verified 2026-09-05 by `zstd -t` on the
three newest archives plus the 9 GB `qemu-105` archive, and by byte-exact size
comparison against the Proxmox source on five archives.

**What does not yet replace it:** TrueNAS `/mnt/Media/backup/mac` and
`/mnt/Media/backup/gowest` are both **empty** — 0 files. Those legs of the
redesign are not started.

**Correction to existing docs:** several documents describe the Backup
Synology as "currently offline (active incident)". It is **up**, 5 days
uptime as of 2026-09-05, idle, and actively receiving Hyper Backup jobs.
Those references are stale and are corrected as part of Milestone 1.

## Scope

- Inventory everything the DS220j holds or does that nothing else covers.
- Confirm replacement coverage exists and is proven, not assumed.
- Migrate or consciously retire anything unique it holds.
- Power it down, with an observation period before anything irreversible.
- Redeploy its disks into TrueNAS.
- Decide Immich and family-cloud placement **from measurement**, not
  assumption.

## Out of scope

- Re-opening `Backup-Architecture-Redesign`'s architecture decisions.
- Changing how the main Synology serves production files.
- The Aster llama.cpp (LXC 110) backup gap — pre-existing and separately
  tracked.
- Any change to Frigate recording retention or media libraries.

---

## Milestone 1 — Inventory and dependency mapping

- [ ] Full inventory of `/volume1` on `.42`: every share, its size, its
      newest content, and whether any other copy exists.
- [ ] Determine whether `Media Backup` (5.7 TB, 6 days stale) is still
      required at all. The redesign already decided **not** to carry it
      forward, since Plex source media is retired — confirm that still holds
      and that nothing unique lives only there.
- [ ] Inventory `/volume1/HomeAssistant-Backups` (551 MB) — is this covered
      by HA's own backup task or the Proxmox guest archive of VM 103?
- [ ] Identify every host, task or credential that references `.42`,
      including DSM tasks on `gowest`, Doctor checks, and repo scripts.
- [ ] Record the IDrive e2 bucket's current contents, versioning and
      retention, so the replacement can be proven equivalent.
- [ ] Correct the stale "Backup Synology is offline" references across
      `docs/05-Backups.md`, `02-IP-Addressing.md`,
      `Backup-Architecture-Redesign.md` and `configs/devices.conf`.

### Gate

Do not begin any migration until every unique item on `.42` is either
matched by a proven copy elsewhere or explicitly marked for retirement with
Jason's agreement in writing here.

---

## Milestone 2 — Complete the replacement coverage

Depends on `Backup-Architecture-Redesign` Milestones 2–3.

- [ ] `gowest` rsync source leg live (its Milestone 2 item, blocked on a
      restricted DSM user).
- [ ] Mac source leg live — TrueNAS `/mnt/Media/backup/mac` non-empty and
      current.
- [ ] Off-site relay LXC deployed with `rclone` + `crypt` to IDrive e2.
- [ ] Doctor coverage and backup-age alerting extended to each new leg, so a
      silent stall is detectable. **Explicitly required**: the 2026-09-04 AP
      Switch outage ran six days unnoticed, and `Media Backup` has been
      quiet for six days without anything flagging it.

### Gate

Every category of data the DS220j protects has a live, monitored replacement
that has produced fresh content — not merely a configured job.

---

## Milestone 3 — Off-site continuity gate

**The DS220j is currently the only path off-site. This gate exists so that
fact is never quietly forgotten.**

- [ ] Real-file restore test from the new IDrive e2 off-site copy — a file
      recovered, opened and verified, not a listing.
- [ ] Real-file restore test from a TrueNAS ZFS snapshot.
- [ ] Both restores evidenced in the log below with timestamps.
- [ ] Only then: disable, but do not delete, the "Mini Atlas Offsite" task
      on `.42`.

### Gate

**No power-down before both restores pass.** Losing the only off-site path
to save a few watts is not a trade this lab makes.

---

## Milestone 4 — Power down and observe

- [ ] Disable `.42`'s Hyper Backup tasks (disable, not delete — reversible).
- [ ] Power down `.42`, leaving disks intact and untouched.
- [ ] **Observation period of at least 14 days** with the unit powered off
      but recoverable. Nothing depending on it may surface in that window:
      Doctor clean, backups current, no restore request unmet.
- [ ] Remove `.42` from `configs/devices.conf`, Doctor checks, the sandbox
      allowlist in `CLAUDE.md` and `.claude/settings.json`, and NetBox.

### Gate

Fourteen quiet days. If anything surfaces, power it back on — that is the
whole point of leaving the disks intact.

---

## Milestone 5 — Storage redeployment to TrueNAS

**Destructive and irreversible. Requires explicit per-action approval on the
day, regardless of any authorization granted by then.**

- [ ] Record the DS220j's disk models, sizes, serials and SMART health
      before removal.
- [ ] Confirm TrueNAS's pool layout can accept them usefully — capacity,
      vdev geometry, and whether they extend an existing vdev or form a new
      one. A mismatched disk added to the wrong vdev is not undoable.
- [ ] Confirm SMART health is acceptable for reuse; a marginal disk from a
      retired NAS is not worth pool risk.
- [ ] Wipe and add to TrueNAS, then verify pool health and capacity.
- [ ] Update `03-Hardware-Inventory.md`, the rack diagram and NetBox.

### Gate

Disks are not wiped until Milestone 4's observation period has passed **and**
Jason approves that specific action on that day.

---

## Milestone 6 — Immich and family-cloud placement (measurement-driven)

Deferred deliberately. The original reason to move these off the main NAS was
an assumption that it was overloaded. That assumption needs testing, and the
picture changed on 2026-09-05: with the redesign in place the NAS is a backup
*source* only, which is a far lighter role than being a Hyper Backup
destination.

- [ ] Measure `gowest` load, RAM and IO over a representative week **after**
      the current 95 GB Synology Drive upload completes. The 2026-09-05
      reading of load 5.05 is inflated by that upload and is not a baseline.
- [ ] Decide from that data whether Immich and the family cloud need to move
      at all.
- [ ] Only if they do: plan placement as a separate project.

### Gate

No migration planned on assumption. Either the measurement justifies it or
this milestone closes as "not required".

---

## Rollback summary

| Step | Rollback |
|---|---|
| Disable `.42` Hyper Backup tasks | Re-enable; they are disabled, not deleted |
| Power down `.42` | Power on; disks untouched during the observation period |
| Remove from inventory/monitoring | Restore entries from git history |
| **Wipe and redeploy disks** | **None — this is the point of no return** |

## Evidence log

| Date | Milestone | Action | Result |
|---|---|---|---|
| 2026-09-05 | Baseline | Verified live state of both Synology units, TrueNAS backup datasets, Hyper Backup task/repo configuration and IDrive e2 target | Recorded above; DS220j confirmed at 484 MB RAM, and confirmed as the sole off-site path |
