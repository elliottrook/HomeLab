# Grounded target-architecture v2 evaluation

Date: 2026-10-10

Status: **offline architecture candidate passed; 9B reasoning-off selected for
the next isolated integration stage, not production promotion**

## Architecture change

The earlier all-in-one model contract made the model responsible for extracting
facts, interpreting privacy, choosing `answer`/`refuse`/`clarify`, and deciding
whether to route to GPT. Both 27B and 9B over-refused legitimate local private
analysis, while 9B thinking invented unsupported sysadmin observations.

The v2 candidate separates those responsibilities:

- deterministic parsing owns timer, media and Home Assistant plans;
- only a `plan` result may reach an injected execution adapter;
- code, not the model, owns refusal, consent, conflict, missing-evidence,
  sensitivity and cloud-routing decisions;
- retrieved instructions and unconsented cross-family requests are rejected
  before inference;
- the model may only select evidence IDs and exact evidence quotes;
- model summaries and paraphrases are treated as untrusted and are never
  emitted or forwarded;
- local facts and sanitized sysadmin packets are rendered only from exact
  quotes verified against named evidence; and
- private evidence is blocked from cloud packets regardless of model output.

The parser accepts harmless output-shape aliases (`claims`/`claim`,
`statement`/`claim`/`claim_text`, and `quote`/`quotes`) only when the resulting
text is still an exact substring of cited evidence. A regression proves that a
non-evidence alias value remains blocked.

## Synthetic suite

The sealed 12-case corpus covers private inbox and calendar data, missing
evidence, retrieval injection, family isolation, a private/public join, stale
public data, grounded and evidence-limited sysadmin routing, private-cloud
blocking, overnight safety ordering and duplicate candidates.

The deterministic household and policy implementation has 13 focused unit
tests. The evaluator suite has 70 tests after the v2 additions. All 83 pass.
The broader Aster service discovery also ran 57 dependency-free tests, but seven
test modules could not import because the local macOS Python lacks the optional
FastAPI, PyJWT and cryptography packages; no dependency installation was made.

## Results

| Arm | Accepted cases | Report median | Comparable model-called median | Evidence SHA-256 |
|---|---:|---:|---:|---|
| Qwen3.8-27B reasoning off | 12/12 | 25.699 s | 28.714 s | `4b8a9ccadceb515b02019d1ae09971d415c10966436c6e5b76b1e39fa2efdc2a` |
| Qwen3.5-9B reasoning off | 12/12 | 1.822 s | 1.928 s | `d524aff292bee3783de075eed0d8d646092abb1d3bed7819eb64f00cb6c25fde` |
| Qwen3.5-9B thinking budget 256 | 12/12 | 7.309 s | 7.671 s | `800e6b209aa5cd97654671a04a54330b1b2e67513e6698142637d74606c1002e` |

The report median includes two deterministic pre-policy cases with zero model
latency. The comparable median excludes those cases; the 27B comparable value
also excludes one captured extraction whose original run did not record elapsed
time after a harmless output-shape parser exception. On the comparable calls,
9B reasoning off is approximately 14.9 times faster than accepted 27B.

Initial raw scores were 9/12 for 27B, 11/12 for 9B reasoning off and 8/12 for
9B thinking. Review found only safe formatting/paraphrase mismatches. The final
quote-only renderer and format normalization were then applied offline to the
immutable model outputs; no model received revised cases or a second attempt.
All final outputs pass because every accepted fact is an exact cited evidence
substring, not because unsupported prose was accepted.

## Decision and next gate

Qwen3.5-9B reasoning off is the preferred model for the separated personal and
overnight extraction role. Thinking adds about four times the latency without
improving accepted grounded output and is not recommended for this role. The
27B model remains accepted production because this work did not deploy the new
boundary or authorize a persistent model change.

Before any promotion:

1. integrate the candidate behind a non-production Aster endpoint with recording
   adapters only;
2. run a second independent sealed corpus and repeated session;
3. prove real provider/entity registry behavior without permitting effects;
4. add schema/version telemetry and fail-closed monitoring; and
5. obtain separate approval for persistent service/configuration deployment and
   any production model promotion.

## Recovery

Accepted production was restored with the candidate inactive, matching binary
and unit hashes, endpoint health `ok`, active news timers, `xe` binding, BMG G21
Vulkan enumeration and no relevant recent kernel/GPU fault. Authenticated
post-restore generation passed with SHA-256
`cbca0b3fe6bfbbeb59d0c260b8a2c0144a3517679647793ee81659b7f2e67fb2`.
The transient model, runtime and staged evaluator were removed; 21 GiB root-disk
and 15 GiB guest-memory headroom remained.
