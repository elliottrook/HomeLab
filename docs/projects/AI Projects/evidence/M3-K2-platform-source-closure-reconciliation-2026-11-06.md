# M3 K2 platform source-closure reconciliation — 2026-11-06

## Result

The current 57-pin Lab Hours release is now source-exact in the platform
worktree. A broad Lab Hours regression found that the manifest had advanced to
the fixed-card-capture release while two source files were not represented by
the checked-out tree and three tests still described the preceding dispatcher,
release name and EPUB scheduler baseline.

The missing sources were recovered read-only from their root-custodied
platform evidence, without changing the installed release or the active B60
booking:

- `lab_hours_reserved_runner.py`:
  `27e33550698d01ec7af78a74c910d67ea191503732201210599e635ec9f3dea9`
- `b60_post_xe_r5_card_bridge.py`:
  `3bd94a1e99491a0c23b4e530161389d3ef80a13fa7f2f5a35a9bad5f918df209`

Both digests exactly match the existing release manifest. The dispatcher fake
now implements the current expired-session and waiting-booking calls, the
release test requires the current 57-pin identity, and the Doctor test models
the current retired EPUB scheduler with the monitor enabled and the worker
timer disabled.

## Verification

`python3 -m unittest discover -s scripts/local-ai -p 'test_lab_hours*.py'`
passes 52/52. `git diff --check` also passes.

This was an offline source reconciliation only. It did not claim or alter a
booking, acquire a lease, change a lock, install a file, invoke a workload,
stop or restart a service, or change a model or route.
