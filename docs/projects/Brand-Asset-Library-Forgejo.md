# Brand Asset Library — Forgejo migration

Owner: Jason. Started/completed: 2026-11-06. Status: complete.
Stream M, bounded owner-approved migration, network backup and HomeLab main linkage.

## 1. Purpose and outcome

All four registered brand libraries now live together in the separate private
Forgejo repository jason/brand-assets, branch main. HomeLab main links the library
and reusable workflow. Original artwork, extra variants and approval states are
preserved, with verified independent network recovery.

## 2. Current state and evidence

Asset commit: 2bdb72732f67e117da6be34da914f16f043e2dce.
Import: 2,591 original files / 4,363,230,287 bytes, plus portable guides/helpers.
Source inventory SHA-256:
ccf058956f206d9438701529e601c8e21f60e7af7cf5fdfe6af442e6f5c7d41b.
Only seven .DS_Store files were excluded and recorded. Original root AGENTS.md
is retained byte-for-byte under migration/original-root/AGENTS.md.

## 3. Scope and exclusions

Migrated Aster Home, fotosforfun, The Contrasting Frame and The Closet Fatman.
No logo redesign, approval promotion, font installation, site/app deployment,
public artwork publication, direct GitHub artwork push or original-library deletion.
No new host, ingress, account, firewall rule or offsite configuration.

## 4. Authority model

Private asset-repository main owns brand state and artwork. HomeLab owns reusable
standards/templates and the [shared-library entry point](../standards/brand-design/BRAND-ASSET-LIBRARY.md).
Each brand's metadata and approval records own its current design/release.
The Documents library is retained as an unchanged reference/recovery copy.

## 5. Architecture and data flow

Authorized agent checkout → private Forgejo Git/LFS → existing Proxmox whole-guest
backup → independent TrueNAS guest-archive pull. Registry paths remain relative.
Git LFS holds large artwork, fonts and archives; tiny signature glyph sources
remain ordinary Git text. No push mirror is configured for the artwork repository.

## 6. Privacy and security

Private repository/owner/default branch were verified. Access still requires
authorized credentials and a reachable network path. A saved-keychain probe was
rejected and not executed; owner-authenticated browser creation and normal
SSH-authenticated LFS provided the safe route. No credentials were added by the
migration. Limited text/archive-name scanning returned no alerts; this was not
exhaustive secret detection, public-rights or licensing clearance.

## 7. Risks and controls

SHA-256 inventory, immutable originals, preserved master hashes and isolated
recovery protect integrity. FileProvider/iCloud cache reads caused local timeouts;
the completed working checkout is outside iCloud and a fresh full LFS download
passed. Git LFS 3.8.1 official macOS ARM64 ZIP SHA-256 matched
0ba10e897e0496412cd86eacaed4ed554c97ddc29bc5c709d28faa5eaaa2222c;
normal macOS signature verification passed without weakening security settings.

## 8. Persistence and resume

Read the library's AGENTS.md, START-HERE.md, registry.json and
[agent handover](https://git.elliottrook.com/jason/brand-assets/src/branch/main/AGENT-HANDOVER.md).
Use a per-agent checkout root, its bundled resolver or explicit --root.
This Mac's installed skill points to /Users/jasonelliott/brand-assets.
Historical absolute build/preview paths may need root configuration.

## 9. Milestones

- [x] Resolve source, storage rules, privacy and recovery baseline.
- [x] Preserve and hash-verify all originals and approval records.
- [x] Create private repository and publish full Git/LFS import.
- [x] Independently clone published Git and verify every original through LFS.
- [x] Fetch all LFS objects with a normal client; Git LFS fsck passed.
- [x] Create post-import backup, copy to TrueNAS and verify isolated recovery.
- [x] Publish HomeLab main entry point; retain its normal documentation mirror.
- [x] Install/test portable skill lookup and independent Mac checkout.
- [x] Provide and walk through the agent handover.

## 10. Validation and efficiency review

Independent published clone and recovered backup each matched every source file:
1,895 LFS file occurrences / 1,574 unique LFS objects, plus 696 ordinary Git
originals, zero failures. All 115 recorded approved-master hashes matched.
Aster's zero recorded current masters/current release unset state was preserved.
Fresh client retrieval and native Git LFS fsck passed; recovered Git fsck passed.
The local working tree was clean and its original-file verifier passed all 2,591.

Deduplication avoids repeating identical LFS bodies; small glyphs use ordinary Git.
Artwork does not inflate HomeLab or its GitHub mirror. The chosen storage/root
fix avoids iCloud dependency. No temporary access grant or network-policy expansion
was needed. Backup retention and existing monitoring remain in place.

## 11. Observability and maintenance

No new host/service or IP was created, so no NetBox/Beszel object was added.
Existing Forgejo guest and backup-freshness monitoring remain applicable.
Use current backup job/freshness evidence and periodic isolated restores, not
this dated receipt alone, to claim future revisions are protected.

## 12. Backup, restore and rollback

Proxmox LXC 108 root disk includes Git, LFS and application state.
Observed schedule: all guests at 00:30, daily 7 / weekly 4 / monthly 6 retention.
TrueNAS task 1 pulls daily at 01:00, deletion disabled. Times are scheduler-local.
No schedule/retention changes were made.

Post-import archive:
vzdump-lxc-108-2026_11_06-10_25_00.tar.zst
3,744,269,119 bytes.
SHA-256: 31573fd2b5ea59d244118d776fb9eff3877eccd32e04d6ad62f41cc4e7d07dc1.

Source: /mnt/backups/dump on Proxmox 192.168.50.10.
Independent copy: /mnt/Recovery/guests/homelab-proxmox-guests on TrueNAS
192.168.20.40. Pull job 62427 completed SUCCESS. Archive matched source SHA-256;
source Zstandard integrity passed.

Private isolated restore root:
/mnt/Recovery/brand-assets-restore-test-20261106-102500
Restored 1,867 regular Git/LFS files / 3,483,119,322 bytes, zero skipped links.
Recovered asset commit matched; all 2,591 originals matched and Git fsck passed.
Production was not replaced. This is Git/LFS recovery, not a booted whole-guest
service restore or a fresh offsite-recovery test.

The manual backup pruned nothing. Standard thin-pool warning was checked against
actual usage: 28.12% data / 1.32% metadata, with no storage settings changed.
Retain the original Mac library and previous releases; recover into isolation
before considering production changes. Skill rollback copies are retained in the
task workspace. Do not force-push or delete history as rollback.

## 13. Documentation and systems of record

HomeLab main root guidance/standard/portfolio link this project and the library.
The artwork repository contains portable setup, brand lookup, source inventory,
approval state and agent handover. Its backup receipt is external here so recording
the archive checksum does not recursively change the backed-up asset revision.
The HomeLab GitHub mirror carries documentation only; no direct GitHub push was made.

## 14. Graduation criteria

Complete: private shared storage, source preservation, independent retrieval,
network backup, isolated restore, writable agent workflow, resumable brand facts,
and a tested handover. No design approval or application deployment is implied.

## 15. Evidence log

2026-11-06: verified source/copy, approved hashes, private repo/no mirrors, published
commit, independent Git/LFS hashes, fresh native client retrieval/fsck, post-import
guest archive, TrueNAS job/copy/hash, isolated restore/full hashes/Git fsck,
portable helper, clean checkout and installed skill root.

## 16. User/agent handover

Give the next agent the linked AGENT-HANDOVER.md and exact brand name. It directs
the agent to clone into its own writable workspace, fetch LFS, resolve registry
paths and follow brand-specific approvals and reusable HomeLab standards.
A normal fresh retrieval plus resolver/verification walkthrough was performed.

## 17. Close-out

Shared asset storage and network recovery are operational. Originals remain intact.
No required migration work is deferred. Rights limitations, future access
provisioning and unrelated logo/app deployments retain their separate boundaries.
