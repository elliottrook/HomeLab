# D4 development-corpus qualification boundary — 2026-10-19

## Result

The offline D4 corpus validator now separates **structural validity** from
**qualification eligibility**.  This prevents the twelve-case Codex-authored
extension draft from becoming evaluation or promotion evidence merely because
it satisfies the JSON field contract.

The new qualification check requires all of the following:

- status `development_intake_complete`;
- every case attributed to Jason's review; and
- no provenance marker that declares the extension unreviewed.

The validator exposes these as separate command modes.  Its default checks
only structure; `--qualification` invokes the stricter human-review boundary.
This makes the intended gate explicit for a future evaluation launcher instead
of relying on a caller to interpret status text.

The current draft fails closed on the first and third conditions.  Its
historically reviewed fields remain intact, but its proposed repair scope,
postcheck and latency fields remain development material until Jason reviews
them.  This is an offline evidence-custody guard; it does not approve the
draft, connect a tool, run a model, or promote a sysadmin role.

## Verification

- focused validator and draft-boundary suite: **10/10 passed**;
- structurally valid draft: accepted for offline schema tests;
- same draft at the qualification boundary: rejected with only the two
  expected unreviewed-status/provenance errors;
- completed synthetic fixture with Jason review markers: accepted;
- synthetic non-Jason reviewer: rejected.

## Practical implication

Stream A can continue building and testing the corpus format without allowing
AI-authored labels to count as independent evidence.  Human review, held-out
cases, real read-only tool behavior and the M1 authority gate remain open.

