# SA3 evaluation preregistration — starting corpus boundary

Date: 2026-09-28
Status: **development-only preregistration; no Qwen configuration run**

## Existing material assessment

`services/aster-agent/evals/sysadmin-graduation.json` contains 14 established
advisor/read-only graduation prompts and `sysadmin-generalization.json` contains
7 paraphrase/boundary prompts. They retain useful safety and provenance
regressions, but neither suite captures an evidence-gathering incident loop,
competing hypotheses, bounded follow-up selection, diagnostic latency or a
verified outcome. They cannot be relabeled as the 20-case SA3 holdout.

The following 12 existing cases are frozen as an initial **development-only
regression slice**:

| Case | Role in SA3 work |
|---|---|
| `runtime_roles`, `network_addressing`, `stale_backend_trap` | current-runtime identity and stale-state discrimination |
| `authority_conflict`, `provenance_behavior` | evidence/authority handling |
| `b60_diagnosis`, `bounded_live_health`, `monitoring_layers` | bounded diagnosis and health evidence |
| `backup_recovery_order`, `missing_fact` | recovery ordering and abstention |
| `unsafe_firewall_request`, `credential_boundary` | authority and secret boundaries |

`rack_uncertainty` and `knowledge_prompt_injection` remain regressions but are
not part of the twelve-case slice. The 7 generalization prompts remain sealed
from implementation tuning where practical, but they are **not** SA3 holdouts:
they have no independent incident labels or diagnostic rubric.

## Required incident corpus before any model comparison

Create 12 sanitized development incidents and at least 20 independently reviewed
holdout variants. Each needs an immutable manifest with: incident family,
symptom, allowed observations, evidence timestamps/age, expected discriminating
check(s), permissible diagnosis or escalation, forbidden effect, repair scope
if any, expected postcheck, and a latency protocol. Store answer labels outside
the model's retrieved corpus. Do not use raw logs, credentials, private chat or
unreviewed service output.

The approved families remain: ARR second login; Doctor parser/schema crash;
Paperless IP collision; NetBox guest-reboot startup; B60 software rendering;
DNS asymmetry; missing/interrupted backup; Jellyfin authentication change;
copied-audio budgeting; stale inventory; and ambiguous ownership. A holdout must
change causal detail or use a later incident so retrieval cannot simply repeat a
known repair.

## Configuration and decision rules

The current Qwen non-thinking baseline remains the only measured configuration.
Before a new run, freeze its model/server revision, context, tool/observation
budget, response limit, temperature, warm/cold protocol and shared-service load
measurements. At most two intentional local improvement configurations may be
run. Do not enable reasoning merely because the UI displays it; verify actual
llama.cpp controls and account for its latency/token use.

Only after the corpus is frozen may the team compare Qwen baseline, at most two
local improvements, and—if necessary—a separately approved OpenAI sysadmin
adapter using the identical sanitized evidence and rubric. Existing advisor
scores, the one Doctor canary and source-level tests do not select a provider.
