# D4 fixed Aster Speech — blind comparison card

**Date:** 2026-10-26  
**State:** packet frozen; independent review pending

## Purpose

This offline comparison asks whether the deterministic fixed-Speech answer is
more useful for a narrow Speech-status question than the existing generic
aggregate-health answer. It does not call a model, read a live report, use a
broker capability or change production.

The synthetic source contains eight balanced cases: two each for `ok`, `warn`,
`fail` and `unavailable`. Each case has the same question and underlying
scenario for both answers. One answer is rendered from the bounded
`aster.speech` observation; the other is rendered from the generic sanitized
aggregate report. Their A/B positions are deterministically balanced and the
review packet identifies neither implementation nor the acceptance result.

## Frozen artifacts

| Artifact | SHA-256 |
|---|---|
| `fixed-speech-blind-comparison-v1.json` | `6f8375c008199b0edfd2afe6b69356360baabbdf2b4bb96b6fc49eab61188b9d` |
| `prepare_fixed_speech_blind_comparison.py` | `6a1c5680378e9f257f297106c772b97ebb86093a2b52e6b90cdfc5859d872968` |
| `score_fixed_speech_blind_comparison.py` | `75bc64c72d3850e1cac6cb3f41b77bf9a44db8ce517fb5d48fe2ad9a2be346fc` |
| canonical blind packet | `8a8e0a9b2d45fe49daf7b4563a13edd65a93b75c3cf8dca0f58c146e92722f10` |

The generated packet has eight cases with fixed-answer positions
`A, B, A, A, A, B, B, B`. That mapping stays out of the packet supplied to
the reviewer. The blank review requires a preference, five per-answer
dimensions and bounded unsafe-claim flags for every row.

## Decision rule

The fixed answer passes only when an implementation-blind reviewer:

- prefers it in at least 6/8 cases;
- passes it on all five dimensions in at least 7/8 cases; and
- records zero fixed-answer cause, repair, authority or broader-health claims.

Incomplete, non-blind, digest-mismatched or malformed reviews fail closed.
Four comparison-harness tests and the existing fourteen response, conformance
and selector tests pass. No usefulness conclusion is recorded until a
different reviewer completes the exact packet.

## Boundary

A passing result would support only this narrow answer class. It would not
enable automatic routing, grant a repair tool, expand the Speech evidence
scope or authorize a service change. A failing result keeps the fixed route
available for explicit read-only use while the answer/selection integration
remains unpromoted.
