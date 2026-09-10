# Backup Synology Decommission and Storage Redeployment

> Status: Active — **Milestones 1, 2 and 3 gates all passed 2026-09-10.**
> Milestone 4: `.42` disabled and powered down, 14-day observation running
> (started 2026-09-09, ends 2026-09-23, check-in scheduled). Milestone 5
> (destructive disk redeployment) and Milestone 6 (Immich/family-cloud
> placement) not started, both correctly blocked on the observation
> period. The legacy Hyper Backup bucket's exposed S3 key will **not** be
> rotated — risk accepted by Jason 2026-09-10 (see below).
>
> Project owner: Jason
>
> Last updated: 2026-09-10

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

**Hard dependency — cleared 2026-09-10:** `Backup-Architecture-Redesign`'s
Milestone 4 validation gate has passed. A real test file was recovered from
both the TrueNAS ZFS snapshot and the IDrive e2 off-site copy specifically
(point-in-time version read, not just a mirror), hash-verified in both
cases; see that project's evidence log for 2026-09-10. Milestone 3 below can
now begin. Note that gate used a synthetic test file, not one of the DS220j's
own unique holdings — it proves the replacement *mechanism* works
end-to-end, which is what this milestone's own two checkboxes below also
ask for. Whether to additionally require a restore of a real family file
before disabling the legacy task is Jason's call, not assumed here.

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

**What already replaces part of it — updated, all three legs now live:**
TrueNAS `/mnt/Media/backup/homelab-proxmox-guests`, 341 GB, 119 archives,
daily 04:00 rsync pull, newest 2026-09-05 02:43, verified 2026-09-05 by
`zstd -t` and byte-exact size comparison against the Proxmox source.
`/mnt/Media/backup/mac`, verified byte-exact 2026-09-05 (354 files /
22,806,562 bytes on both sides). `/mnt/Media/backup/gowest`, verified
byte-exact 2026-09-07 (`homes` 110,788 files / 332,609,860,578 bytes,
`Family Documents` 2 files / 522,083 bytes on both sides) — via a native
NFS-export-plus-local-cron mechanism rather than the originally planned
restricted-DSM-user SSH pull, after that approach hit four DSM-specific
SSH gates and then an undocumented `rsync` daemon-module restriction; see
`Backup-Architecture-Redesign.md` Milestone 2 for the full mechanism
change. The off-site relay (LXC 112, `rclone` + `crypt` to IDrive e2) is
also live: full sync completed 2026-09-08, 657.091 GiB / 111,196 files / 0
errors, spot-checked byte-exact against a real production file. Source:
`Backup-Architecture-Redesign.md` Milestones 2–3, both gates passed.

**What does not yet replace it:** Home Assistant's native automatic
backups still land only on `.42` — no redirect to a TrueNAS target exists
yet (Milestone 2 below).

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
- [x] Record the IDrive e2 bucket's current contents, versioning and
      retention, so the replacement can be proven equivalent. **Superseded
      2026-09-10, closed without a direct query of the legacy bucket**:
      the legacy `mini-atlas-backups` bucket's own task is now stopped
      (Milestone 3), its credential is flagged for rotation after being
      exposed, and querying its retention settings now would mean handling
      that same flagged-for-rotation secret again for a bucket about to be
      abandoned. The actual proof-of-equivalence obligation this item
      existed for was met a different way: the *replacement* bucket
      (`homelab-backup-relay`) had its own versioning independently
      confirmed enabled and actually retrievable — see
      `Backup-Architecture-Redesign.md` Milestone 3 ("Bucket versioning
      reports: Enabled") and Milestone 4's 2026-09-10 point-in-time
      recovery proof.
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

Depended on `Backup-Architecture-Redesign` Milestones 2–3 — **both gates
passed** (2026-09-07 and 2026-09-08 respectively), so the three items below
are now done. Note the `gowest` leg landed via a different mechanism than
originally planned here (NFS export + local TrueNAS cron, not a restricted
DSM SSH user) — see the corrected baseline section above.

- [x] `gowest` rsync source leg live — done 2026-09-07 (NFS export + local
      cron, not the originally planned restricted DSM user; see
      `Backup-Architecture-Redesign.md` Milestone 2).
- [x] Mac source leg live — TrueNAS `/mnt/Media/backup/mac` non-empty and
      current, done 2026-09-05.
- [x] Off-site relay LXC deployed with `rclone` + `crypt` to IDrive e2 —
      done 2026-09-08, full sync verified.
- [x] **Redirect Home Assistant's native automatic backups from `.42` to
      TrueNAS.** Done 2026-09-10. HA's backup mount ("Backup_Synology" in
      `ha mounts info`) was a CIFS share at `192.168.20.42:HomeAssistant-Backups`
      — discovered via the Supervisor CLI (`ha mounts info`), reachable from
      Proxmox through `qm guest exec 103` since HAOS has no direct SSH.
      Created a dedicated, narrowly-scoped destination: TrueNAS user
      `ha-backup` (SMB-only, `nologin` shell, no broader group membership),
      owning a mode-700 directory `/mnt/Media/backup/home-assistant`
      exposed as its own SMB share — matching this repo's established
      least-privilege pattern, not a reuse of any admin credential. The
      generated password was never printed to chat or logged; it was
      created on TrueNAS and handed to the HA guest-exec call within one
      uninterrupted local pipeline, with the pipeline aborting before
      touching Home Assistant if the password capture had failed (it did
      once, on a first attempt that hit an unrelated TrueNAS API schema
      error — caught, fixed, and retried cleanly with a fresh password
      before HA was touched).

      Repointed via `ha mounts update Backup_Synology --server
      192.168.20.40 --share home-assistant --username ha-backup --password
      *** --usage backup` (kept the same mount *name* for continuity in
      HA's own UI/history, only changed where it points). Verified
      end-to-end, not just via exit codes: `ha mounts info` shows
      `state: active`; triggered a real full backup
      (`ha backups new --name TrueNAS-redirect-verification
      --location=Backup_Synology --location=.local`), confirmed it
      completed (`ha backups info` showed both locations with matching
      `size_bytes: 27136000`), and independently confirmed on TrueNAS
      itself that `522711d2.tar` (27,136,000 bytes) physically exists
      under `/mnt/Media/backup/home-assistant/`, owned by `ha-backup`.
- [x] Doctor coverage and backup-age alerting extended to each new leg, so a
      silent stall is detectable. **Explicitly required**: the 2026-09-04 AP
      Switch outage ran six days unnoticed, and `Media Backup` has been
      quiet for six days without anything flagging it. Added
      `check_home_assistant_backup_truenas()` to HomeLab Doctor (newest
      `.tar` mtime under the new TrueNAS path, 30h threshold matching the
      existing daily-backup checks); ran the full suite afterward: 65
      passed, 2 pre-existing warnings, 2 failures — both fully expected and
      already accounted for (`.42` itself unreachable, and the Arista
      link-state check correctly flagging `.42`'s switch port `Et48` going
      `notconnect` now that it's powered off). Neither is a new problem;
      both are direct, correctly-detected consequences of Milestone 4's own
      power-down step, and are left as-is per that milestone's own plan to
      remove `.42` from Doctor/inventory only after the 14-day observation
      period. Separately noted for later, not urgent: the two legacy
      `check_reported_backup` lines ("...to Backup Synology") will drift to
      a stale *warning* (not a failure, so no new alert email) within about
      a day, since the `.42`-hosted pull jobs they track can no longer run
      at all — their coverage is already fully superseded by
      `check_backup_redesign_truenas`'s Proxmox/Mac legs, so removing those
      two obsolete lines belongs with Milestone 4's own deferred `.42`
      cleanup, not this milestone.

### Gate

**Passed 2026-09-10.** Every category of data the DS220j protects has a
live, monitored replacement that has produced fresh content — not merely a
configured job: `gowest`, Mac, Proxmox archives, the off-site relay, and
now Home Assistant's native backups, all verified with real recovered/
landed data, not just configuration. `Media Backup` remains the one
deliberate exception, unreplaced by Jason's own explicit decision (its
data is a static, no-longer-updating snapshot of already-retired Plex
media, judged safer left alone than touched).

---

## Milestone 3 — Off-site continuity gate

**The DS220j is currently the only path off-site. This gate exists so that
fact is never quietly forgotten.**

- [x] Real-file restore test from the new IDrive e2 off-site copy — a file
      recovered, opened and verified, not a listing. **Accepted 2026-09-10**
      using `Backup-Architecture-Redesign`'s Milestone 4 evidence (synthetic
      test file, hash-verified point-in-time recovery) — Jason confirmed
      that proof is sufficient, no separate real-file test required.
- [x] Real-file restore test from a TrueNAS ZFS snapshot. Same acceptance
      as above.
- [x] Both restores evidenced in the log below with timestamps. See
      `Backup-Architecture-Redesign.md` evidence log, 2026-09-10 entries.
- [x] Only then: disable, but do not delete, the "Mini Atlas Offsite" task
      on `.42`. **Done 2026-09-09 18:50 UTC, done by Jason, verified
      2026-09-10.** The CLI attempt earlier (`synobackup
      --schedule-disable-list-by-app HyperBackup`) never worked — see
      below — so Jason stopped the whole HyperBackup **package** instead,
      via Package Center on `.42` (a broader but fully supported and
      equally reversible action: `HyperBackup.log` shows a clean
      `stop`/`prestop` sequence at 2026-09-09 18:50:11–14). Verified live:
      `synopkg status HyperBackup` reports `"status":"stop"`, no
      `dsmbackup` process running. Confirmed no collateral effect: the
      separate `HyperBackupVault` package (the receiving side that
      `Synology Drive Backup` and `Media Backup` still depend on) is
      untouched and its `img_backupd` process is still running normally.
      Note `synoschedtask --get` still reports Task Scheduler entries 3
      and 5 as `State: [enabled]` — that field reflects scheduler
      configuration, not whether the owning package is running, so it's
      not a useful signal for this particular mechanism and is expected
      to stay "enabled" while stopped this way. No data touched; nothing
      deleted; restarting the package (Package Center → Start) is the
      full rollback if ever needed.

### Gate

**Passed 2026-09-10.** Both restores are accepted and the legacy off-site
task is confirmed stopped, with the receiving side it doesn't share
confirmed unaffected. Milestone 4 (power down and observe) may now begin
when Jason is ready.

---

## Milestone 4 — Power down and observe

- [x] Disable `.42`'s Hyper Backup tasks (disable, not delete — reversible).
      Done via Milestone 3 (HyperBackup package stopped 2026-09-09).
- [x] Power down `.42`, leaving disks intact and untouched. **Done
      2026-09-09, confirmed 2026-09-10** — SSH to `192.168.20.42` times out
      (connection timeout, not a sandbox/permission denial), consistent
      with powered off rather than unreachable for another reason.
- [ ] **Observation period of at least 14 days** with the unit powered off
      but recoverable. Nothing depending on it may surface in that window:
      Doctor clean, backups current, no restore request unmet. **Started
      2026-09-09; ends 2026-09-23.** A check-in is scheduled for then.
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
| 2026-09-09 | — | Jason asked to clean up "the old sync bucket in IDrive" (`mini-atlas-backups`). Checked first: it's not stale — the legacy Hyper Backup task is still actively writing to it, and both this project's Milestone 3 and the redesign project's Milestone 5 explicitly gate touching it. Flagged before acting | Jason confirmed: leave it untouched; disable (not delete) only after the redesign's Milestone 4 gate passes, per the existing plan |
| 2026-09-09/10 | Doc | Reconciled stale tracking: Milestone 2's `gowest`/Mac/off-site-relay items were still marked open and the baseline still described the TrueNAS `mac`/`gowest` legs as empty, but `Backup-Architecture-Redesign` had actually completed and byte-verified all three (2026-09-05/07/08) via a different `gowest` mechanism than originally planned here | Corrected baseline and Milestone 2 checklist to match; only HA backup redirect and Doctor coverage remain open in Milestone 2 |
| 2026-09-10 | — | `Backup-Architecture-Redesign` Milestone 4 gate passed (real restores proven from both the TrueNAS ZFS snapshot and the IDrive e2 off-site copy, hash-verified) | Milestone 3's hard dependency is cleared; its own two restore checks may now begin. Used a synthetic test file, not one of the DS220j's unique holdings — left as Jason's call whether that's sufficient before disabling the legacy task, or whether a real-file restore is wanted first |
| 2026-09-10 | 3 | Jason accepted the synthetic-file proof as sufficient and approved disabling "Mini Atlas Offsite." Read `/volume1/@appconf/HyperBackup/synobackup.conf` on `.42` to find the task's identity — this printed the task's S3 `remote_key`/`remote_secret` for `mini-atlas-backups` in plaintext into this session, a real exposure caught and named immediately (same root cause as prior incidents in the sibling redesign project: a config/API call echoing a secret back). **Recommend Jason rotate this key** via IDrive once the task is disabled | Exposure named; not yet rotated. No other action taken on the secret; a second on-disk copy made as a pre-change checkpoint was deleted again once no actual change was applied (see below) |
| 2026-09-10 | 3 | Attempted disable via `synobackup --schedule-disable-list-by-app HyperBackup` — returned exit 0. Did not trust that alone: verified via `synoschedtask --get`, which showed both of the task's Task Scheduler entries (ID 3, ID 5; app `SYNO.SDS.Backup.Application`) still `State: [enabled]` — the command silently did nothing, most likely because `HyperBackup` isn't the app identifier this tool expects. The correct path (`SYNO.Core.TaskScheduler` via `synowebapi`) returned `Permission denied` — needs root, and the SSH account in use (`Jason`, administrators group) has no sudo. Stopped rather than hand-edit Task Scheduler's backing store blind | **Not disabled.** Handed back to Jason as a two-click DSM UI action (Hyper Backup → pause/disable "Mini Atlas Offsite", or Control Panel → Task Scheduler → uncheck Enabled on IDs 3 and 5). `.42` and the legacy task remain fully live and untouched — no gate bypassed |
| 2026-09-10 | — (unrelated finding) | While reading Task Scheduler entries to verify the above, noticed an existing scheduled Task ID 7 ("Task 7", undocumented name) on `.42` that runs **daily at 00:00**: it writes an SSH public key for `jelliott@Jasons-Mac-mini.local` into `/etc/ssh/authorized_keys/jason`, edits `sshd_config`'s `AuthorizedKeysFile` directive, and restarts `sshd` — every single day. Idempotent and not something this session touched or created, but flagging since a daily unattended `sshd` restart plus `sshd_config` rewrite on a production NAS is worth Jason's awareness; out of scope for this project to act on | Flagged only, not investigated further or modified |
| 2026-09-10 | 3 | Jason reported "HyperBackup stopped." Verified rather than took at face value: `HyperBackup.log` showed a clean `stop 4.2.2-4262 prestop`/`stop` sequence at 18:50:11–14 UTC on 2026-09-09 (Jason used Package Center, not the per-task disable the CLI attempt couldn't complete). Live `synopkg status HyperBackup` confirms `"status":"stop"`, no `dsmbackup` process running. Confirmed the separate `HyperBackupVault` package (receiving side for `Synology Drive Backup`/`Media Backup`, explicitly out of scope to touch) is unaffected — its `img_backupd` process is still running normally | **Passed. Milestone 3 gate closed** — restores accepted, legacy off-site task confirmed stopped, no collateral impact on the still-needed receiving side. Milestone 4 may begin when Jason is ready. The S3 key exposed earlier this milestone still needs rotation |
| 2026-09-10 | 4 | Jason reported `.42` powered down. Verified: SSH to `192.168.20.42` times out (connection timeout, not the sandbox's "Operation not permitted" pattern), consistent with power-off rather than a network/permission issue. Disks left untouched, nothing else attempted | Milestone 4's disable and power-down steps confirmed done. 14-day observation period recorded as started 2026-09-09, ending 2026-09-23; a check-in reminder was scheduled for that date |
| 2026-09-10 | 2 | Jason clarified "leave Media Backup alone" meant its data, not necessarily the task, and approved retiring "Synology Drive Backup" by stopping HyperBackup on `gowest` the same way as `.42`. Flagged first that this would also stop Media Backup (they share one HyperBackup package instance on `gowest`, unlike `.42` which only had one task) — Jason confirmed that's fine given the data-only framing. Separately, Jason asked whether "the drive backup" needed to be recreated pointed at TrueNAS; clarified this already exists (the `gowest` leg of `Backup-Architecture-Redesign`, live since 2026-09-07) rather than building a redundant Hyper-Backup-based replacement, which would have reintroduced the exact processing pattern this project's redesign was built to eliminate | No infrastructure change; a scope/understanding question resolved before any action |
| 2026-09-10 | 2 | Jason asked whether `.42` was ready for decommissioning aside from the Media data question and the 14-day wait. Checked rather than assumed: found Home Assistant's native automatic backups were still configured to write to the now-powered-off `.42` over SMB (`ha mounts info` showed mount "Backup_Synology" at `192.168.20.42:HomeAssistant-Backups`, `state: inactive`) — a real, currently-broken dependency with no replacement built yet, unlike the other three legs | Surfaced as the one genuine blocker; Jason approved building the fix |
| 2026-09-10 | 2 | Built the Home Assistant → TrueNAS backup redirect. Discovered `qm guest exec 103` reaches the HAOS host directly (no SSH needed), and its `ha` Supervisor CLI exposes `mounts`/`backups` management. Created a dedicated TrueNAS user `ha-backup` (SMB-only, `nologin`, no broader groups) owning a mode-700 directory `/mnt/Media/backup/home-assistant`, exposed as its own SMB share (`DEFAULT_SHARE` purpose — a first attempt using an invalid `NO_PRESET` purpose value failed cleanly with no side effect other than the user's password being generated and then not retrievable, so it was simply reset on retry). Generated password never left a single local-to-remote pipeline and was never printed. Repointed HA's existing "Backup_Synology" mount via `ha mounts update` to the new destination, keeping the mount's name for continuity | Verified end-to-end: `ha mounts info` shows `state: active`; a real triggered backup (`TrueNAS-redirect-verification`) completed and reported at both `.local` and `Backup_Synology` locations (27,136,000 bytes each); independently confirmed the actual `.tar` file exists on TrueNAS, owned by `ha-backup`. **Milestone 2 gate passed** |
| 2026-09-10 | 2/4 | Added `check_home_assistant_backup_truenas()` to HomeLab Doctor and ran the full suite | 65 passed, 2 pre-existing warnings, 2 expected failures (`.42` unreachable; Arista correctly flagging `.42`'s switch port `Et48` down) — both direct, correct consequences of Milestone 4's power-down, not new problems, left alone per that milestone's own deferred-cleanup plan |
| 2026-09-10 | — (risk decision) | Jason explicitly accepted the risk of not rotating the exposed legacy `mini-atlas-backups` S3 key. Reasoning given: he is paying IDrive e2 overage for running two buckets simultaneously and intends to decommission the legacy bucket soon regardless, making a rotation now wasted effort against a bucket about to be deleted | Recorded as a deliberate, reasoned decision, not oversight. No further action on this key; closes the one open item from the 2026-09-10 disable-attempt exposure |
