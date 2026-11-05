# Aster Lab Hours SA3 candidate-i R2 card — 2026-11-04

## Booking proposal

- ID: `aster-stream-a-sa3-candidate-i-20261104-1830-r2`
- Owner/workload: `aster-stream-a` /
  `sa3-evidence-envelope-candidate-i-quality-v1`
- Window: 18:30–19:30 host-local offset `-07:00`, comprising the fixed
  2,700-second transaction ceiling and 900-second recovery reserve
- Authoritative ledger check: clear, no booking IDs

R2 is distinct from spent R1. R1 failed restored before the candidate workload
because the host adapter supplied candidate-g's scope prefix. Its attempt and
terminal evidence remain retained; it will not be retried or overwritten.

## Corrected installed boundary

Installed candidate-i proof retains all prior exact packet, runtime, model,
binary, transaction and wrapper pins. The changed host identities are:

- listener adapter:
  `80e7491b3d9bd3c457bf362baae97ba3377ac260dde1169933ddbdbc97cc1ee6`;
- 36-pin release manifest:
  `05e41525f08f52597128b6523b92c1ed7de3316cee09e3e79f95d347d31eb65d`.

The predecessor bytes are retained in root-only checkpoint
`sa3-candidate-i-scope-r1-20261104`. The installed host scope function, actual
guest command and guest wrapper independently agree on
`aster-llama-sa3-i-<token>.scope`. Lease, locks, services and production
postchecks pass with no restart.

## Runtime and terminal boundary

The dispatcher must recheck the exact reservation, installed pins, lease,
shared operation lock, candidate/listener absence, production health and
recovery reserve at claim. Accept success only for 20 cases, exactly 14 model
requests, six deterministic no-transport abstentions, zero retries/errors/
effects, result schema v2, candidate alias `candidate-i`, retained canonical
digest, exit zero, `production_restored=true`, no remaining candidate state,
scope, listener or lock, ready lease and healthy independent postchecks.

Any other state is terminal NO-GO without retry. Retain no prompt, answer,
case identity, response body, exception text or arbitrary output outside the
root-custodied result. This authorizes no model/backend change, repeated
attempt, route, tool grant, repair authority or automatic promotion.
