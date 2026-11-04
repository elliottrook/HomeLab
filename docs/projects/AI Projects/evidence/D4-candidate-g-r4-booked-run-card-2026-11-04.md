# D4 candidate-g r4 booked run card — 2026-11-04

## State

**GO — scheduled/conditional.** The authoritative Lab Hours ledger was clear
for the complete window before reservation and now contains exactly the fresh
booking `aster-stream-a-sa3-envelope-20261104-1400-r4` for 14:00–15:30
America/Vancouver, owner `aster-stream-a`, registered workload
`sa3-evidence-envelope-quality-v1`, and 900-second recovery buffer.

## Static and current proof

- Corrected host adapter: `fecb32cb…c74600c`.
- Corrected LXC110 wrapper: `1d01c8c…3a4fc2`.
- Matching release manifest: `6fa56d9c…a157f71`, 34 pins loaded.
- Host/guest diagnostic proofs: passed.
- Root-only host and guest predecessor checkpoints: retained.
- Aggregate Doctor: healthy, no codes.
- Whole-host lease: exactly ready.
- Shared drain/operation state and port-11436 listener: absent.
- Production postcheck: healthy, zero restarts on Aster Agent, accepted llama,
  Speech, `pvescheduler`, and `pvestatd`.
- Exact platform booking card: mirrored commit `6738775e`.

## Fresh execution gates

The dispatcher must still recheck the booking, installed pins/custody, lease,
shared lock, production sources/services, listener absence and restoration
capacity at claim time. Any changed, failed or uncertain gate is terminal
NO-GO without a model call.

The transaction is one attempt with no retry or extension. It is scoreable only
for exactly 20 cases, 14 model requests, zero errors, frozen identities, exit
zero, retained bounded digest, `production_restored=true`, no remaining
candidate state/listener/lock, lease ready and all independent production
postchecks healthy. A nonzero result must retain its exact bounded class when
available and otherwise remain conservatively unclassified.

This card authorizes no model/backend change, restart, route/tool grant,
automatic promotion or reuse of spent r3. Only a fully validated completion may
advance to the already frozen model-blind review.
