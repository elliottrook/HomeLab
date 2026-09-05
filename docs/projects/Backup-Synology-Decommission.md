# Backup Synology Decommission and Storage Redeployment

> Status: Active — Milestone 2 (blocked on `Backup-Architecture-Redesign`)
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

- [x] Full inventory of `/volume1` on `.42`: every share, its size, its
      newest content, and whether any other copy exists.
- [x] Determine whether `Media Backup` (5.7 TB, 6 days stale) is still
      required at all. **Decided by Jason 2026-09-05: leave it in place,
      undecided, until a separate decision is made about a media backup
      sourced from TrueNAS.** No replication effort is needed now. It must
      **not** be deleted. See the disk-redeployment consequence recorded in
      Milestone 5 below — this decision blocks that milestone until resolved.
- [x] Inventory `/volume1/HomeAssistant-Backups` (551 MB) — is this covered
      by HA's own backup task or the Proxmox guest archive of VM 103?
- [x] Identify every host, task or credential that references `.42`,
      including DSM tasks on `gowest`, Doctor checks, and repo scripts.
- [ ] Record the IDrive e2 bucket's current contents, versioning and
      retention, so the replacement can be proven equivalent.
- [x] Correct the stale "Backup Synology is offline" references across
      `docs/05-Backups.md`, `02-IP-Addressing.md`,
      `Backup-Architecture-Redesign.md` and `configs/devices.conf`.


### Milestone 1 findings — inventory complete 2026-09-05

**`.42` holds only two shares.** Volume is 7.3 TB, 6.1 TB used, **84% full**.

| Share | Size | Newest content |
|---|---:|---|
| `Backup` | 5.8 TB | 2026-09-05 04:41 |
| `HomeAssistant-Backups` | 551 MB | 2026-09-05 04:53 |

`Backup` breaks down as:

| Item | Size | Newest | Replacement status |
|---|---:|---|---|
| `GoWest_1.hbk` — "Media Backup" | 5.7 TB | 2026-08-30 ⚠️ | Redesign decided **not** to carry forward (Plex retired) — confirm |
| `GoWest_2.hbk` — "Synology Drive Backup" | 103 GB | 2026-09-05 00:01 | ❌ TrueNAS `gowest` leg is **empty** |
| `HomeLab-Backups/automated/private-backups` | 4.3 MB | 2026-09-05 04:41 | ❌ TrueNAS `mac` leg is **empty** |
| `HomeLab-Backups/automated/proxmox-guests` | 12 KB | — | ✅ superseded by TrueNAS (119 archives, verified intact) |

**Four things must be replaced before power-down:**

1. **The only off-site path in the lab.** Hyper Backup "Mini Atlas Offsite" →
   `s3.us-west-4.idrivee2.com`, bucket `mini-atlas-backups`, target
   `GoWest_Backup_1.hbk`. Confirmed `enable_data_encrypt=true` and
   `enable_version_rotation=true`; 7.2 GB local cache at
   `/volume1/@img_bkp_cache`. Nothing else in the lab pushes off-site.
2. **Home Assistant's native backups — a live dependency found by this
   inventory.** HA writes `automatic_backup_*.tar` daily over SMB directly to
   `.42`, roughly 26 MB each, retaining three plus one manual
   `post_server_change` snapshot. Newest 2026-09-05 04:53. The Proxmox VM 103
   guest archive covers the whole VM but **not** HA's native restore format,
   which is the granular and hardware-portable path. Powering `.42` down
   without repointing this stops HA backups **silently**.
3. **Mac config backups.** `automated/private-backups` (4.3 MB) is currently
   the **only copy off the Mac**. The TrueNAS `mac` leg has 0 files.
4. **Synology Drive / homes / Family Documents.** `GoWest_2.hbk` is current
   and active; the TrueNAS `gowest` leg has 0 files.

**Already safely superseded:** the Proxmox guest archives. `.42`'s copy is
now a 12 KB stub of logs and status files while TrueNAS holds 119 archives,
verified 2026-09-05 by `zstd -t` and byte-exact size comparison to source.

**Lab references to `.42` needing removal at Milestone 4:**
`.claude/settings.json` (sandbox allowlist), `CLAUDE.md` (topology table and
allowlist), `configs/devices.conf`, `configs/services.conf`,
`scripts/doctor.sh` (a `gowest-backup` check plus the `synology-pull`
backup-age check), `scripts/lab`, `scripts/backup/guided.sh`,
`scripts/certificate-check.sh`, and NetBox.

**Assumption corrected:** the DS220j was believed to be a passive,
mostly-superseded backup target. It is not — it is an active participant
holding the lab's only off-site path and the only copy of two data sets, and
it is receiving fresh data daily from Home Assistant. The decommission is
correspondingly more involved than "power it off".

### Gate

Do not begin any migration until every unique item on `.42` is either
matched by a proven copy elsewhere or explicitly marked for retirement with
Jason's agreement in writing here.

**Gate status 2026-09-05: PASSED.** Three replacements remain in scope for
Milestone 2 (off-site path, Home Assistant native backups redirected to
TrueNAS, Mac config backups, Synology Drive set — four items, three targets
since Mac and Drive both land on TrueNAS). `Media Backup` is resolved as
"leave in place, undecided, not to be deleted" — it needs no replacement
effort now, but it does add a hard blocking condition to Milestone 5,
recorded there.

---

## Milestone 2 — Complete the replacement coverage

Depends on `Backup-Architecture-Redesign` Milestones 2–3.

- [ ] `gowest` rsync source leg live (its Milestone 2 item, blocked on a
      restricted DSM user).
- [ ] Mac source leg live — TrueNAS `/mnt/Media/backup/mac` non-empty and
      current.
- [ ] Off-site relay LXC deployed with `rclone` + `crypt` to IDrive e2.
- [ ] **Redirect Home Assistant's native automatic backups from `.42` to
      TrueNAS.** Decided by Jason 2026-09-05: these are a network backup and
      belong with the rest, not on a unit being retired. Needs a TrueNAS
      SMB or NFS target HA can write to (its native backup integration, not
      a Proxmox-side pull, since these are HA's own portable backup format —
      distinct from and complementary to the whole-VM guest archive that
      already covers VM 103). Verify at least one backup lands and is
      restorable before treating this leg as done.
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

- [ ] **Blocking condition, added 2026-09-05:** `GoWest_1.hbk` ("Media
      Backup", 5.7 TB) must remain intact and readable on these disks until
      Jason separately decides its fate alongside a TrueNAS-sourced media
      backup. Do not wipe, migrate, or otherwise touch this data as part of
      this milestone — confirm its continued presence immediately before
      any wipe step, not just at planning time.
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

Disks are not wiped until Milestone 4's observation period has passed,
Jason approves that specific action on that day, **and** the Media Backup
data on these disks has either been migrated elsewhere or Jason has
explicitly approved discarding it. Absent that, this milestone stays open
indefinitely — a slow decision here is not a reason to force it.

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
| 2026-09-05 | M1 | Full share inventory of `.42`, reference sweep across repo/Doctor/allowlist, TrueNAS coverage comparison | Four replacements required before power-down; Home Assistant found writing daily backups directly to `.42` — a live dependency not previously recorded anywhere |
| 2026-09-05 | M1 | Presented two open decisions to Jason | Media Backup: leave in place, undecided, not to be deleted — now a hard blocking condition on Milestone 5 disk redeployment. HA backups: redirect to TrueNAS alongside the other network backups — added to Milestone 2 scope |
