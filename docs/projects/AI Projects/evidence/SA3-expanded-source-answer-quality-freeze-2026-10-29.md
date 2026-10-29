# SA3 expanded-source answer-quality packet freeze — 2026-10-29

## Classification

- **SOURCE-ONLY PASS:** a frozen synthetic packet now covers all eight installed
  sanitized SA1–SA3 evidence classes and the existing fair scorer can bind its
  separate answer key.
- **NO LIVE EFFECT:** no model, service, network target, incident store, route,
  tool, credential or production evidence was used.
- **INDEPENDENT SOURCE REVIEW PASS:** the frozen packet, separate answer key,
  runner and fail-closed review boundary were independently accepted without
  changing their reviewed bytes.
- **NOT YET MODEL-QUALIFIED:** no predictions or model-blind semantic reviews
  exist, and no evaluation workload has been registered, booked or run.

## Frozen boundary

The packet contains 20 synthetic sanitized cases, including four mandatory
abstention cases. Every installed evidence class appears in at least two cases:

- fixed Doctor status;
- aggregate Forgejo status;
- fixed gateway health;
- accepted inference health;
- aggregate NetBox network state;
- public gateway configuration identity;
- typed backup protection state; and
- root-published critical gateway log aggregate.

The packet permits no authority, effect, tool call, route or repair. Its key
uses only the eight visible source identifiers. A qualifying result still
requires all 20 predictions, at least 18 complete passes, all four abstentions,
empty effects and a model-blind independent semantic review for every case.

Pinned identities:

- packet SHA-256:
  `d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066`
- answer-key SHA-256:
  `718cf430e0acc945bf0c8025982786935e59a63a601b6217e747494e022cd445`

## Validation

The focused packet, runner, review-receipt and fair-scorer suite passes **23/23**. It proves exact
20-case membership, duplicate-key rejection, packet/key identity binding,
coverage of every source at least twice, four abstention cases, fixed
no-authority/no-effect/no-tools constraints, malformed-key rejection and the
rule that missing independent reviews cannot qualify a result.

The inactive runner is pinned at
`39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351`.
It gives the model only the synthetic prompt, sanitized observations, visible
capability catalogue and fixed no-authority/no-effect/no-tools constraints. It
never loads the answer key, performs exactly one request per case with no retry,
uses strict structured output and records runtime/schema failures as `invalid`
rather than converting them into a safe-looking clarification. The runner is
source only and has not been registered, installed or invoked.

The independent-review manifest pins shared commit
`7717fc6fd10e257f3c58b2ca07eb18c1203cb72e`, the five material file-byte
digests and both canonical artifact digests. Its own SHA-256 is
`fbbb04821a4fc5aa165282e6f49bc84b7d54f7b056e3dc7cc0e013134bb396d7`.
The receipt verifier requires an identified independent reviewer, the exact
commit and manifest digest, ten exact boolean findings and a consistent
pass/reject decision. A false finding cannot be represented as a pass.

## Independent review result

The independent source-only review returned **PASS** against material commit
`7717fc6fd10e257f3c58b2ca07eb18c1203cb72e` and shared review commit
`afa63e0e4d5754e3984a96a4e2b24ec2f1f4e36a`. All five pinned file hashes,
both canonical artifact digests and all ten required findings match. The
receipt SHA-256 is
`d579b2b3346835efb6a9b2f1baa5f9184c9e35d1e2638827c1f13c8eeecaf2f0`.
The reviewer also repeated the focused source-only suite at **23/23** and
confirmed injected transport failures remain invalid, empty-effect results.

This review covers the frozen synthetic material and offline implementation
only. It does not evaluate a model, local-AI service, latency, deployment,
routing or repair, and it grants no operational authority. The retained
[review evidence](SA3-expanded-source-quality-independent-review-2026-10-29.md)
and machine-readable receipt
`services/aster-agent/evals/sa3-expanded-source-quality-independent-review-v1.json`
are the accepted source-review record.

## Next gate

The source-review gate is complete. The next gate is platform registration of
the exact runner and frozen packet as their own hash-pinned Lab Hours workload.
Only after that registration may an execution window be checked and booked.
The full execution and recovery interval must pass the authoritative
reservation check, booking, whole-host lease and shared-lock gates, including
the immediate pre-effect recheck. The run remains no-effect and cannot promote
routing or repair authority.
