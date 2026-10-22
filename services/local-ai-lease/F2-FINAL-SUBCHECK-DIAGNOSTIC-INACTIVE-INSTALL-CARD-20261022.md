# F2 final-subcheck diagnostics — inactive install card

Status: source-only HOLD. This card proposes one bounded coordinator correction
after the 2026-10-22 final no-go. It authorizes no install, timer activation,
retry, reschedule, scan, receipt, lease, service stop, model call, or F3.

## Observed failure

The 2026-10-22 prepare phase completed and wrote a valid prepared state. The
01:20 final phase exited 1 and persisted only coarse `FINAL_FAILED`; service
stdout and stderr were deliberately suppressed, and no archive/result rows were
written. The terminal state was preserved, no lease/lock/receipt/scanner
remained, and the spent date-specific timers were removed under the approved
post-cycle rollback.

## Bounded correction

The coordinator now wraps each final subcheck with content-free bounded codes:

| Subcheck | Failure code |
|---|---|
| Final guard invocation | `FINAL_GUARD_SUBCHECK_FAILED` |
| Observer process launch | `OBSERVER_LAUNCH_FAILED` |
| Observer communication | `OBSERVER_COMMUNICATION_FAILED` |
| Observer exits nonzero | `OBSERVER_EXIT_NONZERO` |
| Observer timeout | existing `OBSERVER_TIMEOUT` |
| Observer output/projection | existing bounded output/projection codes |

No command output, credentials, paths from child output, or traceback is written
to the durable state. The existing first-failure and no-retry rules remain.

## Exact source pins, not installed

Preserve the currently installed coordinator as a root-owned 0600 checkpoint,
then replace only this coordinator after separate approval. The four corrected
supporting sources remain unchanged and already installed from the prior
approved correction.

| Path | Current installed SHA-256 | Corrected source SHA-256 |
|---|---|---|
| `/usr/local/libexec/local-ai-lease/f2_scheduled_release_candidate.py` | `fd711a4c1afa9fe128464f61390d63c54f7e513a8811cbc79f0d27c522452356` | `98b26e88fc17418f0f48dbf24aafb3b44b06069de5fec2d244b55e58d7adb425` |

Source test pin: `scripts/local-ai/test_f2_scheduled_release_candidate.py` is
`5d07939244276d465636b01e97f34e14fd3797804fbbcd825dd545ae2fa52ddb`.
Proposed rollback checkpoint:
`/root/aster-f2-final-subcheck-rollback-<new-source-short-hash>`.

## Validation evidence

- Local focused coordinator tests: 13/13 passed.
- Target Linux focused coordinator tests: 13/13 passed under Python 3.13
  using private `/tmp` staging only; no installed file was changed.
- Temporary target staging was removed.
- The test cases cover guard, launch, nonzero observer exit, timeout, output,
  state custody, one-shot behavior, and first-failure preservation.

Before any future installation, re-read the live coordinator/supporting hashes,
custody, timer state, and terminal state. Install only the coordinator after a
fresh approval, run the same target-side tests, and do not activate or retry a
cycle as part of installation. A later exact-cycle activation requires a new
date-specific card and separate approval.
