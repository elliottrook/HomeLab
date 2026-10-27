# F2 observer-exit diagnostic source review — 2026-10-27

**Decision:** GO for a separately approved inactive one-file installation.

Stream A reviewed platform commit
`be6cafa47d77668a69181a80018a755d6f740840`, based on the frozen October 27
platform source. The candidate explains why the terminal state retained only
`OBSERVER_EXIT_NONZERO`: the observer child had emitted a bounded JSON failure
projection, but the coordinator checked its nonzero exit before parsing that
projection and discarded its phase.

The correction changes only the coordinator. It accepts an exact three-field
`no_go` projection and maps the known child phases to bounded classes:

- `preflight` to `OBSERVER_CHILD_PREFLIGHT_DENIED`;
- `observer` to `OBSERVER_CHILD_SCAN_FAILED`; and
- `result` to `OBSERVER_CHILD_RESULT_INVALID`.

Oversized, malformed, extra-field, unknown-phase or non-identifier error-class
output retains `OBSERVER_EXIT_NONZERO`. No exception text, command output,
archive content or path is persisted. Timeout, process-group termination,
one-shot ownership and successful projection validation are unchanged.

The focused coordinator and observer suites passed 31/31. A clean archive of
the committed source passed 55 tests across the complete F2 suite with one
expected non-root custody skip. The accompanying historical-card test now
validates the frozen October 21 pins rather than incorrectly requiring that
historical card to match the moving source tree.

The install card pins predecessor `6a1d520a…8193` and candidate
`efe8bc99…87ec`, requires root-only rollback and target-Linux test proof, and
leaves every F2 timer disabled and inactive. The source correction cannot
recover the child phase discarded on October 27 and does not authorize a host
change, timer, scan, F3 conversion, receipt, lease, service stop, model call,
schedule change or Git push.
