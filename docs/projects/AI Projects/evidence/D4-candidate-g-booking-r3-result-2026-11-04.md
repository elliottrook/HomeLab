# D4 candidate-g booking r3 result — 2026-11-04

## Decision

**GO — scheduled / conditional.** Standing Stream A candidate-run authority
applies to exactly one transaction for registered workload
`sa3-evidence-envelope-quality-v1`.

## Authoritative reservation

- booking: `aster-stream-a-sa3-envelope-20261104-1315-r3`
- owner: `aster-stream-a`
- start: 2026-11-04 13:15:00 America/Vancouver
- end: 2026-11-04 14:45:00 America/Vancouver
- restore buffer: 900 seconds
- initial state: `scheduled`

The authoritative ledger returned `clear` for the complete 13:15–14:45 window
before reservation. The resulting booking names the registered, hash-pinned
workload and contains no arbitrary command.

## Static gates

Before booking, Stream A verified the exact 34-file installed manifest,
including the corrected source, drain/session, Doctor and manifest hashes. The
Lab Hours dispatcher and Doctor timers were active and enabled, the Doctor was
healthy, the lease was exactly `ready`, and the drain state, drain lock and
shared operation lock were absent.

## Runtime boundary

At claim time the dispatcher must independently recheck the booking, installed
pins, production health, whole-host lease and shared lock. The transaction may
make fourteen no-retry prose calls only after a successful bounded drain. It
must restore production unconditionally and retain content-free terminal
evidence. Any stale, missing, changed or uncertain gate is NO-GO. This booking
does not authorize a retry, model/backend change, routing promotion, tool grant
or deployment.

