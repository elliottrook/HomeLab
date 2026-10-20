# F2 failure-phase preservation correction — 2026-10-20

Status: source-only correction; not installed and not authorized for a new
scan. The October 20 cycle remains terminal `no_go` and must not be retried.

## Observed defect

The two-phase coordinator wrote `prepare/no_go` when the 01:09 preparation
failed, then the 01:10 final invocation overwrote that state with
`final/no_go`. It also exposed Python exception type names as the error class,
which was not a bounded diagnostic vocabulary. The resulting state could not
distinguish a failed preparation from a failed final gate.

## Correction

`f2_scheduled_release_candidate.py` now:

- records `first_failure_phase` as exactly `prepare` or `final`;
- records `failure_class` from a fixed allowlist only;
- preserves the first terminal `no_go` state when a later final invocation is
  attempted, without retrying or replacing it;
- keeps the existing terminal-state and fail-closed behavior; and
- emits only the phase and bounded failure class in CLI failure output.

The bounded classes are:

```text
WINDOW, STATE_CONFLICT, STATE_CUSTODY, PREFLIGHT_FAILED,
FINAL_GUARD_FAILED, OBSERVER_TIMEOUT, OBSERVER_FAILED,
OBSERVER_OUTPUT_OVERSIZED, OBSERVER_OUTPUT_INVALID,
OBSERVER_PROJECTION_INVALID, FINAL_FAILED, UNKNOWN
```

No exception message, archive path, command output, credential, or private
diagnostic is persisted or printed.

## Frozen source pins

| Path | SHA-256 |
|---|---|
| `scripts/local-ai/f2_scheduled_release_candidate.py` | `aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23` |
| `scripts/local-ai/test_f2_scheduled_release_candidate.py` | `df4d3402bff12f362432d53fc57af072eb67897a848864cc8da3eb706f5b2bf0` |

## Offline validation

- Focused correction suite: 10/10 passed.
- Full local `scripts/local-ai` suite: 344 passed, 8 expected skips.
- Tests cover first preparation failure surviving final invocation, bounded
  observer-timeout classification, terminal behavior, and existing custody,
  deadline, projection, and process-group safeguards.

The correction has not been installed, enabled, invoked, or pushed. It does
not authorize a new F2 scan, F3 release, lease, service stop, model call, or
timer change.
