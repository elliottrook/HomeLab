# M3 — 9B/SYCL routing compatibility preflight

> Prepared 2026-10-12. **BLOCKED; no inference run authorized by this card.**
> This is an engineering check of a proposed Decision response, not a router
> quality evaluation, calibration set, sysadmin qualification or release gate.

## Decision question

Can the currently accepted local 9B/SYCL service return a syntactically valid,
bounded capability proposal for simple synthetic requests, without granting a
tool or sending private context? If it cannot, do not spend a later lab window
on a larger local-model routing comparison. If it can, the result permits only
a separately preregistered, human-labelled read-only shadow proposal.

## Frozen input and comparison

Use the 30 **synthetic development** families in
`scripts/aster-adaptive/fixtures/routing-families-v1.json` at SHA-256
`c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec`.
One request per family, in file order, with no presentation variants. These
examples and their expected capabilities have been visible during development;
they are **not** an independent holdout. The intended comparison is the
existing CPU-only deterministic selector, pinned by its v2 definition, applied
to these same 30 texts by a yet-to-be-reviewed adapter. The current probe's
12 fixtures are different; its results cannot be substituted for this
comparison. Report agreement and disagreements descriptively, never as an
accuracy estimate. The closed S1 personalized corpus remains untouched and
must not be substituted or used to tune this check.

The model receives only the request text, frozen capability names and a fixed
output schema. It receives no expected labels, credentials, tool definitions,
personal records, system reports or route feedback. There is no tool executor.
Output is a `status` of `plan`, `clarify` or `abstain` and a deduplicated set of
capability IDs from the frozen fixture vocabulary; any other field or ID is an
invalid output. A proposal is never authorization. `deny`, privacy/locality and
permission decisions remain deterministic and are **outside** this probe.

## Measurement and stop rules

Run serially, at most 30 model requests, one attempt per family, no retry and
one server slot. Cap each response at 256 generated tokens and the entire run
at 20 minutes; stop sooner on the first unexpected server, privacy or schema
failure. Record per-case validity, exact capability/status match, extra or
missing capability, abstention, elapsed request time and any non-200 or
truncated response. Report p50/p95 only if all 30 attempts complete. Record
model/runtime identity, service health and source hashes immediately before
and after. Do not report a calibrated confidence: none is measured here.

The engineering threshold for a *next experiment proposal* is 30/30 parseable,
schema-valid responses, zero forbidden capability IDs and no server failure.
Exact-match counts are descriptive; passing the engineering threshold cannot
promote a model route. Failure retains the result and rejects this particular
interface until a new versioned hypothesis is reviewed. No production setting
changes, so rollback is simply to end the probe and retain the accepted
runtime. If the service or other AI consumer degrades, stop and yield the slot.

## Execution gate still missing

Before changing this card to **READY**, freeze and locally test an exact runner,
schema/prompt, output custody and a credential-safe way to call the existing
private endpoint without printing or placing its API key in model context,
arguments, logs or Git. Pin the installed model artifact and llama.cpp build;
the 2026-10-11 observation identified Qwen3.5-9B Q4_K_M on llama.cpp b11429
SYCL FP16 but is not a current preflight. Verify the active whole-host lab
lease, completed backup chain, no competing B60 experiment, restoration
deadline, available slot and healthy Aster before any call. Jason will supply
exclusive lab time later; the former scheduled window is paused. A clock time
alone is insufficient.

Retain content-free timing, route and validity records in Git. Any raw model
response is synthetic-only but still needs an explicit local custody path and
review before retention. Capture the exact run identity and hashes; do not
rewrite a failed result or silently rerun it. A later representative quality
test needs new, independently accepted labels and its own evidence threshold.
