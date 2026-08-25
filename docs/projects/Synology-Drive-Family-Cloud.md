# Synology Drive Family Cloud Project

## Project handover: Claude

> Status: Handover ready; implementation not started
>
> Project owner: Jason
>
> Last updated: 2026-08-24

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

- [ ] Record DSM, Synology Drive Server and Hyper Backup versions.
- [ ] Confirm supported macOS/iOS client versions; use macOS Drive Client 4.1 or
  later where supported.
- [ ] Record current main/backup NAS capacity, snapshots and backup growth.
- [ ] Inventory existing homes, shared folders, permissions and Drive remnants.
- [ ] Confirm whether Drive was previously enabled and identify stale databases,
  clients or Team Folder settings without deleting them.
- [ ] Define expected users, devices, initial data size and five-year growth.
- [ ] Take a current configuration/data recovery checkpoint.

Completion gate: existing state and capacity are documented, and reactivation
will not overwrite or expose existing data.

## 6. Milestone 2 — Identity and folder design

- [ ] Create or verify one non-administrator DSM account per family member.
- [ ] Create family groups and document their intended permissions.
- [ ] Enable user home service and verify private `My Drive` separation.
- [ ] Define the minimum shared family Team Folders and their owners.
- [ ] Decide which shared folder, if any, requires Synology encryption.
- [ ] Record the encryption-key backup and reboot/mount procedure before use.
- [ ] Verify an ordinary family user cannot access DSM administration or another
  person's private files.

Completion gate: the identity and folder model passes least-privilege tests with
representative administrator and family accounts.

## 7. Milestone 3 — Synology Drive Server

- [ ] Install or update Synology Drive Server from Package Center.
- [ ] Enable only the selected Team Folders in Drive Admin Console.
- [ ] Set conservative version retention based on capacity and recovery goals.
- [ ] Configure file filters and size limits only where justified.
- [ ] Confirm indexing/database health and expected storage consumption.
- [ ] Confirm Drive service ports and firewall access remain private and scoped.
- [ ] Record the exact server name used by clients and the direct fallback URL.

Completion gate: Drive Server is healthy, private folders and Team Folders are
correct, and no unintended share is exposed.

## 8. Milestone 4 — macOS Finder pilot

- [ ] Install the current Synology Drive Client on Jason's Mac mini first.
- [ ] Configure On-demand Sync rather than downloading the full dataset.
- [ ] Confirm Synology Drive appears as a Finder location.
- [ ] Test online-only files, local download, pinning, edits and conflict handling.
- [ ] Test sleep, restart, network loss and reconnection.
- [ ] Confirm disk-space reclamation does not delete server data.
- [ ] Repeat with the laptop only after the Mac mini pilot is stable.
- [ ] Document the client setup and removal procedure.

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
