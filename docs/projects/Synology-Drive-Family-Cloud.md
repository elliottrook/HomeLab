# Synology Drive Family Cloud Project

## Project handover: Claude

> Status: Milestones 1-3 complete; Milestone 4 done on the Mac mini, laptop
> repeat still open
>
> Project owner: Jason
>
> Last updated: 2026-08-25

## 1. Purpose

Reactivate the existing Synology Drive capability as a simple private family
cloud for file synchronization, Finder integration, mobile access and controlled
sharing. Use the Synology already operating in the HomeLab instead of deploying
a new file platform unless it fails a defined requirement.

The desired experience is intentionally narrower than Nextcloud:

- separate private accounts for family members;
- a live/on-demand drive in macOS Finder;
- iPhone/iPad file access, offline pinning and optional camera upload;
- explicit shared family folders;
- expiring/password-protected links and file requests for friends;
- encrypted storage where practical and HTTPS in transit;
- backup and recovery proven before production reliance.

## 2. Existing environment

| Component | Current location | Role |
|---|---|---|
| Main Synology DS920+ | `192.168.20.41`, Servers VLAN 20 | Synology Drive server and primary family data |
| Backup Synology | `192.168.20.42`, Servers VLAN 20 | Hyper Backup repository and recovery destination |
| OPNsense | Existing gateway/DNS/firewall authority | Access policy and internal DNS |
| Tailscale | Existing private remote-access path | Preferred private administration/access option |
| Hyper Backup | Existing versioned backup workflow | Drive data and configuration protection |

Both Synology systems are production storage appliances. Do not change shared
folders, permissions, encryption or retention without a current backup and a
clear rollback path.

## 3. Design decisions

- Use individual DSM accounts; do not share Jason's administrator account.
- Give each person a private `My Drive` area.
- Enable only deliberately selected Team Folders.
- Start with the LAN/Tailscale access model. Do not broadly expose DSM to the
  Internet merely to make sharing convenient.
- Prefer current Synology Drive clients and macOS On-demand Sync.
- Treat Synology shared-folder encryption as storage-at-rest protection, not
  client-side or zero-knowledge encryption.
- Keep Seafile Community Edition as a fallback only if Synology Drive fails a
  documented client, sharing or encryption requirement.
- Do not enable Synology Office, Chat, Mail or unrelated collaboration packages
  during this project.

## 4. Security boundaries

- Store unique account passwords in the household password manager.
- Require MFA for administrator accounts and consider it for family accounts
  according to usability.
- Grant permissions through groups wherever possible.
- Keep DSM administration separate from ordinary Drive use.
- Use HTTPS for browser/client traffic and validate the certificate/name used.
- Do not commit DSM exports, databases, credentials, recovery keys or share URLs
  containing tokens to Git.
- Record encrypted-folder keys and recovery instructions in protected offline
  storage before depending on encryption.
- Use short expirations and passwords for friend links containing private data.

## 5. Milestone 1 — Discovery and capacity

- [x] Record DSM, Synology Drive Server and Hyper Backup versions.
- [x] Confirm supported macOS/iOS client versions; use macOS Drive Client 4.1 or
  later where supported. — Server-side `SynologyDrive` 4.0.3-27892 requires
  Drive Client 4.0.0+ for DSM 7.3+, satisfied. macOS client requires macOS
  Monterey 12+; Jason's Mac mini runs macOS 26.5.2, well clear. **Important:**
  Synology recently raised the iOS/iPadOS app's requirement to iOS 18+,
  dropping iOS/iPadOS 17 support — confirm every family iPhone/iPad is on
  iOS 18+ before the Milestone 5 pilot.
- [x] Record current main/backup NAS capacity, snapshots and backup growth. —
  Main NAS (`192.168.20.41`): 11 TB total, 6.8 TB used, 3.7 TB free (65%).
  Backup NAS (`192.168.20.42`, DS220j): 7.3 TB total, 5.9 TB used, 1.4 TB free
  (82%) — noticeably tighter headroom than the main NAS. Its primary Hyper
  Backup job (`GoWest_1.hbk`) is 5.7 TB, accounting for most of that usage.
- [x] Inventory existing homes, shared folders, permissions and Drive remnants.
- [x] Confirm whether Drive was previously enabled and identify stale databases,
  clients or Team Folder settings without deleting them.
- [x] Define expected users, devices, initial data size and five-year growth. —
  Six accounts total: Jason (admin, unrestricted), Alisa, Carter, Justin, Jen,
  elliottrook. Non-Jason accounts to be capped at a 100 GB quota each, no
  planned growth at this time. Devices: iPhone client for all six people; Mac
  client for Jason and Alisa; iPad client for Jason.
- [x] Take a current configuration/data recovery checkpoint. — Jason's
  pre-existing Drive content (the 247 GB "Windows Back-up" folder plus a few
  test `.odoc` files) was moved into `/volume1/DriveBackup-20260825/Jason/` on
  the main NAS and verified complete; Jason's `Drive` folder is now empty.
  Alisa/Carter had no Drive folder and Justin's was already empty, so no
  checkpoint was needed for them.

Completion gate: existing state and capacity are documented, and reactivation
will not overwrite or expose existing data. **Reached.**

**Follow-up risk carried into later milestones (not acted on, per the
no-Hyper-Backup-changes rule):** `/volume1/DriveBackup-20260825/Jason/` is not
yet covered by Hyper Backup, so it currently has no off-box copy — only
same-box RAID5 protection. Revisit when Milestone 7 (backup and recovery) adds
Drive-related paths to the backup selection, and note the backup NAS's
comparatively tight 1.4 TB headroom when sizing that addition.

## 6. Milestone 2 — Identity and folder design

- [x] Create or verify one non-administrator DSM account per family member. —
  Alisa, Carter, Justin and Jen are confirmed non-administrator accounts.
  `elliottrook` remains an administrator alongside Jason — a deliberate
  exception (Jason's decision), not an oversight; each got a 100 GB quota on
  `volume1` regardless (DSM's quota UI wouldn't apply one to `elliottrook`
  specifically, since it's an admin account).
- [x] Create family groups and document their intended permissions. — Created
  DSM group `Family` (Alisa, Carter, Jason, Jen, Justin — `elliottrook`
  deliberately excluded per Jason's decision).
- [x] Enable user home service and verify private `My Drive` separation. — Home
  service already enabled. Verification uncovered a real problem: the `homes`
  shared folder's own ACL granted `Alisa` full read/write and `Justin`/`Jen`
  read access to *every* user's home folder (pre-existing, predates this
  project), and creating the `Family` group temporarily made it worse by
  adding blanket read/write for the whole group. Fixed by removing all
  individual-user and group entries from the `homes` shared folder's
  permissions, leaving only `administrators` (Jason + elliottrook) and each
  user's own ownership. Re-audited and confirmed: no ordinary family member can
  now access another's home/Drive folder.
- [x] Define the minimum shared family Team Folders and their owners. — One
  Team Folder: `Family Documents`, read/write for the `Family` group only
  (initially created with individual per-user grants including `elliottrook`
  and the built-in `admin` account by the folder wizard; corrected to
  group-only access).
- [x] Decide which shared folder, if any, requires Synology encryption. — None;
  Jason opted out of Synology encryption for this project.
- [ ] Record the encryption-key backup and reboot/mount procedure before use. —
  Not applicable; no encryption in use.
- [x] Verify an ordinary family user cannot access DSM administration or another
  person's private files. — Private-file access verified and fixed (see home
  service item above). DSM administration access was not tested with a live
  login (Alisa/Carter/Justin/Jen are confirmed outside the `administrators`
  group, which is the standard DSM control for this, but a real login spot
  check would be the gold-standard confirmation if Jason wants one).

Completion gate: the identity and folder model passes least-privilege tests with
representative administrator and family accounts. **Reached** — the one
pre-existing privacy gap found during verification was fixed, not just
documented.

## 7. Milestone 3 — Synology Drive Server

- [x] Install or update Synology Drive Server from Package Center. — Already
  installed and current (v4.0.3-27892, confirmed in Milestone 1).
- [x] Enable only the selected Team Folders in Drive Admin Console. — Enabled
  `Family Documents` only, via Drive Admin Console → Team Folder. Verified via
  `@eaDir` markers (`cloud.tmp.dir`, `clientd.tmp.dir`, `@drive.queues`,
  `SYNO@.fileindexdb`) that Drive is actually managing/indexing the folder,
  not just that the DSM shared folder exists.
- [x] Set conservative version retention based on capacity and recovery goals.
  — 25 max versions, rotate/delete versions older than 30 days.
- [x] Configure file filters and size limits only where justified. — Decided:
  none. `Family Documents` is a small family documents folder, not a
  general-purpose sync target where filtering matters.
- [x] Confirm indexing/database health and expected storage consumption. —
  Drive's internal block store (`/volume1/@synologydrive/@sync`) is
  consuming ~219 GB. Investigated and found Jason's personal My Drive
  currently holds a few hundred GB of photos; Jason will migrate these to a
  dedicated photos app later and asked not to act on this now — recorded as a
  known, accepted, temporary storage consumer, not a fault. No corruption or
  indexing errors observed; Drive's processes (`syncd`, `cloud-workerd`, etc.)
  are running normally.
- [x] Confirm Drive service ports and firewall access remain private and
  scoped. — Drive listens on 6690 (plus DSM's normal 5000/5001/80/443), bound
  to all local interfaces as expected; no port-forward/NAT changes were made
  by this project. QuickConnect was found enabled (a relay-based internet
  exposure path) and Jason disabled it in favor of Tailscale, which he
  confirmed already provides working remote access to the NAS.
- [x] Record the exact server name used by clients and the direct fallback
  URL. — Clients connect to `192.168.20.41` (hostname `GoWest`) over LAN or
  Tailscale; no QuickConnect ID or DDNS hostname in use. Recommend using
  Synology Drive Client's "secure connection" (HTTPS via DSM) option rather
  than plain port 6690 when clients are set up in Milestone 4/5, since only
  the unencrypted sync port was found listening (no 6691).

Completion gate: Drive Server is healthy, private folders and Team Folders are
correct, and no unintended share is exposed. **Reached.**

**Note carried forward:** personal "My Drive" folders have no defined version
retention policy yet (only `Family Documents` does) — worth revisiting once
Jason's photo migration is done, so deleted-file history doesn't accumulate
unbounded going forward. Also worth noting the NAS is dual-homed
(`192.168.20.41` on the documented Servers VLAN 20, plus an undocumented
`192.168.1.41` on `eth1`) — not a problem, just not previously recorded
anywhere.

## 8. Milestone 4 — macOS Finder pilot

- [x] Install the current Synology Drive Client on Jason's Mac mini first.
- [x] Configure On-demand Sync rather than downloading the full dataset. — Sync
  Task set up as Two-way sync with "Enable On-demand Sync to save disk space"
  checked (macOS client's default), pointed at the personal My Drive root
  (`/home/Drive` on the NAS side, `~/SynologyDrive/MyDrive` locally).
- [x] Confirm Synology Drive appears as a Finder location. — Required a
  one-time macOS "Enable" click the first time (File Provider extensions need
  explicit user approval before they'll mount, same as iCloud Drive/OneDrive);
  after that it loaded normally.
- [x] Test online-only files, local download, pinning, edits and conflict
  handling. — Verified: a server-created file appeared as an online-only
  placeholder (cloud icon), downloaded correctly on open, and a local edit
  propagated back to the server. Conflict handling was tested but with a
  caveat: the "server-side" edit was made via a direct SSH file write, which
  bypasses Drive's own change-tracking — the local client's edit silently
  overwrote it rather than producing a conflict copy. This doesn't
  necessarily reflect how two genuine Drive clients would resolve a real
  conflict; a fully clean test would need a second device actually running
  Drive Client. Worth knowing regardless: direct out-of-band edits on the NAS
  (via SSH/scripts) can be silently clobbered by a client's next sync.
- [x] Test sleep, restart, network loss and reconnection. — Jason restarted
  the Mac mini and toggled Wi-Fi off/on; Drive reconnected and resumed
  correctly in both cases.
- [x] Confirm disk-space reclamation does not delete server data. — Used
  Finder's "Free up space" quick action; confirmed via `du`/`stat` that local
  disk blocks dropped to 0 while the file's logical size and Finder listing
  stayed intact, and the server-side copy (with both edits) was fully
  unaffected.
- [ ] Repeat with the laptop only after the Mac mini pilot is stable.
- [x] Document the client setup and removal procedure. — See below.

**Client setup procedure (macOS):**
1. Download Synology Drive Client (4.0.3+) from Synology's Download Center for
   the DS920+, macOS.
2. Install the `.dmg`, launch the app, enter server address `192.168.20.41`
   and sign in with the individual DSM account.
3. Choose **Sync Task** (not Backup Task). On the folder-selection screen,
   click **Advanced → Sync Mode** and confirm **"Enable On-demand Sync to save
   disk space"** is checked, with **Two-way sync** selected.
4. Finish setup, then open Finder → the new location will show "not enabled"
   the first time — click **Enable** to complete macOS's one-time File
   Provider approval.
5. Team Folders (e.g. `Family Documents`) are a separate sync connection, not
   automatically included in the personal My Drive sync task — add them from
   Drive Client's own interface when needed. Confirmed on Jason's Mac mini:
   added a second sync connection for `Family Documents`
   (`~/SynologyDrive/Family`), and a server-created test file appeared there
   as an on-demand placeholder exactly as it did for My Drive.

**Client removal procedure:** Open Synology Drive Client → remove the sync
task from its task list → quit/uninstall the app from Applications. The
on-demand placeholders under `~/Library/CloudStorage/SynologyDrive-*` are
removed by macOS once the File Provider extension is uninstalled; server-side
data is never affected by removing a client.

Completion gate: Finder behaves as a dependable live drive without unnecessary
local duplication, and recovery from disconnects is predictable.

## 9. Milestone 5 — iPhone and iPad pilot

- [ ] Install Synology Drive on one iOS/iPadOS test device.
- [ ] Confirm private files and permitted Team Folders are visible.
- [ ] Test upload, download, edit, offline pinning and resynchronization.
- [ ] Decide whether camera upload belongs in Drive or the existing photo system.
- [ ] If enabled, test duplicate handling, background behaviour and destination
  permissions with a small sample.
- [ ] Test cellular/Tailscale access according to the approved access design.
- [ ] Repeat for other family devices after the pilot passes.

Completion gate: mobile access is understandable, private and recoverable, and
camera upload does not duplicate or conflict with the chosen photo workflow.

## 10. Milestone 6 — Friend sharing and file requests

- [ ] Choose the external-sharing method without broad DSM exposure.
- [ ] Test a password-protected, expiring read-only link with a non-family user.
- [ ] Test a file-request/upload link into a dedicated restricted destination.
- [ ] Confirm recipients cannot browse parent folders or other content.
- [ ] Confirm link revocation takes effect promptly.
- [ ] Establish default expiration, password and data-sensitivity rules.
- [ ] Document auditing and emergency revocation.

Completion gate: a friend can receive or submit a test file through a bounded,
revocable path without obtaining a DSM account or wider NAS access.

## 11. Milestone 7 — Backup and recovery

- [ ] Add required Drive application configuration, databases, user homes and
  Team Folders to Hyper Backup without duplicating unnecessary data.
- [ ] Confirm the backup destination has sufficient free capacity and retention.
- [ ] Run an initial backup and a small incremental backup.
- [ ] Restore an individual file and an earlier version.
- [ ] Restore a deleted file and a representative Team Folder item.
- [ ] Document the supported Drive Server/package recovery order.
- [ ] Confirm encrypted-folder recovery after reboot using protected keys.
- [ ] Record restore timing and evidence without exposing household filenames.

Completion gate: both user-level recovery and package/data recovery are proven
from the protected backup path.

## 12. Milestone 8 — Monitoring, documentation and hand-back

- [ ] Add only actionable service/capacity checks to existing monitoring.
- [ ] Add a Homepage link after the supported access name is stable.
- [ ] Document routine account creation, device replacement and client removal.
- [ ] Document version-retention and capacity-review intervals.
- [ ] Update architecture, addressing, backup and operational documents.
- [ ] Run HomeLab Doctor and a representative client/backup validation.
- [ ] Remove pilot accounts, links and test data that are no longer required.

## 13. Claude execution instructions

- Work one milestone at a time and stop at each completion gate for Jason's
  confirmation.
- Begin with read-only discovery. Do not uninstall packages, delete old Drive
  state, change shared-folder encryption or alter Hyper Backup selections until
  the impact is understood and a recovery checkpoint exists.
- Present commands in large, pasteable blocks where safe, but isolate destructive
  or credential-bearing actions.
- Never request that credentials or encryption keys be pasted into tracked files
  or chat output.
- Preserve the existing backup and NAS services throughout the pilot.
- At hand-back, identify completed checkboxes, evidence, rollback steps, residual
  risks and every repository file changed.

## 14. Definition of done

The project is complete when each family member has private storage, intentional
shared folders work, macOS Finder and mobile clients are stable, friend sharing
is bounded and revocable, encryption limitations are understood, backups and
representative restores pass, monitoring is actionable, and no broad public DSM
exposure was introduced.

## 15. Evidence log

| Date | Milestone | Evidence | Result |
|---|---|---|---|
| 2026-08-24 | Project handover | Requirements separated from initial-build roadmap | Ready |
| 2026-08-25 | Milestone 1 | DSM 7.4.1-90080 (build 90080, GM); SynologyDrive package 4.0.3-27892 (enabled); HyperBackup/HyperBackupVault 4.2.2-4262 (enabled). Main volume (`/volume1`): 11 TB total, 6.8 TB used, 3.7 TB free (65%), RAID5 across 4 disks, all healthy (`[UUUU]`), separate RAID1 system partitions. | Recorded |
| 2026-08-25 | Milestone 1 | Individual DSM accounts already exist for admin, Jason, Alisa, Carter, elliottrook, Jen, Justin, guest, plus a Time Machine Backup service account — no shared admin-account use observed. Drive was previously enabled and used: Jason had an active `Drive` home folder with real content (Synology Office test docs, a large test video since deleted by Jason himself, and an unrelated 247 GB "Windows Back-up" folder). Alisa and Carter have no Drive folder yet; Justin's is already empty. Legacy Drive service folders (`@SynoDrive`, `@synologydrive`, `@SynologyDriveShareSync`) found and left untouched. | Recorded |
| 2026-08-25 | Milestone 1 | Established SSH key-based access to the main Synology (`Jason@192.168.20.41`) for future automation. Root cause of an initial failure: DSM's default ACL grants the `administrators` group write access to every user's home directory, which trips OpenSSH `StrictModes` and silently blocks key auth. Fixed by pointing `AuthorizedKeysFile` at a root-owned path outside the home directory (`/etc/ssh/authorized_keys/%u`) rather than disabling `StrictModes` or altering the ACL. | Done |
| 2026-08-25 | Milestone 1 | Recovery checkpoint for Jason's pre-existing Drive content: moved (not copied) everything except the deleted test video into `/volume1/DriveBackup-20260825/Jason/`, in preparation for a clean-slate Drive folder for Jason, Alisa, Justin and Carter. Move completed and verified: Jason's `Drive` folder is empty, and the backup folder contains the "Windows Back-up" folder plus the `.odoc` files and `.DS_Store`, correctly owned. | Done |
| 2026-08-25 | Milestone 1 | Backup NAS (`192.168.20.42`) discovery: same DSM 7.4.1-90080, model DS220j, 7.3 TB total / 5.9 TB used / 1.4 TB free (82%). Established SSH key access there too, using the same `AuthorizedKeysFile` fix as the main NAS (this box has no home-folder service enabled, which is otherwise unrelated to the SSH fix). Confirmed Synology Drive Client/app compatibility: server package needs Drive Client 4.0.0+ (satisfied), macOS client needs Monterey 12+ (satisfied), and the iOS/iPadOS app now requires iOS 18+ (Synology recently dropped iOS/iPadOS 17 support) — needs confirming against family devices before Milestone 5. | Recorded |
| 2026-08-25 | Milestone 1 | Requirements gathered from Jason: 6 total accounts (Jason, Alisa, Carter, Justin, Jen, elliottrook); non-Jason accounts to be capped at 100 GB each with no planned growth; iPhone client for all six; Mac client for Jason and Alisa; iPad client for Jason. Milestone 1 completion gate reached. | Done |
| 2026-08-25 | Milestone 2 | Confirmed `elliottrook` is administered alongside Jason in the `administrators` group; Jason decided to keep it that way rather than demote it. Set a 100 GB `volume1` quota via DSM's User Quota UI for Alisa, Carter, Justin and Jen (the CLI tool `synoquota` proved unreliable/undocumented for this and was abandoned in favor of the native UI). `elliottrook` could not get a quota through the same UI because it's an admin account — accepted as-is. | Done |
| 2026-08-25 | Milestone 2 | Created DSM group `Family` (Alisa, Carter, Jason, Jen, Justin; `elliottrook` deliberately excluded) and shared folder `Family Documents`. The folder's creation wizard initially granted individual access to `elliottrook`, the built-in `admin` account, and each family member separately rather than through the group; corrected via ACL edit to group-only access, verified via `synoacltool`. | Done |
| 2026-08-25 | Milestone 2 | Home-folder privacy audit (`synoacltool` on the `homes` shared folder and each user's home directory) found a pre-existing gap predating this project: `Alisa` had full read/write and `Justin`/`Jen` had read access to every user's home folder via the `homes` share's own ACL. Creating the `Family` group temporarily compounded this by adding blanket group access. Fixed by stripping all individual-user and group grants from the `homes` shared folder, leaving only `administrators` and per-user ownership. Re-audited twice to confirm the fix actually took (the first pass removed redundant individual entries but left the `Family` group grant in place, which alone still allowed full cross-access). No Synology encryption will be used for this project (Jason's choice). Milestone 2 completion gate reached. | Done |
| 2026-08-26 | Milestone 3 | Enabled `Family Documents` as a Team Folder in Drive Admin Console (verified via `@eaDir` Drive-managed markers); set version retention to 25 max versions / 30-day rotation; decided no file filters or size limits are needed. | Done |
| 2026-08-26 | Milestone 3 | Confirmed Drive's service ports (6690, plus DSM's normal web ports) are bound to all local interfaces with no port-forward changes made by this project. Found QuickConnect enabled (a relay-based internet-exposure path inconsistent with the project's LAN/Tailscale-only rule); Jason confirmed working Tailscale access first, then disabled QuickConnect. Noted the NAS is dual-homed (`192.168.20.41` on Servers VLAN 20, plus an undocumented `192.168.1.41` on `eth1`) — not a problem, just not previously recorded. Clients will connect via `192.168.20.41` over LAN or Tailscale. | Done |
| 2026-08-26 | Milestone 3 | Storage/indexing check found Drive's internal block store (`@synologydrive/@sync`) consuming ~219 GB despite `Family Documents` being empty. Investigation traced this to a few hundred GB of photos currently sitting in Jason's personal My Drive folder — real, current content, not stale data from the earlier cleanup. Jason will migrate these to a dedicated photos app later; recorded as a known, accepted, temporary storage consumer, not a fault. Drive's processes are healthy and running normally. Personal My Drive folders still have no defined version-retention policy (only `Family Documents` does) — worth revisiting after the photo migration. Milestone 3 completion gate reached. | Done |
| 2026-08-26 | Milestone 4 | Installed Synology Drive Client on Jason's Mac mini (this device). On-demand Sync confirmed working end-to-end: server-created files appear as online-only placeholders, download correctly on open, local edits propagate back to the server, and Finder's "Free up space" quick action reclaims local disk blocks (`du`/`stat` confirmed 0 blocks) without ever touching server data. Restart and Wi-Fi toggle resilience confirmed by Jason directly. Conflict-handling test had a caveat: the simulated "server-side" edit was a raw SSH write bypassing Drive's own change tracking, so the local client's edit silently overwrote it rather than producing a true conflict copy — not a clean test of real two-client conflict resolution, but a useful finding that out-of-band NAS edits can be clobbered by client syncs. Added and verified a second sync connection for the `Family Documents` Team Folder on the same Mac, confirming Team Folder sync works identically to personal My Drive. Test files cleaned up from both locations afterward. Still open: repeating the pilot on Jason's laptop. | Done |
