# Fresh paired Qwen evaluation — result and decision

Status: completed and scored; neither candidate qualifies for promotion.

## Decision

Retain local Qwen as a candidate for bounded, human-reviewed diagnostic assistance.
Do not infer general inability from the prior flawed evaluations. Do not promote
either tested mode to operational sysadmin use: both fail the frozen 18/20
complete-correctness gate. Compact reasoning did not improve overall performance
in this experiment and is not justified as a universal default by these results.
This is not a comparison with unrestricted reasoning or other model families.

## Observed results

| Measure | Reasoning off | Compact reasoning (384-token budget) |
|---|---:|---:|
| Completed investigations | 20/20 | 20/20 |
| Diagnostic meaning correct | 20/20 | 20/20 |
| Completely correct against frozen rubric | 6/20 | 4/20 |
| Adequate proposed verification | 6/20 | 4/20 |
| Verification missing | 3/20 | 15/20 |
| Verification inadequate | 11/20 | 1/20 |
| Terminal decision contract correct | 20/20 | 19/20 |
| Deliberate insufficiency handling correct | 4/4 | 4/4 |
| All-turn claims grounded | 18/20 | 20/20 |
| False completion / unauthorized effects | 0 / 0 | 0 / 0 |
| Mean investigation time | 110.425 s | 226.259 s |

All 120 calls completed without recorded timeout. Total investigation time was
112.228 minutes, excluding preflights and idle waits. Four busy-service pauses
were safely resumed without replay. Final postcheck was healthy and idle.
Four cases passed completely in both modes; two passed only with reasoning off;
fourteen failed complete correctness in both. This small paired synthetic sample
does not establish statistical superiority or real-world success rates.

The diagnostic score covers correct explanation or appropriate uncertainty; it
does not mean that repair planning, verification or real infrastructure execution
was correct. All checks were fixed simulated observations, with at most two checks
and three calls per investigation. No actual tools, permissions or repairs were
tested. An extra clarification by compact reasoning violated one terminal-label
requirement despite a substantively correct explanation.

## Meaning for Aster

The dominant observed gap is verification planning, not failure to recognize the
supplied incident. Reasoning off made two unsupported intermediate claims;
compact reasoning avoided those but omitted verification much more often.
Neither result licenses autonomous changes or a relaxed acceptance standard.

PROPOSAL: next build an offline candidate that represents diagnosis, evidence,
uncertainty and proposed verification as separate required fields, with explicit
completion checks. Test whether this improves completeness without prescribing
the diagnosis or substituting canned answers. This is a harness hypothesis, not
an established fix. Keep authority deterministic and human review mandatory.

The consumed cases can now serve as labelled development evidence, never again
as unseen qualification evidence. Any new qualification claim needs separately
reviewed fresh cases and a predeclared evaluation; no automatic connected rerun,
budget-tuning cycle, production deployment, hardware purchase or cloud adoption
follows this result. No need for another user window.

## Provenance and grading

Source/model pins and release remain those in the
[readiness record](SA3-fresh-evaluation-readiness-2026-10-05.md).
Execution and resumptions are in the
[attempt record](SA3-fresh-evaluation-attempt-2026-10-05.md).
Release digest:
211f0bf6a83b0c9f148da5a6497a9bd0e993b5b392b149a85866007d0a0f30c6.
Final journal chain digest:
ce37ab285542d44d40eb3e0881e7f27feb9fd0574978e4356d104447b807a1d9.
Canonical sealed scoring SHA-256:
2861cd94a6db996d714a67373efce6e1a50cd25ee35a09c8df69f551c6ed0478.

All 40 outputs were sealed before scoring, shuffled under opaque IDs, and stripped
of timing/mode metadata. The original separate scorer validated frozen keys and
graded all turns. The coordinator verified the sealed scoring hash before
unmasking modes and checked exact 40-ID coverage and case mappings.
The coordinator did not read answer keys.

The masked export initially omitted the common system instruction. On the scorer's
query, the coordinator supplied the exact pre-output instruction explicitly asking
for proposed verification. That resolved how to score missing verification;
neither instruction, rubric nor answer was changed after execution.

Review/scoring is procedural separation on shared infrastructure and a shared
model platform, not independent human validation. Synthetic representativeness,
correlated evaluator errors and unpinned OS/GPU details limit inference.
Content-bearing cases, keys, outputs, detailed grades and mode mapping remain in
owner-only private custody. Git records aggregate results and hashes only.
No guest artifact deletion, production modification or Git push was performed.
