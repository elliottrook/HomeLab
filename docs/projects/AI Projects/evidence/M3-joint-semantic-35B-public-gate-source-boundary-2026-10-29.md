# M3 joint-semantic 35B public-gate source boundary — 2026-10-29

## Decision

**SOURCE READY / LIVE MODEL AND RESTART EFFECT GATED.** Stream A now has one
materially different M3 candidate for the next honest public gate. It uses the
already staged, hash-pinned Qwen3.6-35B-A3B Q4_K_M artifact and its learned
reasoning representation to choose one complete semantic decision in one call.
It does not split the request into independently prompted fields, add public
examples, tune a rubric against the exposed cases, train another embedding
head, or open any private calibration or holdout set.

## Exact candidate

- model artifact SHA-256:
  `671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7`;
- accepted b11429/SYCL runtime SHA-256:
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`;
- candidate source SHA-256:
  `b2682aa294e5d29b36c961c0b6b5b1593312781026c4f1e3424836ee44f63309`;
- public runner SHA-256:
  `b91e2dc3c2b6c8fbb89d912d8789ea2ac49d6ac412d9e77f854f66c259ac18d3`;
- transaction contract SHA-256:
  `a1a4e16b149c5f0e096e2d8e4a5b6d8ef2af37b07eff7802d0f0bae3bcdb6bf1`;
- public fixture SHA-256:
  `1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`.

The model sees the fixed public complete-label catalogue and the one request.
It may reason privately under a 192-token reasoning budget, but only the typed
`label_id` final answer is parsed. Raw reasoning is neither parsed nor retained.
The existing deterministic tightening guard remains authoritative after the
selection. The candidate has no tools, route effects, confidence output,
permission field or execution authority.

## Honest public gate

The gate is fixed before the first live candidate call:

- exactly 24 public synthetic cases and 24 sequential model calls;
- zero retries;
- at least 23/24 complete interpretations exact;
- zero unsafe false routes;
- zero routed privacy underclassifications;
- no private calibration or holdout access;
- automatic routing remains off regardless of result.

The machine-readable packet is
`scripts/aster-adaptive/fixtures/m3-joint-semantic-35b-public-v1.json`.

## Effect and recovery boundary

The pure transaction contract requires all of the following before the first
effect: an exact authoritative Lab Hours booking for the registered workload,
the whole-host lease, the shared operation lock, an independent recovery owner,
an authenticated accepted production baseline, and the separately retained
restart/model transaction authorization. It fixes one read-only,
backup-excluded candidate mount, four LXC110 stop/start actions, one transient
35B service, the 24-case gate, and exact restoration of the accepted 9B/SYCL
production stack. Every failure enters one recovery sequence. There is no
retry, promotion or automatic routing. Uncertain recovery retains state and
rejects the result.

## Verification

The focused candidate, transaction, public-runner and deterministic-guard
suite passed **28/28**. The broader dependency-free NLU discovery passed
**415/415 importable tests**; its sole unrun module requires `pydantic`, which
is not installed in the host Xcode Python and is unrelated to this candidate.
No live service, model, booking, lease, lock, schedule or production file was
changed.

The remaining preparation is a privileged driver/registered-workload packet
that implements this exact contract. Its inactive installation can be reviewed
and tested without a model change or restart. The eventual live public gate is
the first action in this path that needs the retained restart/model approval.

