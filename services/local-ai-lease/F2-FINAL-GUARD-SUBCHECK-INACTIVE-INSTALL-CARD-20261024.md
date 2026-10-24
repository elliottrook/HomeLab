# F2 final-guard subcheck correction — inactive install card

Status: source-only HOLD. This card authorizes no installation, activation,
retry, reschedule, scan, receipt, lease, service stop, model call, or F3.

## October 24 evidence

Prepare succeeded at 01:15. Final failed at 01:20 with
`FINAL_GUARD_SUBCHECK_FAILED`; no observer child or result rows were produced.
The installed coordinator wrapper collapsed every final-guard exception into
that one code, so the failing guard was not identifiable. Historical terminal
evidence must remain preserved.

## Bounded per-subcheck correction

The source now retains content-free codes for each final guard boundary:

| Guard boundary | Code |
|---|---|
| Clock probe/parse | `FINAL_GUARD_CLOCK` |
| Exact cycle/window | `FINAL_GUARD_WINDOW` |
| Lease/receipt absence | `FINAL_GUARD_LEASE_RECEIPT` |
| Host exclusion held | `FINAL_GUARD_EXCLUSION` |
| Manual lease ready | `FINAL_GUARD_LEASE_READY` |
| Quiet process check | `FINAL_GUARD_QUIET_PROCESSES` |
| Host load | `FINAL_GUARD_LOAD` |
| Installed source pins | `FINAL_GUARD_INSTALLED_PIN` |
| Snapshot flags | `FINAL_GUARD_SNAPSHOT_FLAGS` |
| Clock monotonicity | `FINAL_GUARD_CLOCK_MONOTONIC` |
| Snapshot freshness | `FINAL_GUARD_FRESHNESS` |

Raw command output and tracebacks remain suppressed; only the bounded code is
persisted in the terminal state.

## Source pins, not installed

The installed coordinator remains the previously approved diagnostic version.
Replace only these two cooperating source files after separate approval:

| Path | Current installed/source baseline | Corrected source SHA-256 |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_preflight_snapshot.py` | `a199e369b2a3843a911a3978b410b525db7f1c67a9a8a7878f86f4a829cf57d7` | `6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684` |
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425` | `9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1` |

The full prior installed coordinator hash is preserved in the installation
record and must be re-read before any replacement. Supporting wrapper,
observer, producer, and integrity pins remain unchanged. Proposed rollback is
a fresh root-only checkpoint of the current two files.

## Validation

- Offline guard/coordinator tests: 24 passed, 1 expected root-custody skip.
- Target Linux guard/coordinator tests: 24/24 passed with private staging;
  temporary transfer files were removed.
- Full repository-local suite must pass before any install.

No timer activation or F2 rerun is part of this correction. Any future exact
cycle requires a new date-specific activation card and separate approval.
