# M3 — tool-loop and routing smoke results

Date: 2026-09-25. Status: **controlled comparisons retained; M3 overall open**.
Decision: retain Aster and the explicit-rule routing baseline. No production
migration, model request, new dependency installation or remote write occurred.

## Tool-loop conformance and overhead

The [frozen plan](M3-tool-loop-plan.md) and
[fixture manifest](../../../../scripts/aster-adaptive/fixtures/tool-loop-v1.json)
cover eight cases. The final manifest added revocation and expiry between reads
before any comparison was run. Both actual Aster chat-loop source and PydanticAI
passed every case in two fresh-process repeats. Accepted fixture-call sequences
matched the literal expected list; no prohibited fixture action occurred.

| Case | Aster boundary attempts / rejected | PydanticAI boundary attempts / rejected |
|---|---:|---:|
| One read | 1 / 0 | 1 / 0 |
| Two sequential reads | 2 / 0 | 2 / 0 |
| Invalid type, then repaired | 2 / 1 | 1 / 0 |
| Malformed JSON, then repaired | 2 / 1 | 1 / 0 |
| Unknown tool, then answer | 0 / 0 | 0 / 0 |
| Repeated invalid calls | 0 / 0 | 0 / 0 |
| Revoked between reads | 2 / 1 | 2 / 1 |
| Expired between reads | 2 / 1 | 2 / 1 |

Repeated invalid calls terminated as failures within four scripted responses for
both implementations. Repaired malformed calls reached one accepted fixture action
in both. PydanticAI rejected malformed arguments before boundary dispatch, while
Aster passed them to the independent strict validator, which rejected them.
Both retained current authorization/expiry checks outside the harness.

PydanticAI demonstrates earlier schema rejection, but the deterministic boundary
must still validate and authorize requests. These fixtures therefore establish no
safe removal of that component and no maintenance benefit sufficient to migrate.
PydanticAI's schema behavior remains useful evidence for a future structured-tool
use case, not permission to weaken adapters.

| Ordinary case | Aster p95 ms, runs 1 / 2 | PydanticAI p95 ms, runs 1 / 2 | Scripted response steps |
|---|---:|---:|---:|
| One read | 0.030 / 0.026 | 1.699 / 1.657 | 2 |
| Two sequential reads | 0.033 / 0.031 | 2.187 / 2.247 | 3 |

Each timing row has ten warmups and 200 retained samples per run. Setup (AST
extraction or Agent construction) is excluded from these loop-only timings for
both candidates. Do not compare these directly with the preload profile, which
included Agent construction. The baseline's Lab Operations and initial payload
are fixture stubs, and its response cap is explicitly four. No actual model cost,
prompt-token or answer-quality comparison is implied. Full raw aggregate records
and evaluator/source/dataset digests are in [M3-tool-loop](M3-tool-loop/aster-1.json).

## Separate routing experiment

[Preregistered routing plan](M3-routing-plan.md) compares fixed lexical rules with
a small dependency-free TF-IDF nearest-neighbour model. The frozen corpus contains
300 presentation variants from 30 semantic families, split 10 families/100 examples
each for train, calibration and test. All copies of a family stay in one split.
Training vocabulary/IDF uses train families only. Calibration chose threshold 0.4
using the declared exact-match criterion and higher-threshold tie break.

| Route proposer | Test-family exact | Example exact | Prohibited-label violations |
|---|---:|---:|---:|
| Fixed rules | 10 / 10 | 100 / 100 | 0 |
| TF-IDF nearest | 1 / 10 | 10 / 100 | 0 |

The challenger abstained on eight families and misrouted “Set it for later” to
timer rather than clarification. It matched only the calendar/web/local-join
family. Its calibration result was 5/10 families; that did not generalize to this
small held-out set. No threshold, training examples, rules or labels were modified
after viewing the test results.

**These are synthetic smoke results, not independent production accuracy.** The
same implementation session authored the rules and corpus; design bias is possible.
Ten prefixes are formatting variants, not ten independent intents. There are only
ten independent held-out families and no human-gold labels. Do not quote 100/100
as evidence of general household reliability. The next evaluation needs new,
independently reviewed families and realistic ambiguity/private-data constraints.
All route outputs have `authorization=not-granted` and null confidence. Hypothetical
timer, home and calendar labels do not declare those services available to Aster.

Machine-readable results, calibration choices and every family prediction are in
[routing smoke evidence](M3-routing/smoke-v1.json). Four additional isolation tests
verify split counts, train-only vocabulary, explicit local join and no permission
grant. The normal adaptive suite now has **30 passing tests**.

## Resume

- Preserve negative results. Retain Aster and rules; no migration is justified by
  the current evidence. LangGraph still has no demonstrated requirement.
- M3 still needs representative independently reviewed routing labels and pinned
  local-model compatibility/quality/resource evidence. Synthetic fixture results
  cannot complete that production-facing gate.
- Prepare the next read-only inference measurement envelope only after checking
  current serving load, dependency consumers, budgets and overlap with B60 Stream M.
  Do not modify inference settings or borrow that project's authorization.
- M4's local evidence-store/restore work can proceed independently, using these
  retained result records. Keep proposal, evaluator and promotion authority separate.
- M1 independent security review, approval trust-base resolution and approved
  corrective deployment remain open. No connected pilot may rely on the undeployed
  candidate. Any new push requires separate explicit authorization.
