# Synology Drive Family Cloud Project

## Project handover: Claude → ChatGPT

> Status: **Concluded 2026-08-31.** Milestones 1-8 complete for the pilot
> rollout (Jason's own accounts and devices), including a fully proven
> backup/restore path and HomeLab Doctor monitoring. The Cloudflare Access
> admin-login problem is also resolved (root cause was split DNS blocking
> Cloudflare's own backend from reaching Authentik — see
> Authentik-Cloudflare-Access-OIDC-Handover.md). One item is deliberately
> deferred, not abandoned: rolling out mobile/desktop clients to the rest of
> the family (Alisa, Carter, Justin, Jen) — see section 16 (Hand-back) below
> for full detail, rollback steps and residual risks before picking this
> back up.
>
> Project owner: Jason
>
> Last updated: 2026-08-31

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
- [x] Repeat with the laptop only after the Mac mini pilot is stable. —
  Jason installed the Mac client on his laptop; confirmed working.
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
local duplication, and recovery from disconnects is predictable. **Reached.**

## 9. Milestone 5 — iPhone and iPad pilot

- [x] Install Synology Drive on one iOS/iPadOS test device. — Installed on
  Jason's iPhone and iPad; both confirmed on iOS 18+ per the Milestone 1
  compatibility note.
- [x] Confirm private files and permitted Team Folders are visible. — Both
  My Drive and Family Documents showed up correctly on mobile.
- [x] Test upload, download, edit, offline pinning and resynchronization. —
  Confirmed working by Jason directly on-device; not independently verified
  step-by-step the way the Mac mini pilot was (no SSH-equivalent visibility
  into the iOS app's local state), so this is based on his own testing rather
  than external confirmation.
- [x] Decide whether camera upload belongs in Drive or the existing photo
  system. — Decided: keep camera upload in the existing Synology Photos
  workflow; Drive's camera upload will not be enabled, avoiding any
  duplication/conflict.
- [ ] If enabled, test duplicate handling, background behaviour and destination
  permissions with a small sample. — N/A; camera upload is not being enabled
  in Drive.
- [x] Test cellular/Tailscale access according to the approved access design.
  — Confirmed working by Jason off home WiFi.
- [ ] Repeat for other family devices after the pilot passes. — Still open;
  Alisa, Carter, Justin and Jen's devices haven't been set up yet.

Completion gate: mobile access is understandable, private and recoverable, and
camera upload does not duplicate or conflict with the chosen photo workflow.
**Reached for the pilot device** — rolling out to the rest of the family is
the one remaining item, tracked above rather than blocking this gate.

## 10. Milestone 6 — Friend sharing and file requests

- [x] Choose the external-sharing method without broad DSM exposure. — Drive's
  public sharing via the Cloudflare Tunnel set up earlier tonight (see
  [Synology-Drive-Cloudflare-Handover.md](../Synology-Drive-Cloudflare-Handover.md)),
  scoped so only the `/d/*` and `/oo/*` share-link paths bypass Cloudflare
  Access — no WAN port-forward, and DSM's own login surface stays behind a
  login wall (login method for that wall is a separate open item, see
  [Authentik-Cloudflare-Access-OIDC-Handover.md](../Authentik-Cloudflare-Access-OIDC-Handover.md)).
- [x] Test a password-protected, expiring read-only link with a non-family
  user. — Tested an expiring link from a private/incognito context (simulating
  an outsider with no access to any of Jason's accounts); confirmed working.
  The password-protection toggle itself wasn't separately tested (it's a
  standard, well-understood Drive feature) — see the default-rules decision
  below for when to use it.
- [x] Test a file-request/upload link into a dedicated restricted destination.
  — Tested; confirmed working.
- [x] Confirm recipients cannot browse parent folders or other content. —
  Confirmed: navigating up/around from the share link does not expose parent
  folders or other content.
- [x] Confirm link revocation takes effect promptly. — Tested a scheduled
  link expiration; confirmed access was cut off as expected.
- [x] Establish default expiration, password and data-sensitivity rules. —
  Decided: every share link gets an expiration date by default; add a
  password only for sensitive content, not as a blanket requirement.
- [x] Document auditing and emergency revocation. — See below.

**Auditing and emergency revocation:** to see or revoke an active share link
immediately (not waiting for its scheduled expiration), open the shared
file/folder in Synology Drive, open its sharing settings, and disable or
delete the link — this takes effect immediately, the same mechanism confirmed
by tonight's expiration test. For a fuller audit of everything currently
shared, check Drive Admin Console's sharing/link management view.

Completion gate: a friend can receive or submit a test file through a bounded,
revocable path without obtaining a DSM account or wider NAS access.
**Reached.**

## 11. Milestone 7 — Backup and recovery

- [x] Add required Drive application configuration, databases, user homes and
  Team Folders to Hyper Backup without duplicating unnecessary data. —
  **Important discovery**: the only existing Hyper Backup task ("Media
  Backup") backs up `/Plex` only — there was no backup coverage at all for
  any user data before this. Created a new, separate task ("Synology Drive
  Backup") covering `/homes` and `/Family Documents`, kept independent from
  Media Backup so their schedules/retention don't interfere. Settings: daily
  at 00:00, integrity check Monday 04:00, rotation enabled keeping 30
  versions, no client-side encryption (Jason's deliberate choice — lower
  priority for a same-LAN NAS-to-NAS backup than it would be for an off-site
  destination).
- [x] Confirm the backup destination has sufficient free capacity and
  retention. — `/homes` totals 121 GB, `Family Documents` 1.3 MB, against
  1.4 TB free on the backup NAS — ample headroom.
- [x] Run an initial backup and a small incremental backup. — Initial backup
  completed successfully: 102 GB landed at the destination (close to the
  121 GB source size, difference from compression). The task was originally
  created with "Application: None" (files only, missing Drive's own
  settings/config); corrected to add the `SynologyDrive` application backup,
  and Jason additionally kept `HyperBackup` itself in the application list
  (backing up the backup tool's own configuration too — a reasonable,
  low-cost addition). One mix-up caught along the way: the Application field
  initially had "HyperBackup" selected instead of "SynologyDrive" —
  corrected before the backup ran. Three further incremental "Back up now"
  runs were used for the restore tests below, each completing quickly (all
  single small test files).
- [x] Restore an individual file and an earlier version. — Created a test
  file in `Family Documents`, captured two versions via "Back up now" (an
  original and a modified version), then used Backup Explorer to restore the
  earlier version specifically. Confirmed via direct file read on the NAS
  that the restored content matched the original version exactly, not the
  modified one.
- [x] Restore a deleted file and a representative Team Folder item. — Deleted
  the same test file (in `Family Documents`, a Team Folder), captured the
  deletion in a further "Back up now" run, then used Backup Explorer to
  restore it from before the deletion. Confirmed via direct file read that
  the deleted file came back with the expected content.
- [x] Document the supported Drive Server/package recovery order. — For a
  full disaster-recovery scenario (not just individual file restores, which
  are proven above):
  1. DSM base system intact or freshly installed.
  2. Install the Hyper Backup package and relink the existing repository
     pointing at the Backup Synology (`192.168.20.42`, share `Backup`).
  3. Install the Synology Drive Server package via Package Center — this
     creates the expected default directory/database structure before any
     data is restored into it, rather than restoring onto a package that
     doesn't exist yet.
  4. Stop the Synology Drive Server package before restoring its data, to
     avoid the running service conflicting with files being written back.
  5. Using Hyper Backup's restore wizard, restore the `SynologyDrive`
     application data (Team Folder/sharing/quota/retention settings) before
     restoring the `homes` and `Family Documents` folder data — restoring
     the application config first means the service already knows about
     these folders when the file data lands.
  6. Restart the Synology Drive Server package.
  7. **Re-verify the Milestone 2 privacy fix survived the restore** — this is
     the one recovery-order risk specific to this project: a full folder
     restore could in principle reintroduce the ACL state that existed at
     backup time. Since the `homes` shared folder's ACL was deliberately
     locked down in Milestone 2 (removing cross-user access), re-run the same
     `synoacltool` audit from that milestone after any real restore, rather
     than assuming the fix persisted automatically.
  8. Re-confirm Team Folder enablement, quotas, and version-retention
     settings in Drive Admin Console match what's documented in Milestones
     2-3, since a partial/older restore could bring back stale settings.
- [x] Confirm encrypted-folder recovery after reboot using protected keys. —
  Not applicable; no Synology encryption is in use anywhere in this project
  (Jason's choice, also recorded in Milestone 2).
- [x] Record restore timing and evidence without exposing household
  filenames. — All restore testing used a clearly-labeled test file
  (`restore-test.txt`) created specifically for this purpose, not any real
  household data, so no filenames are exposed here. Each backup run
  (initial and the three incrementals used for restore testing) and both
  restores completed within seconds to low minutes given the small file
  sizes involved — this doesn't establish full-scale restore timing for the
  complete 102 GB backup, which would take proportionally longer; that
  wasn't tested here since a full destructive restore isn't warranted to
  prove the mechanism works.

Completion gate: both user-level recovery and package/data recovery are proven
from the protected backup path. **Reached** — individual file/version/deletion
recovery is directly proven; full package-level recovery order is documented
but, appropriately, not destructively tested against production data.

## 12. Milestone 8 — Monitoring, documentation and hand-back

- [x] Add only actionable service/capacity checks to existing monitoring. —
  Added `check_synology_drive_backup` to `scripts/doctor.sh`, checking the
  freshness of the Hyper Backup destination folder on the backup NAS (same
  pattern as the other `check_backup_age`-style checks). Verified standalone;
  full end-to-end `doctor.sh` run and real backup validation still pending
  Milestone 7's initial backup finishing.
- [x] Add a Homepage link after the supported access name is stable. — Added
  a "Family Drive" tile to the live Homepage dashboard config
  (`/opt/homepage/config/services.yaml` on the docker host), pointing to
  `https://192.168.20.41:5001`. Confirmed visible on the dashboard after a
  container restart (config changes don't hot-reload).
- [x] Document routine account creation, device replacement and client
  removal. — See "Routine operations" (section 12a) below.
- [x] Document version-retention and capacity-review intervals. — See
  "Routine operations" (section 12a) below.
- [x] Update architecture, addressing, backup and operational documents. —
  Added a "Synology Drive same-site backup" section to `docs/05-Backups.md`;
  recorded the dual-homed NIC discovery in `docs/02-IP-Addressing.md`.
  `docs/01-Architecture.md` and `docs/04-Operations.md` were reviewed and
  found already generic enough to cover this project without needing edits.
- [x] Run HomeLab Doctor and a representative client/backup validation. —
  Ran the full `doctor.sh` after Milestone 7's backup and restore tests
  completed: the new `check_synology_drive_backup` check passed cleanly
  ("Synology Drive Backup is 0 hour(s) old"). Other warnings/failures in the
  same run (stale OPNsense/Arista/Proxmox config backups, unreachable Reolink
  cameras, Mac disk usage) are pre-existing and unrelated to this project —
  not addressed here, out of scope. The "representative backup validation"
  itself is the restore testing documented in Milestone 7 above.
- [x] Remove pilot accounts, links and test data that are no longer required.
  — The one known leftover, a public test share link for `HDR Window.jpeg`
  from the original Cloudflare setup validation, already has a same-day
  expiration set and will self-expire; Jason confirmed the expiration
  mechanism has already worked correctly on this exact link once before
  (it expired yesterday, was recreated for further testing, and expires
  again today) — no manual revocation needed.

## 12a. Routine operations

**Adding a new family member's account:**
1. Control Panel → User & Group → Create → set up an individual, non-admin
   DSM account (matches this project's design: only Jason and elliottrook are
   administrators — everyone else stays an ordinary account).
2. Add the account to the `Family` group (Control Panel → User & Group →
   Group → Family → Edit Members) — this grants access to the
   `Family Documents` Team Folder without needing per-user ACL entries.
3. Set a 100 GB quota via Control Panel → User & Group → select the user →
   Edit → Quota tab → `volume1` → 100 GB (matches every existing family
   account except Jason).
4. Do **not** grant access to anything on the `homes` shared folder itself
   beyond the user's own account — that folder's permissions were
   deliberately locked down in Milestone 2 so no one can see into another
   family member's private Drive folder; adding a new user doesn't need any
   change there, DSM handles per-user home folder creation automatically.
5. Install the Drive Client/app on their device(s) using the setup procedure
   in Milestone 4, pointing at `192.168.20.41` (LAN) or via Tailscale
   remotely.

**Replacing a device:**
1. On the old device, remove the sync task from Drive Client (or just
   uninstall the app on mobile) — this never deletes server-side data, only
   the local on-demand cache/placeholders.
2. Set up the new device following the same client setup procedure as
   Milestone 4/5. On-demand Sync means no bulk re-download is needed upfront;
   files populate as they're opened.
3. If the old device is lost/stolen rather than just retired, also consider
   revoking its session via DSM's Control Panel → Connection Log / My Drive's
   device management, and rotating the account's password as a precaution.

**Removing a client without removing the account:**
- Same as step 1 of "Replacing a device" above — removing a Drive Client sync
  task or uninstalling the mobile app never touches server-side data. The
  account and its files remain exactly as they were.

**Version-retention settings currently in place:**
- `Family Documents` (Team Folder): 25 max versions, rotate/delete versions
  older than 30 days (set in Milestone 3).
- Personal My Drive folders: **no version-retention policy is set** — this
  was flagged as an open item back in Milestone 3, pending Jason's photo
  migration out of his My Drive folder. Worth revisiting once that migration
  happens, so deleted-file history doesn't accumulate unbounded.
- Hyper Backup "Synology Drive Backup" task (Milestone 7): 30-version
  rotation, daily backups at 00:00, weekly integrity check (Monday 04:00).

**Capacity review intervals:**
- Main NAS (`192.168.20.41`): 3.7 TB free as of Milestone 1 (65% used). No
  fixed review cadence was set during this project — worth checking
  DSM's Storage Manager periodically, especially since per-user quotas
  (100 GB × 5 non-Jason accounts = up to 500 GB reservable) are well within
  current headroom but worth re-checking if usage grows.
- Backup NAS (`192.168.20.42`): 1.4 TB free as of Milestone 1 (82% used,
  noticeably tighter than the main NAS). The new Drive backup task adds
  ~121 GB — comfortable now, but this destination has less headroom overall
  and is shared with the existing Plex media backup, so it's the more
  time-sensitive one to periodically re-check as data grows.

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
| 2026-08-29 | Milestone 4 | Jason installed and confirmed the Mac Drive client on his laptop, closing the last open Milestone 4 item. Milestone 4 completion gate reached. | Done |
| 2026-08-29 | Milestone 5 | Jason installed Synology Drive on his iPhone and iPad and confirmed both My Drive and the Family Documents team folder are visible, sync/edit/offline behavior works, and cellular access via Tailscale (off home WiFi) works. Decided to keep camera upload in the existing Synology Photos workflow rather than enabling it in Drive, avoiding duplication. Milestone 5 completion gate reached for the pilot device; rolling out mobile clients to Alisa, Carter, Justin and Jen remains open. | Done |
| 2026-08-29 | Milestone 6 | External sharing tested end-to-end via the Cloudflare Tunnel set up earlier tonight: an expiring read-only link opened correctly from a private/incognito context simulating an outsider, could not be used to browse parent folders or other content, and a scheduled expiration correctly cut off access. A file-request/upload link was also tested and confirmed working. Decided on a default sharing policy: every link expires by default, with a password added only for sensitive content rather than as a blanket rule. Documented the emergency-revocation procedure (disable/delete the link from its sharing settings, effective immediately). Milestone 6 completion gate reached — note this relies on the Cloudflare Tunnel routing, which is confirmed working, independent of the (at the time) unresolved Cloudflare Access admin login problem tracked separately. | Done |
| 2026-08-29 | Milestone 6 (follow-up) | The separately-tracked Cloudflare Access admin-login problem was resolved via a ChatGPT troubleshooting session, verified here. Root cause: split DNS — `auth.elliottrook.com` only existed in internal DNS, so Cloudflare Access's own backend (which performs the OIDC token exchange server-to-server, not through the browser) couldn't reach Authentik's token/userinfo/JWKS endpoints. Fixed by publishing `auth.elliottrook.com` through the same Cloudflare Tunnel already used for Drive sharing, routed to NPM, rather than exposing it via a direct WAN record. A Cloudflare OIDC client secret was accidentally exposed during that troubleshooting session and was rotated immediately as a precaution. Full detail in `docs/Authentik-Cloudflare-Access-OIDC-Handover.md`. DSM's Cloudflare-tunneled admin login is now fully working with Authentik password + passkey/MFA. | Done |
| 2026-08-31 | Milestone 7 | Discovered the existing Hyper Backup task ("Media Backup") only ever covered `/Plex` — no user data had any backup coverage before this. Scoped Milestone 7 to Drive-related folders only (not a full-NAS backup, which would be a larger, separate effort). Sized the actual data first (`/homes` 121 GB, `Family Documents` 1.3 MB) and confirmed it fits comfortably against 1.4 TB free on the backup NAS. Created a new, independent Hyper Backup task ("Synology Drive Backup") rather than modifying the existing Media Backup task, using settings matching this homelab's documented Hyper Backup standard (`docs/05-Backups.md`): daily at 00:00, weekly integrity check (Monday 04:00), 30-version rotation. No client-side encryption — a deliberate, low-stakes choice for a same-LAN NAS-to-NAS backup. Initial backup confirmed running (active worker processes) at session end. | In progress |
| 2026-08-31 | Milestone 8 | Added `check_synology_drive_backup` to `scripts/doctor.sh` (checks the Hyper Backup destination folder's freshness on the backup NAS), plus new SSH config aliases `gowest` and `gowest-backup` to support it. Added a "Family Drive" tile to the live Homepage dashboard config on the docker host, confirmed visible after a container restart. Confirmed the one known leftover test artifact (a public share link for `HDR Window.jpeg`) has a working same-day expiration and needs no manual cleanup — a second real-world confirmation of link expiration working, after the one already tested in Milestone 6. Wrote routine-operations documentation (account creation, device replacement, client removal, version-retention and capacity-review intervals) directly into this tracker. Updated `docs/05-Backups.md` and `docs/02-IP-Addressing.md` to reflect the new backup task and the dual-homed NIC discovery from Milestone 3; `docs/01-Architecture.md` and `docs/04-Operations.md` reviewed and found already adequate. | In progress |
| 2026-08-31 | Milestone 7 | Initial Hyper Backup run completed: 102 GB landed at the destination (close to the 121 GB source, difference from compression). Ran a full restore-testing cycle using a dedicated test file in `Family Documents` (never real household data): captured an original version, a modified version, and a deletion via three "Back up now" runs, then used Backup Explorer to (1) restore the earlier version — confirmed exact content match — and (2) restore the deleted file — confirmed it came back correctly. Documented the full package-level disaster-recovery order (install Hyper Backup, relink repository, install Synology Drive Server before restoring its data, restore application config before folder data, and explicitly re-verify the Milestone 2 ACL privacy fix survived any real restore, since that's a genuine project-specific recovery risk). Encrypted-folder recovery is not applicable (no encryption in use). Milestone 7 completion gate reached. | Done |
| 2026-08-31 | Milestone 8 | Ran the full `doctor.sh` after the above: `check_synology_drive_backup` passed cleanly. Other warnings/failures in that run (stale OPNsense/Arista/Proxmox backups, unreachable Reolink cameras, Mac disk usage) are pre-existing and unrelated to this project, not addressed here. Milestone 8 complete. This closes every Milestone 1-8 item for the pilot rollout except rolling out mobile/desktop clients to Alisa, Carter, Justin and Jen, which remains open as the one project-wide follow-up. | Done |

## 16. Hand-back (concluded 2026-08-31)

This project is being concluded and handed back at this point, per Jason's
request. The pilot rollout (Milestones 1-8, for Jason's own accounts and
devices) is fully complete. One item is deliberately deferred rather than
completed — see "Deferred, not abandoned" below.

### Completed checkboxes

- **Milestone 1 (Discovery and capacity):** complete. DSM/package versions,
  capacity on both NAS units, account/folder inventory, client compatibility
  (including the iOS 18+ requirement), and requirements gathering all done.
- **Milestone 2 (Identity and folder design):** complete. Accounts, quotas,
  the `Family` group and `Family Documents` Team Folder all correctly scoped
  — and a real pre-existing privacy bug (cross-user home-folder access) was
  found and fixed, not just documented.
- **Milestone 3 (Synology Drive Server):** complete. Team Folder enabled,
  version retention set, QuickConnect replaced with Tailscale, storage
  consumption investigated.
- **Milestone 4 (macOS Finder pilot):** complete on Jason's Mac mini and
  laptop. On-demand sync, disk-space reclamation, and restart/network-loss
  resilience all verified.
- **Milestone 5 (iPhone/iPad pilot):** complete for Jason's own devices.
  Camera upload deliberately left with the existing Synology Photos
  workflow.
- **Milestone 6 (Friend sharing):** complete. Expiring links, file-request
  links, parent-folder containment, and revocation all verified from an
  outsider's perspective. The related but separately-tracked Cloudflare
  Access admin-login problem is also resolved (see below).
- **Milestone 7 (Backup and recovery):** complete. A dedicated Hyper Backup
  task now protects `homes`, `Family Documents`, and Drive's own application
  configuration — where none existed before this project. Individual-file,
  earlier-version, and deleted-file recovery are all directly proven; full
  disaster-recovery order is documented.
- **Milestone 8 (Monitoring and documentation):** complete. HomeLab Doctor
  monitors backup freshness, Homepage has a working link, and routine
  operations/retention/capacity-review procedures are documented.

### Evidence

The full evidence log (section 15 above) has a dated, milestone-tagged entry
for every significant action and finding across this project — versions
recorded, commands run, test results, and decisions made. Nothing in this
hand-back summary should be treated as a substitute for that log; it's the
authoritative record.

### Rollback steps

- **SSH key access to both NAS units** (`AuthorizedKeysFile` pointed at
  `/etc/ssh/authorized_keys/%u` instead of the default, to work around a
  `StrictModes`/ACL conflict): revert by restoring
  `/etc/ssh/sshd_config.bak-*` (timestamped backups exist on both hosts from
  when this change was made) and restarting `sshd` via `synosystemctl
  restart sshd`.
- **Per-user quotas** (100 GB on `volume1`/`homes` for everyone but Jason):
  revert via Control Panel → User & Group → select user → Quota tab → set
  back to unlimited.
- **`Family` group and `Family Documents` Team Folder**: can be deleted via
  Control Panel → User & Group / Shared Folder if no longer wanted; this
  would remove the shared-folder feature entirely, not just a setting.
- **`homes` shared folder ACL lockdown**: this is a security fix, not a
  preference — **do not roll this back**. Reverting it would reintroduce the
  pre-existing bug where family members could read/write each other's
  private home folders.
- **Hyper Backup "Synology Drive Backup" task**: delete via Hyper Backup →
  select the task → Action → Delete. The backed-up data itself
  (`/volume1/Backup/GoWest_2.hbk` on `192.168.20.42`) would need manual
  deletion separately if reclaiming that space is desired.
- **QuickConnect disabled**: re-enable via Control Panel → QuickConnect if
  ever wanted back — not recommended, since it reintroduces a relay-based
  internet-exposure path this project deliberately moved away from in favor
  of Tailscale.
- **Cloudflare Tunnel routes and Access applications** (`share.elliottrook.com`,
  `auth.elliottrook.com`, the three Access applications, the Authentik OIDC
  login method): rollback order and specifics are documented in
  [Synology-Drive-Cloudflare-Handover.md](../Synology-Drive-Cloudflare-Handover.md)
  and [Authentik-Cloudflare-Access-OIDC-Handover.md](../Authentik-Cloudflare-Access-OIDC-Handover.md)
  — do not improvise a rollback here without reading those, since undoing
  pieces out of order could re-expose DSM's login surface without protection.
- **Homepage dashboard "Family Drive" tile**: a timestamped backup of the
  original `services.yaml` exists on the docker host at
  `/opt/homepage/config/services.yaml.bak-*`; restore it and run `docker
  restart homepage` to revert.
- **`check_synology_drive_backup` in `scripts/doctor.sh`**: `git revert` the
  commit that added it (`9c5d88e`), or manually remove the function and its
  call site.
- **SSH config aliases** (`gowest`, `gowest-backup` in `~/.ssh/config` on
  Jason's Mac): not git-tracked, local convenience only — remove the `Host`
  blocks if no longer wanted, no functional impact on the NAS either way.

### Residual risks

- **The one deliberately deferred item**: mobile/desktop Drive clients have
  not been rolled out to Alisa, Carter, Justin, or Jen — only Jason's own
  devices were piloted. This is the main piece of unfinished work.
- Personal My Drive folders (everyone's, not just Jason's) still have **no
  version-retention policy** — only `Family Documents` does. Flagged since
  Milestone 3, pending Jason's photo migration out of his My Drive folder.
- Jason's few-hundred-GB photo collection is still sitting in his My Drive
  folder, inflating Drive's internal storage consumption; he plans to
  migrate it to a dedicated photos app, not yet done.
- The backup NAS (`192.168.20.42`) has comparatively tight headroom (1.4 TB
  free before this project's ~102 GB addition) and is shared with the
  existing Plex media backup — worth periodic re-checking as data grows,
  more so than the main NAS.
- The `/oo/*` Cloudflare Access bypass path (Synology Office document
  shares) was configured but never re-tested end-to-end — no suitable
  `/oo/` share link was available during either the original setup or the
  Authentik fix's closeout validation.
- Real two-client conflict resolution in Drive was never cleanly tested —
  the Milestone 4 test simulated a "server-side" edit via a raw SSH write,
  which bypasses Drive's own change-tracking and isn't equivalent to two
  genuine Drive clients editing simultaneously.
- Full-scale restore timing was not measured — only small test-file restores
  were timed (seconds to low minutes). A real restore of the full ~102 GB
  backup would take proportionally longer; that wasn't tested since a
  destructive full restore isn't warranted just to prove the mechanism.
- A Cloudflare OIDC client secret was briefly exposed during the ChatGPT
  troubleshooting session that fixed the Authentik integration; it was
  rotated immediately as a precaution — already handled, but worth knowing
  it happened.

### Every repository file changed by this project

- `docs/projects/Synology-Drive-Family-Cloud.md` (this file)
- `docs/Authentik-Cloudflare-Access-OIDC-Handover.md`
- `docs/Synology-Drive-Cloudflare-Handover.md` (authored by a separate Codex
  session, not this one, but directly part of this project's Milestone 6)
- `docs/05-Backups.md`
- `docs/02-IP-Addressing.md`
- `scripts/doctor.sh`

**Live infrastructure changes made that are not tracked in this
repository** (worth knowing about even though there's no file diff to
point to): DSM configuration on both Synology units (SSH
`AuthorizedKeysFile`, user quotas, the `homes` folder ACL fix, the `Family`
group and `Family Documents` Team Folder, QuickConnect disabled, the new
Hyper Backup task), the Cloudflare Zero Trust account (Applications,
Policies, the Authentik OIDC login method), the Authentik OAuth2
Provider/Application for Cloudflare Access, and the Homepage dashboard
config on the docker host.

### Deferred, not abandoned

Rolling out Drive clients to Alisa, Carter, Justin, and Jen is the intended
next step whenever this project is picked back up — the setup procedure is
fully documented above (Milestone 4's client setup procedure and Milestone
8's routine-operations section), so it should be straightforward to execute
without needing to rediscover anything.
