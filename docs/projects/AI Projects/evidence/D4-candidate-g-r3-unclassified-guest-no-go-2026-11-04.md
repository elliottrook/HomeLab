# D4 candidate-g r3 unclassified guest NO-GO — 2026-11-04

## Decision

Booking `aster-stream-a-sa3-envelope-20261104-1315-r3` is spent and **NO-GO**.
It must not be retried. It produced no retained candidate result, so it cannot
be scored or sent to blind review.

## Measured transaction

- Authoritative window: 2026-11-04 13:15–14:45 America/Vancouver.
- Claimed: exactly 13:15:00 by `lh-32065516f943bf80f673`.
- Terminal: 13:18:13, after 193 seconds.
- State: `no_go`.
- First failure phase: `owner-transaction`.
- Failure code: `OWNER_TRANSACTION_FAILED_RESTORED`.
- Production restored: `true`.
- Owner error: `candidate-g listener exited nonzero: unclassified guest failure`.
- Retained result: absent.

The guest journal shows that the transient llama server accepted candidate
requests, but the adapter removed its temporary raw capture during required
cleanup and retained no content-free inner failure class. It is therefore not
valid to infer whether all 14 model requests completed or which validation gate
failed.

## Independent restoration

Post-transaction checks passed:

- Lab Hours lease returned exactly `ready` with no lease, shared-operation, or
  drain lock;
- no candidate listener, capture, transient guest unit, or model process
  remained;
- LXC104, LXC110 and LXC116 remained running;
- Aster Agent, accepted 9B/SYCL production llama, Speech, News, EPUB,
  dispatcher, Doctor, `pvescheduler`, and `pvestatd` were healthy;
- the aggregate Doctor returned healthy with no codes.

The failure therefore did not leave production degraded.

## Deterministic diagnostic defect and correction

The host adapter attempted to parse the entire guest stderr stream as one JSON
document. Transport or systemd text surrounding the wrapper's bounded JSON
receipt made that decode fail and replaced the inner code with `unclassified
guest failure`.

Platform commit `1a185f54e8470ab0766ccd84ba61cdc3330206ef` corrects the
source-only diagnostic path:

- the host adapter now selects only the last bounded standalone JSON code;
- the guest wrapper emits only error count and sorted error-class names when a
  result contains model-request errors;
- prompts, answers, case identifiers and arbitrary exception messages remain
  excluded;
- invalid or over-length diagnostics still fail closed as unclassified.

The focused source suite passed 27/27 and the same parser/error-class behavior
passed a direct Proxmox Python proof. Forgejo and its GitHub mirror both carry
the exact platform commit. No production file or service was changed by this
source correction.

## Next gate

Build and review a reversible inactive installer, validate exact installed
hashes/custody and target behavior, then obtain a fresh conflict-free Lab Hours
booking for any future one-attempt candidate-g transaction. R3 itself remains
spent; this evidence does not authorize a retry, model change, deployment,
routing promotion, or blind-review claim.
