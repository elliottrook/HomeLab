# F2 failure-phase correction — inactive-install card

Status: source-only preparation; HOLD. This card authorizes no installation,
scan, receipt, lease, service stop, model call, schedule activation, retry,
daemon reload, or remote push.

## Scope and exact file set

The corrected source is from reviewed commit
`183e7cfcc6d5de9c6e1da0d7f86c0cc8269f80c9`. Only this installed path would
change:

| Source | Installed target | Required SHA-256 | Required custody |
|---|---|---|---|
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23` | root:root 0644 |

The focused test is source-only and is not installed:

| Source test | SHA-256 |
|---|---|
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `df4d3402bff12f362432d53fc57af072eb67897a848864cc8da3eb706f5b2bf0` |

No unit file, timer file, wrapper, dependency module, state file, receipt
path, lease path, or service configuration is in the replacement set.

## Current Proxmox reconciliation

Read-only inventory on 2026-10-20 found:

- Installed coordinator: SHA-256
  `67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d`,
  root:root 0644. This differs from the corrected source and is the only
  installed source discrepancy requiring replacement.
- `f2-preflight-prepare.timer` and `f2-preflight-final.timer`: disabled and
  inactive.
- `f2-preflight-prepare-20261020.timer` and
  `f2-preflight-final-20261020.timer`: disabled and inactive; their one-time
  unit files are absent.
- Base prepare/final services are failed from the terminal October 20 attempt;
  this card does not clear, restart, or otherwise alter those states.
- `/var/lib/local-ai-lab/f2-scheduled/2026-10-20.json` is present and must be
  preserved as immutable cycle evidence; `/var/lib/local-ai-lab/f2-preflight/current.json`
  is absent.

These are observed discrepancies and not permission to repair the failed
services, delete state, rerun the cycle, or activate a schedule.

## Inactive staging and rollback plan

Before any future separately approved installation, create a fresh root-owned
0700 checkpoint such as `/root/aster-f2-failure-phase-rollback-183e7cfc`.
Save the current installed coordinator as root:root 0600 and record its
observed SHA-256. Do not checkpoint or replace any other path. If the target
is absent or the observed hash differs from the reconciled old hash, stop for
review rather than guessing a rollback source.

Stage the corrected source in a private root-owned 0700 directory. Verify the
source and staged bytes against the hashes above before any target write. The
only future target write is an atomic replacement of the coordinator with
root:root 0644. If any post-install check fails, restore only the saved
coordinator bytes and verify the old hash and custody. Do not remove the
October 20 state file.

## Required target-Linux validation

Against a private staging tree plus the installed dependency directory, run:

1. `PYTHONDONTWRITEBYTECODE=1` compile/import of the corrected coordinator.
2. The focused `test_f2_scheduled_release_candidate` suite, including
   first-prepare-failure preservation, final-attempt non-overwrite,
   bounded failure classes, timeout/process-group cleanup, custody, and
   projection checks. The reviewed source result is 10/10 passed.
3. Re-check the installed target hash/custody, all F2 timer states disabled /
   inactive, and absence of any new receipt, lease, lock, scan child, or
   preflight snapshot.

The validation must use synthetic runners and temporary state only. It must
not invoke the real observer, `zstd`, backup commands, TrueNAS, a model,
systemd start/reload, or any service command.

## Correction behavior

The corrected coordinator writes bounded `failure_class` values and an exact
`first_failure_phase` of `prepare` or `final`. A terminal `prepare/no_go`
state is never overwritten by a later final invocation. The October 20 state
was produced by the prior source and cannot be retroactively repaired by this
card; the next eligible cycle requires a fresh approval after this correction
is independently reviewed and, if authorized, installed.

## Explicit boundary

This is an inactive-install preparation card only. It does not authorize a
new F2 attempt, any retry of October 20, a receipt or F3 release, a lease,
service stop, model request, schedule activation, daemon reload, deletion of
the terminal state, or a Git push.
