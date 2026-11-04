# D4 candidate-g r8 booking review — 2026-11-04

## Decision

R8 is **READY / conditional** as one fresh registered candidate-g transaction.
R3–R7 are spent and are not retried.

The authoritative Lab Hours ledger reported the complete 16:15–17:45
offset-qualified window clear at 15:47. The window includes the registered
workload's fixed 900-second recovery reserve. The booking identity is
`aster-stream-a-sa3-envelope-20261104-1615-r8`, owned by `aster-stream-a` and
bound to registered workload `sa3-evidence-envelope-quality-v1`.

## Static gate

The installed response-normalization correction passes exact host/guest hashes
and root custody, both recovery checkpoints, all 34 release pins, bounded known
llama metadata normalization and fail-closed unknown-key rejection. The lease
was ready, Doctor healthy with zero codes, shared state/locks and candidate
listener absent, required production services healthy and restart counts zero.

The transaction remains fail closed on any fresh ledger conflict, missing
booking, lease/lock failure, pin drift, service-health failure or insufficient
restoration time. The dispatcher owns the claim and effect; Stream A does not
manually invoke or retry it.

## Acceptance boundary

Accept a candidate result only for 20 frozen cases, exactly 14 model requests,
zero retries/errors/effects, correct identities and digest, exit zero, complete
production restoration, no residual process/listener/state/lock, ready lease
and passing independent postchecks. Otherwise record the first bounded failure
as NO-GO without retry.

This card authorizes no model/backend change, restart, blind-review outcome,
automatic routing, tool grant or promotion.
