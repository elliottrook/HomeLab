# Brand Asset Library — Forgejo migration

Owner: Jason. Started 2026-11-06. Status: staged, awaiting authenticated repository
creation and import/backup verification. Stream M; bounded private migration,
network backup and HomeLab main linkage requested by Jason with instruction to
proceed. No general infrastructure administration or public publication granted.

## Purpose and scope

Make all four existing brand libraries accessible to authorized agents through
private Forgejo, preserving all originals, variants, approvals and work records.
Link the library from HomeLab main; retain and verify network recovery coverage.
No art redesign, approval promotion, source deletion, new public exposure, new
offsite transmission, firewall change or direct GitHub asset push is in scope.
This project produces no speech and requires no new UI design.

## Evidence and authority

See the [shared-library entry point](../standards/brand-design/BRAND-ASSET-LIBRARY.md)
for proposed destination, exact storage paths, bootstrap and verified backup
baseline. Source authority remains the owner's Documents Brand Asset Library until
import, independent retrieval and post-import network recovery gates pass. The
asset repository will own brand state; HomeLab owns reusable standards and links.

## Risk assessment and integrations

- Confidentiality: keep repository private and avoid artwork mirroring to GitHub;
  authenticated clone rights/network reachability remain required per agent.
- Integrity: SHA-256 inventory every source/copy, preserve approval status and
  original local library, and verify independent retrieval including LFS.
- Availability/capacity: about 4.36 GB logical source; recheck free space and avoid
  unnecessary staging copies on the 24 GB Forgejo guest. No service restart needed.
- Recovery: retain source, use existing LXC 108 backup and independent TrueNAS copy;
  require a post-import archive and isolated Git/LFS recovery before graduation.
- Dependencies: Git LFS supported by Forgejo; the Mac needed a task-local client.
  Some source files have macOS `dataless` flags and require hydration to read.
- Authentication: automatic review rejected a keychain credential probe; do not
  work around the rejection. Use owner-authenticated browser session or separately
  approved credential handling. No new credentials or access rules planned.
- Monitoring/NetBox/Beszel: no new host/service; existing Forgejo guest and backup
  monitoring remain relevant. Check their coverage/freshness before graduation;
  no duplicate monitor or inventory object is proposed.
- Backup schedules, retention, offsite scope, wiki/mirror publication and user
  credentials are not modified incidentally. Any required expansion needs review.

## Milestones and persistence

- [x] Read canonical process/storage guidance; inspect source registry and live
  Forgejo/LFS/storage plus Proxmox and TrueNAS backup baseline.
- [ ] Finish complete hash-verified source copy and review import scan alerts.
- [ ] Create private asset repository and import with LFS; verify remote main.
- [ ] Independently clone/pull LFS; compare inventory and approved-master hashes.
- [ ] Verify post-import independent network backup and isolated restore.
- [ ] Publish HomeLab main link and confirm automatic GitHub documentation mirror.
- [ ] Update installed skill storage guidance after canonical destination validates.
- [ ] Owner handover, intent/efficiency review and close-out evidence.

On resumption, read the workspace `brand-assets-forgejo/HANDOVER.md` and
`source-inventory.json` if complete; inspect actual refs and file hashes before
continuing. Do not mistake partial copied files or a prepared document for deployment.

## Validation, maintenance and rollback

Verify all source hashes, LFS objects, four brands' sample SVG/PNG/ZIP renders,
approved-master records, fresh independent clone and network backup restoration.
The import scanner is a limited high-confidence check, not an exhaustive security
or licensing audit. Do not bless pre-existing hash drift during migration.
Review clone size, per-brand selective retrieval and backup growth to avoid
unnecessary operational cost. Retain local originals; if shared retrieval fails,
keep local authority and revert guidance by ordinary commit, never force-push.
Do not replace a production guest during a restore test.

## Evidence log and close-out

2026-11-06: Forgejo 15.0.7 active, LFS enabled, repositories/LFS inside root disk.
Proxmox all-guest backup enabled; latest LXC 108 archive present independently on
TrueNAS, pull task 1 SUCCESS. No post-import protection or migration completion
claimed. Asset/import commit, HomeLab link commit, independent clone checks,
post-import backup and restore evidence remain to be recorded.
