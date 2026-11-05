# SA3 candidate-j R1 NO-GO and exclusion correction — 2026-11-04

Booking `aster-stream-a-sa3-candidate-j-20261104-2100-r1` claimed exactly at
21:00 and ended terminal NO-GO at 21:03:07. The bounded terminal state records
`first_failure_phase=owner-transaction`,
`failure_code=OWNER_TRANSACTION_FAILED_RESTORED` and
`production_restored=true`. The lease returned to ready with no candidate
process, scope, state or lock. R1 is spent and will not be retried.

The retained owner error identifies the deterministic source defect before any
model request: candidate-j's wrapper treated the presence of installed
candidate-g/i public packet files in the shared runtime directory as forbidden
review material. Those predecessor files are expected inert shared-runtime
residents and are not imported or pinned by candidate-j. The wrapper's exact
five-file pin set already enforces candidate isolation.

The correction removes only those two predecessor packet names from the
existence ban. Blind-review and decision files remain forbidden. Candidate-j's
pin set still excludes every candidate-g/i packet, key and review file. The
corrected wrapper is `a883c144…5f2a`; the repinned 39-file release manifest is
`9eddfdd2…d665`. Eighteen focused candidate-j tests and current-release
integrity pass.

The dedicated correction installer replaces only the host wrapper, guest
wrapper and host release manifest after exact old-hash, custody, ready-lease,
lock and unit checks. It retains root-only rollback checkpoints and restarts no
service. Installation and any fresh booking remain distinct effects.
