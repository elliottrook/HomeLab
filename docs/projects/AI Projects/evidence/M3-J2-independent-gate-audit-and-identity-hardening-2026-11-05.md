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

The complete source-only J2 suite passes 54/54, including explicit rejection
of leading/trailing whitespace, case variants and embedded spaces. This is a
source validation improvement only; it is not evidence of external custody.

## Next autonomous work

Build dependency-free validators for a cryptographically or externally
verifiable proof envelope, an exact corpus/evaluation zero-intersection proof,
and one combined admission object. Synthetic fixtures may exercise those
contracts, but only evidence from the separately controlled custodians can
satisfy the real gates. Training remains a later, separately authorized effect.
