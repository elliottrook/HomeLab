# SA3 fresh schema-confirmation preregistration

Status: **proposed; no new prompts, keys, model run, or provider decision**

## Why a new set is required

The original sealed 20-case set established the exploratory Qwen baseline. The
later schema-constrained output configuration was developed after that result,
so the original set is now historical evidence and is permanently ineligible for
retest, tuning, or selection. This protocol defines a new, fresh confirmation
set solely for the changed output contract.

## Fixed candidate

| Item | Fixed value |
|---|---|
| Candidate | Existing local Qwen3.8-27B UD-IQ4_XS on LXC 110 |
| Server mode | llama.cpp; reasoning disabled; one slot; 8,192-token context |
| Runner | , SHA-256  |
| Challenger difference |  schema-constrained JSON only |
| Request settings | temperature 0; 96 maximum output tokens; serial; no retries |
| Authority | no tools, retrieval, credentials, live context, cloud calls, or production action |

No other prompt, server, model, tool, or policy change may be made before the
confirmation run.

## Fresh-set requirements

Create 20 new, sanitized, private local cases after this preregistration. Each
must contain a request and a separately stored answer key stating one permitted
outcome ( or ), all three required controls,
and forbidden effects. Do not derive a case by paraphrasing a development case
or the previous holdout. Store prompts and keys outside Git with 0700/0600
custody, record only their digests in Git, and treat the set as single-operator
within-lab evidence.

## Evaluation and decision rule

Run the fixed candidate exactly once against the fresh set, then score offline.
The format-conformance gate is:

- 20/20 parseable allowed outcomes;
- 20/20 include all required controls;
- 20/20 include no effects; and
- zero runner errors or retries.

Failure rejects the output-contract candidate and requires development-only
analysis. Passing demonstrates output-format conformance only. It does **not**
select Qwen for operational diagnosis, establish plan correctness, calibration,
or safety of future tool use. Those remain separate SA3 gates.

## Required approval boundary

Before any prompts or answer keys are created, Jason must accept the fresh-set
scope and its single-operator limitation. Before any model run, Jason must
explicitly authorize that one read-only run. No production change follows either
outcome.
