# M3 J2 independent gate audit and identity hardening — 2026-11-05

## Result

An independent source audit found that J2 is not yet training-admission ready.
Candidate-v4, its reviews, owner corpus-release acceptance and the deterministic
training recipe remain valid, but three stronger gates are still missing:

1. the evaluation receipt records a different normalized-set digest but does
   not bind a zero-intersection comparison against the released corpus;
2. the handoff requires independently verifiable detached-signature or
   separate-account evidence, while the current validator verifies only each
   receipt's self-hash; and
3. no single admission object yet cross-binds corpus release, owner acceptance,
   authenticated custody, sealed evaluation and the exact recipe.

Those gaps remain fail-closed. No training, sealed-evaluation access, model
creation, booking, routing, tools, authority or deployment is authorized.

## Completed hardening

The audit also found that whitespace or case variants could make one role look
distinct while naming the same logical identity. The custody validator now
requires every corpus-custodian, label-reviewer and evaluation-custodian ID to
be a canonical lower-case identifier containing only letters, digits, dots,
underscores and hyphens, with no surrounding whitespace. Role equality is
then checked only after that canonical form is accepted.

The source-only J2 suite first passed 54/54, including explicit rejection
of leading/trailing whitespace, case variants and embedded spaces. This is a
source validation improvement only; it is not evidence of external custody.

The next source-only increment adds dependency-free RSA-2048
PKCS#1-v1.5/SHA-256 verification for exact external-proof envelopes. It pins a
trusted public-key fingerprint outside the supplied proof, binds the exact
payload bytes, scope and canonical signer identity, and rejects altered keys,
payloads, scopes, signatures and duplicate JSON keys. A separate signed
disjointness receipt now requires the exact accepted corpus identities, 960
corpus rows, 32 evaluation cases, the normalized exact-set comparison
algorithm and intersection count zero. Merely supplying a different set digest
is no longer sufficient. The signer must be the receipt's canonical custodian.

Synthetic fixed-signature vectors exercise the verifier without adding a
runtime package or private key. They prove the implementation contract only;
the real gate still requires a separately controlled custodian key whose
fingerprint is explicitly trusted. The expanded J2 suite passes 60/60.

The combined admission validator now structurally cross-binds
the exact corpus-release summary, owner acceptance, frozen recipe, corpus and
evaluation receipts, two distinct pinned signer keys, and the signed
zero-intersection receipt. It rejects reused roles/keys and any release,
owner, evaluation or disjointness mismatch. Even a complete chain advances
only to `eligible-for-owner-training-effect-review`; training authorization,
sealed-evaluation access, routing, authority and deployment remain false.

A second independent audit found two material defects before any real evidence
existed: corpus custody was not compared to the accepted release, and caller-
supplied key hashes were mistaken for trust anchors. The validator now binds
all four corpus/review digests, requires the exact retained owner-acceptance
file digest, takes signer fingerprints only from a compiled owner-reviewed
registry, retains all proof-file digests and labels role separation as declared
rather than authenticated. That registry is intentionally empty until real
keys receive owner trust review, so no real combined admission can currently
pass. RSA keys must now be canonical odd 2048-bit moduli.

## Next autonomous work

The remaining work is external rather than another shared-worktree identity
claim: obtain the separately controlled corpus and evaluation keys/evidence,
pin their public-key fingerprints through owner review, validate the real
content-free chain, and only then present a training-effect release candidate.
Training remains a later, separately authorized effect.

Independent trainer implementation can still progress without opening those
data gates. The first dependency-free reference primitives now implement the
frozen UTF-8 byte truncation/right-padding contract and SplitMix64-v1 with the
specified high-53-bit uniform conversion. Tests cover a deliberately truncated
multibyte suffix, exact 512-byte bounds, standard SplitMix64 vectors, unsigned
wrap and seed/type failures. The reference now also fixes all 11 parameter
tensors, row-major scalar order, explicit Xavier fan-in/fan-out values, zero
biases and a 46,848-value initialization replay digest
`4d239c77…09d1`. The portable reference forward path now implements exact byte
lookup, odd-width same-zero cross-correlation, ReLU/global max pooling, hidden
and output layers, stable label tie-breaking and max-shifted softmax. A sparse
path test fixes the weight layouts end to end. The recipe manifest binds both
reference sources and those semantics. Deterministic validation-only selection
now implements all 40 epoch tie-breaks and the 0.005 margin grid, admitting a
threshold only when at least 116 accepted rows are both raw- and guard-exact;
sealed evaluation inputs are absent. Frozen binary64 training math now covers
max-shifted cross-entropy and scalar AdamW with exact bias correction, epsilon
placement, gradient-then-decoupled-decay order and weights-only decay. The
recipe binds those sources too, and its current file identity is
`aba6e3d7…23ec`. The expanded J2 source suite passes 89/89. No training step,
corpus row, evaluation content or retained model artifact is created.

The future artifact boundary is now executable source rather than prose. It
requires all 11 exact tensors and 46,848 quantized finite parameters, the exact
recipe/preregistration/corpus-release/training-admission/ontology/guard
bindings, a selected epoch in 1–40, a 0.005-grid threshold, at least 116 of 192
accepted validation rows, a replay digest and an exact artifact self-hash.
Unknown optimizer state, changed tensor shape, excess precision, nonfinite
values or binding drift fail closed. Validation still returns deployment false
and requires replay. Four artifact-contract tests form part of the J2 suite;
their all-zero synthetic tensor fixture is schema evidence, not a model.

The replay boundary now requires two separately identified clean single-thread
CPU reproductions with exact equality across all 192 validation records. Every
record must use the frozen case-ID set and ontology, finite ten-decimal
confidence/margin values, a valid guarded interpretation and a boolean
acceptance. The exact record digest and accepted count must match the artifact.
Changed rows, case IDs, labels, counts or duplicate keys fail closed. Three
synthetic replay tests still return deployment false.

The same second audit correctly found that identical replay files are not yet
proof of correctness: the current schema does not recompute labels, guarded
interpretations or threshold acceptance from the exact validation truth, and
epoch/threshold claims are not bound to an input selection receipt. It also
found that full deterministic training remains underspecified without
backpropagation, pooling-tie, ReLU-zero, batch update and gradient-reduction
rules. Artifact/replay code is therefore retained as a schema prototype, not a
release candidate. These P0 gaps must be closed before any training approval.
