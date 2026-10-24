# F2 final-guard subcheck correction — independent review

**Reviewed:** 2026-10-24 America/Vancouver. **Platform source:** full commit
`770107dfe5a7f0473f99be98675752fa7fa86b14`.

## Finding

The correction replaces the single `FINAL_GUARD_SUBCHECK_FAILED` result with
bounded codes for clock, exact window, lease/receipt absence, host exclusion,
lease readiness, competing processes, load, installed pins, snapshot flags,
clock monotonicity and snapshot freshness. Raw command output and tracebacks do
not enter terminal state. Unexpected exceptions still fail closed under the
existing generic class.

The two candidate hashes independently match the platform card:

| Installed path | Current hash | Candidate hash |
|---|---|---|
| `f2_preflight_snapshot.py` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` | `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684` |
| `f2_scheduled_release_candidate.py` | `98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` |

Both installed files are root:root mode 0644. Recurring F2 timers remain
disabled/inactive. Stream A independently ran the focused suite from a clean
archive of the pinned commit: 24 tests passed with one expected macOS
root-custody skip. The platform owner separately reports 24/24 target-Linux
passes and 362 full-suite passes with eight expected skips.

## Decision boundary

The candidate is ready for one separately approved inactive two-file install
with fresh root-only rollback checkpoints, installed-hash verification and the
same target-Linux tests. Installation must leave all F2 timers disabled and
must not schedule or run F2, create a receipt or lease, stop a service, call a
model or advance F3. A later exact cycle requires its own card, independent
review and approval.
