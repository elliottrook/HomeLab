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

The combined admission validator is now source-complete as well. It cross-binds
the exact corpus-release summary, owner acceptance, frozen recipe, corpus and
evaluation receipts, two distinct pinned signer keys, and the signed
zero-intersection receipt. It rejects reused roles/keys and any release,
owner, evaluation or disjointness mismatch. Even a complete chain advances
only to `eligible-for-owner-training-effect-review`; training authorization,
sealed-evaluation access, routing, authority and deployment remain false. The
expanded source-only J2 suite passes 62/62.

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
wrap and seed/type failures. The expanded J2 source suite passes 67/67. No
weights, corpus rows, evaluation content or model artifact are created.
