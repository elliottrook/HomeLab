# M3 J2 label-review validator boundary — 2026-11-04

## Decision

**SOURCE READY; NO J2 LABEL REVIEW OR TRAINING CLAIMED.**

The source-only validator closes the missing per-row review proof identified by
the J2 custody audit. It binds one review to the exact 960-row corpus bytes,
the preregistration manifest, the fixed ontology and distinct declared corpus
custodian/reviewer identities. Every source row must retain the preregistered
48-train/12-validation balance for each of the 16 coherent labels.

All 960 review rows must be explicit, unique and complete. An `accepted` row
must preserve its source label; a `corrected` row must select a different known
label. Any unresolved or corrected row keeps the corpus ineligible. The review
is self-hashed and its content-free summary records authority not granted and
automatic routing off.

The combined J2 preregistration, custody, corpus and label-review suite passes
24/24. This validates the schema and fail-closed behavior with synthetic test
fixtures only. No corpus, real review, evaluation set, booking, model call,
training, route effect or deployment was created.

## Remaining custody limit

Distinct identity strings and self-hashes do not authenticate independent
people or processes in a shared worktree. A later release boundary must bind
externally controlled signer fingerprints (or equivalent separate-account
evidence) and a genuine sealed evaluation path. The corpus validator now pins
the exact eight exposed reference names, byte digests, normalized-set digests
and counts plus the frozen ontology; the six raw calibration corpora remain in
human-controlled custody. Until the remaining gates close, this validator is
necessary evidence plumbing, not proof that independent custody occurred.
