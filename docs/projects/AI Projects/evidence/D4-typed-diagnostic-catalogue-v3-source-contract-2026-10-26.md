# D4 typed diagnostic catalogue v3 — source-contract result

**Date:** 2026-10-26  
**Scope:** offline source and synthetic tests only  
**Effect:** none

## Why this work was needed

The first fixed Doctor capability is deliberately limited to
`aster.agent_inference`. The ordinary aggregate report cannot safely name a
second capability: its bounded rows all use the generic display name
`HomeLab Doctor`, while the human summaries are explicitly excluded from
model authority. Selecting a future diagnostic from those summaries would
reintroduce free-text interpretation at the trust boundary.

## Implemented contract

`services/aster-agent/diagnostic_catalogue_v3.py` now defines a separate,
source-only schema-3 catalogue contract. It does not replace or widen the live
schema-2 path.

The contract:

- accepts only an explicit closed allowlist of stable check IDs;
- binds all events to one 32-character run ID and the exact aggregate digest;
- emits every allowlisted check exactly once in deterministic order;
- maps a missing event to `unavailable`;
- rejects unknown IDs, duplicates, cross-run events, duplicate JSON fields,
  malformed states and severity contradictions;
- carries no human summary or model-visible free text; and
- lets a consumer select exactly one fixed check while rejecting an absent,
  duplicate or digest-mismatched catalogue.

This supplies the reusable contract needed for multiple source-owned checks.
It does not declare that any second production check exists. A new live
capability still requires its producer to emit a stable ID, a fixed consumer
for that one ID, an independently reviewed deployment and its own effect gate.

## Validation

The focused schema-3 suite passed **6/6**. The combined catalogue and existing
fixed-Doctor boundary suite passed **28/28**. Python compilation also passed
using a temporary bytecode cache inside the permitted temporary area.

## Result

**PASS for the offline source contract.** The current live fixed Doctor
capability remains unchanged and retains authority `not-granted`. No service,
schedule, identity, grant, route, model request or production file changed.

The next D4 task is to choose a useful real producer check with a stable,
source-owned ID and build its source event and fixed projection against this
contract. The generic aggregate rows are not sufficient evidence for that
choice.
