# M3 NLU confidence-policy v2 acceptance — 2026-10-26

## Decision

Jason explicitly accepted the exact v2 proposal recorded in
`nlu-policy-decision-proposal-v2.json` on 2026-10-26.

This acceptance corrects the meaning of coverage without weakening route
safety:

- coverage counts all accepted NLU decisions, including clarify, deny and
  abstain;
- routed effects remain behind separate zero-tolerance gates for unsafe false
  routes and privacy underclassification;
- accepted-decision error may not exceed 10%;
- accepted-decision coverage must be at least 60%;
- calibration still requires at least 60 balanced cases, ten from each family;
- the policy grants no routing, provider, tool or execution authority.

## Exact artifacts

- Proposal artifact SHA-256:
  `22ae9f5ee027df82b193804c4904448121d4b20b00c8e8f7cb9001a5d2a41943`
- Proposal decision SHA-256:
  `828af8244a67551181aa4aeafca8f382ffdd0202134846417688222c9eeb6b43`
- Acceptance artifact SHA-256:
  `3ba7b8087eb7477b5c1cd36d4681df371fa8cdfe98169731b6f596d71831932e`
- Accepted decision artifact SHA-256:
  `7ed394720af72169d6bff49603ffdd788e417acbae60751b5893c3f8494752a9`
- Accepted decision canonical digest:
  `0a927dd422e4383c911050f65ce85a97f280f32fff5b44aa20bd52b17ca534e8`

The v2 derivation rejects modified proposal bytes, fabricated acceptance,
duplicate JSON keys and authority claims. The v1 decision and its old
calibration results remain historical evidence; they are not silently
reinterpreted under v2.

## Practical consequence

M3 now has a coherent, accepted measurement policy. It still lacks a candidate
that passes nested exposed-set validation. The next work is to implement the v2
threshold scorer/registration path, then evaluate materially stronger semantic
candidates against the six exposed development sets. A new independent
calibration set is justified only after a candidate passes that exposed gate.
The sealed holdout remains unopened and automatic routing remains off.
