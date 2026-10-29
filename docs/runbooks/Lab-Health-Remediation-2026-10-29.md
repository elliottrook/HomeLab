# Lab health remediation — 2026-10-29

## Scope

Reconcile the dirty primary checkout, rerun HomeLab Doctor and configuration
drift, and repair only confirmed current failures. No credential, firewall,
public-ingress, or guest change was included. A later owner-approved follow-up
permanently removed only expired noncurrent IDrive guest-object versions after
verifying the retained recovery copies described below.

## Repository reconciliation

- Preserved the combined SA2 diagnostic-publication and Lab Doctor work on
  `codex/lab-doctor-drift-remediation-20261029` before moving local `main`.
- Added `.aster-local-state/` to `.gitignore`; the recovery checkpoints remain
  on disk and were not deleted.
- Pruned 19 worktree registrations whose recorded directories no longer held a
  usable checkout. Active worktrees, including AsterTV v2, were left intact.
- Fast-forwarded local `main` to the validated remediation commits. Remote Git
  publication remains separately approval-gated.

## Operational repairs

1. Restarted only `aster-fixed-doctor-caller.service` in LXC 104. The service
   is active, its caller socket is mode `0660` with the expected identities,
   and the AI-PAM check passes. Rollback is to stop that caller service.
2. Restored TrueNAS rsync task 3 from 02:00 to the documented 04:20 schedule.
   Its source/destination, pull direction, include filter, delete policy, and
   enabled state were unchanged. Rollback is to restore the 02:00 schedule.
3. Reran the protected TrueNAS configuration exporter. Two attempts stopped at
   the existing 120-second SQLite deadline without replacing the verified
   archive. A source-local instrumented retry then completed, showing transient
   database contention rather than a native TrueNAS export fault. The published
   archive covers 20 applications, 24 verified SQLite databases and 5,074 files;
   media remains excluded.
4. Corrected the News Aggregator Doctor query to compare ISO timestamps through
   SQLite `julianday()`. The previous lexical comparison counted a 16-hour-old
   connection reset as recent. The corrected two-hour query observed 92
   successes and zero failures.
5. After Jason approved the recommended bounded cleanup, audited all 32
   noncurrent `homelab-proxmox-guests` versions under the relay lock. Every
   version was 170--195 hours old, beyond the active one-day lifecycle window,
   absent from the retained local filenames, and associated with a guest that
   still had 11--12 current local recovery archives. All 237 current cloud
   guest archives matched local filenames; the other 11 local archives were the
   intentional Paperless exclusion. Permanently deleted exactly 32 reviewed
   noncurrent versions / 83,610,183,597 encrypted bytes. All 237 current cloud
   guest objects and all 248 local recovery archives remained unchanged; no
   configuration, family, Home Assistant, Mac, Jellyfin or service history was
   targeted. Protected evidence is retained in LXC 112 under
   `/var/lib/idrive-version-maintenance/cleanup-20261029-guest-history-*`.
6. Resolved the two Jellyfin duplicate reviews using format and payload
   evidence rather than folder names alone. Retained Watoto Children's Choir
   `Mambo Sawa Life Is Good!`: both copies were AAC/M4A at 44.1 kHz, stereo,
   16-bit, while the retained copy was the newer iTunes 12.10.9.3 encode with
   a slightly larger aggregate audio payload and better artwork; the competing
   copy identified iTunes 9.0.2. Retained Taylor Swift `folklore [Bonus Track]`:
   both copies were 16-bit/44.1-kHz stereo FLAC, tracks 1--16 had identical
   decoded-audio MD5 values, and the retained copy also had track-17 synced
   lyrics and higher-resolution artwork. Atomically moved the two inferior
   folders (496,663,321 bytes total) outside the Jellyfin library to the
   recoverable quarantine below; no media was permanently deleted:
   `/mnt/Media/data/tools/jellyfin-integrity/quarantine/20261029-better-format-selection/`.
   Its manifest contains a SHA-256 inventory of both quarantined and retained
   folders for exact rollback and verification.

## Validation

- Focused Python tests: 21 passed.
- Python compilation, shell syntax, synthetic report generation, and
  `git diff --check`: passed.
- Configuration drift: `NONE`; baseline 2026-10-29 09:02:26 PDT, 88 protected
  entries.
- Final Doctor after the IDrive and Jellyfin follow-ups: 95 passed, 0 warnings,
  0 failures.
- Git working tree: clean.

## Remaining warnings

- None. A fresh Jellyfin scan and dry integrity report
  (`20261029T173826Z-run.json`) found six candidate comparisons, zero duplicates
  awaiting approval, five existing ambiguous references, zero action errors,
  zero collection alerts and no cleanup-trigger drift. Doctor reports the
  Jellyfin integrity run clean.

## IDrive follow-up result

- Refreshed usage is 895,821,846,003 current bytes plus 38,199,814,395 history
  bytes, 934,021,660,398 bytes total. The usage check now passes.
- Guest noncurrent history is zero; the one-day guest lifecycle rule remains
  enabled. The provider may asynchronously remove the 32 empty delete markers.
- The remaining 38.2 GB is bounded history for mutable configuration, Gowest,
  Home Assistant and Mac data, plus negligible old validation objects. It was
  preserved because it is not redundant dated guest-archive history.
