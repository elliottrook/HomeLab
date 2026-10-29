# Lab health remediation — 2026-10-29

## Scope

Reconcile the dirty primary checkout, rerun HomeLab Doctor and configuration
drift, and repair only confirmed current failures. No credential, firewall,
public-ingress, guest, or destructive backup-retention change was included.

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

## Validation

- Focused Python tests: 21 passed.
- Python compilation, shell syntax, synthetic report generation, and
  `git diff --check`: passed.
- Configuration drift: `NONE`; baseline 2026-10-29 09:02:26 PDT, 88 protected
  entries.
- Final Doctor: 93 passed, 2 warnings, 0 failures.
- Git working tree: clean.

## Remaining warnings

- Jellyfin integrity reports two duplicate candidates requiring content review:
  Watoto Children's Choir (`Mambo Sawa` versus `Mambo Sawa Life Is Good!`) and
  Taylor Swift (`folklore` versus `folklore [Bonus Track]`). No media was
  deleted or consolidated automatically.
- IDrive reports 895.8 GB current plus 121.8 GB retained history, 1.018 TB
  total. The report is current and the configured lifecycle remains active.
  Reducing usage would delete recovery history or current backups and requires
  a separate, exact retention decision; the warning was not suppressed.
