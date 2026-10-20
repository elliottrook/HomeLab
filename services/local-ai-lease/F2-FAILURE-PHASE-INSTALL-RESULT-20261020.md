# F2 failure-phase correction — installation result

Date: 2026-10-20
Status: bounded diagnostic installation complete; no F2 retry authorized or run.

## Installed change

The reviewed coordinator from commit
`183e7cfcc6d5de9c6e1da0d7f86c0cc8269f80c9` was installed at:

`/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py`

The pre-install target hash was verified as
`67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d`.
The post-install hash is
`aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23`.
The installed file is `root:root` mode `0644`.

## Rollback checkpoint

The old bytes were preserved and verified at:

`/root/aster-f2-failure-phase-rollback-183e7cfc/f2_scheduled_release_candidate.py`

The checkpoint hash is
`67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d` and
custody is `root:root` mode `0600`. Rollback, if separately authorized, is
limited to restoring those bytes to the coordinator path.

## Validation and post-checks

- Target-Linux compile/import validation passed.
- Target-Linux focused F2 suite passed: 10/10.
- F2 timers `f2-preflight-prepare.timer`, `f2-preflight-final.timer`,
  `f2-preflight-prepare-20261020.timer`, and
  `f2-preflight-final-20261020.timer` are all loaded, inactive, and disabled.
- `f2-preflight-prepare.service` and `f2-preflight-final.service` remain
  failed from the prior attempt; they were not cleared, restarted, or changed.
- The terminal state file remains present and
  `/var/lib/local-ai-lab/f2-preflight/current.json` remains absent.
- No F2 coordinator, zstd, or scan child was running during the post-check.

No receipt, lease, model call, service restart, schedule activation, backup
operation, or F2 retry was performed. Existing unrelated system locks and
checkpoint directories were not modified.

## Local record

This result is recorded locally only. It does not authorize a new F2 cycle,
receipt, lease, service repair, schedule activation, or remote push.
