# M3 J2 deterministic training-recipe manifest boundary — 2026-11-04

## Decision

**SOURCE-ONLY RECIPE CONTRACT READY; NO MODEL OR DATA CREATED.**

The J2 byte-convolution candidate now has an exact deterministic recipe
manifest and fail-closed validator. The manifest consumes no corpus or
evaluation content and performs no training. It remains bound to the frozen
J2 preregistration, the existing 16-label ontology and deterministic guard.

## Frozen recipe

The contract fixes strict UTF-8 encoding, first-512-byte truncation, distinct
right-padding token 256, a trainable 32-dimensional byte embedding, same-padded
width-3/5/7 convolutions with 48 ReLU channels each, global max pooling, a
96-dimensional ReLU hidden layer and a sorted 16-label softmax output.

Initialization uses seed `20261104`, SplitMix64, binary64 parameters, exact
parameter traversal, Xavier-uniform weights and zero biases. Training is fixed
at 40 epochs of single-thread CPU AdamW over case-ID-sorted 32-row batches,
with no shuffling, early stopping, accelerator, network, evaluation input or
sealed-holdout access.

Checkpoint and threshold selection use only the frozen 192-row validation
partition. The checkpoint maximizes guarded joint-label exactness under fixed
tie-breakers. Margin selection uses the inclusive 0.000–1.000 grid at 0.005
steps, requires at least 116 accepted rows, and requires every accepted row to
match both its raw label and guarded interpretation. No eligible selection
rejects the candidate.

The artifact contract fixes ten-decimal ties-to-even quantization, exact source
bindings, canonical serialization, an externally pinned digest, full 192-row
post-reload replay and two clean CPU reproductions. The guard may replace a
coherent label only with a strictly more restrictive disposition, while the
personal-sensitivity floor remains mandatory. Authority is not granted;
automatic routing, tools, route effects and deployment remain off.

## Proof and limits

The focused 9/9 tests and combined 45/45 J2 source suite cover exact acceptance
plus fail-closed drift in UTF-8 byte
handling, architecture, initialization, optimizer, row order, offline inputs,
validation selection, minimum coverage, quantization, replay, artifact digest,
guard policy, authority and routing. Exact source identities and the final test
count after verification are:

- validator: `c7266af3c0459525e6d63b3c7605a54c630c411df47dc83c414234eb3df44cf0`;
- tests: `09e1ef6242fd446b6b31c0862da4805efee75a97fba3f3561a517b94e82f6468`;
- exact manifest: `81be6b610f230361057c9d969e28b76677e7c0464bd100d79c56f0fde68a74a6`.

This milestone consumes no corpus or label-review content and creates no
evaluation set, model,
checkpoint, confidence threshold or artifact. It does not authorize training,
a Lab Hours booking, access to sealed content, deployment, routing or tools.
