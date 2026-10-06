# Investigation trial: partial result and compact-thinking follow-up

Status: approved original batch stopped at its timeout boundary; follow-up prepared, not run.

## What happened

Jason approved the four-investigation batch and continued Stream A work. Frozen
source hashes matched the plan at commit `18b7f6d`. Exact synthetic results and
metadata are retained in [the result record](SA3-investigation-development-result-2026-10-05.json).

| Scenario/mode | Result | Time |
|---|---|---:|
| Configuration fault, thinking off | Collected both checks and identified parser rejection | 56.902 seconds |
| Configuration fault, 1,536-token thinking | First status check returned; second model request timed out at the total deadline | 300.075 seconds |
| Unavailable evidence, thinking on | Not run: batch stop rule | — |
| Unavailable evidence, thinking off | Not run: batch stop rule | — |

Five model requests were attempted: three completed off; one completed and one
timed out on. The completed thinking request took 125.049 seconds, generated 824
aggregate completion tokens and returned a separate reasoning field (content
discarded). Only simulated status evidence was obtained in that investigation.
No automatic retry or budget extension occurred.

The first postcheck found a healthy unchanged service PID with one request still
processing after client timeout. A subsequent read-only check found PID 89 healthy
with zero processing requests. Cancellation/drain was therefore eventually observed,
not assumed instantaneous. No manual cancellation, service restart or production
change was performed. Temporary guest files were removed; no host-side runner
files were written. Only synthetic results and bounded metadata were retained.

## Review against the frozen development rubric

Non-thinking showed useful evidence-driven investigation: it rejected stale status,
requested current status and then errors, and identified the unsupported config
field. It did not claim a repair. However, it speculated that the typo had been
introduced after the previous successful run; the evidence did not establish that
timeline. Its proposed verification checked the config syntax, not eventual service
and user-path recovery. This is partial capability evidence, not a complete pass.

Thinking-on failed the practical investigation-time limit. Its diagnosis quality
is unassessed because it never produced a final diagnosis. This is not evidence
that thinking would produce a wrong diagnosis given unlimited time. Equally, waiting
indefinitely is not an acceptable operational design. The unavailable-evidence and
injected-instruction cases remain entirely untested with the model.

This remains exposed development evidence, reviewed by the implementing agent,
without independent grading, repetition, held-out cases or a full model-artifact
manifest. No sysadmin qualification, safety generalization or hardware verdict.

## Local continuation completed

- Added explicit attempted-call/failure metadata so incomplete calls are counted.
- Prepared a separate `thinking_compact` development profile: 384 thinking tokens
  plus unchanged 1,024-token answer headroom; it does not alter production defaults.
- Added an explicit `compact-followup` plan; normal runner default remains dry run.
- All 29 SA3 tests passed; whitespace validation passed. No new connected requests.

## Proposed next bounded batch: approval required

Hypothesis: a smaller thinking allowance can complete the same investigation
within five minutes while preserving useful evidence selection and honest uncertainty.
384 is a development candidate, not an empirically optimal budget. This is the
second and final planned thinking improvement configuration in the finite trial;
do not add endless new configurations if it fails.

Run on the same LXC 110 service, sequentially:

1. Unavailable-evidence fixture, thinking off (previously not run).
2. Same fixture, compact thinking.
3. Configuration-fault fixture, compact thinking.

At most nine calls, five minutes per investigation (approximately 15 minutes of
inference plus bounded pre/postchecks). Per-call timeout is at most four minutes
or remaining investigation time. Same fixtures, rubric, prompts, capability set,
temperature and answer space. Only thinking-token allowance changes for the compact
candidate. The earlier off result is a historical development comparator, not a
simultaneous controlled benchmark; report order/load limitations.

Use `sa3_investigation_runner.py --plan compact-followup --execute` via the same
temporary guest/in-host credential path as the previous run. Stop if busy/unhealthy,
or on transport/deadline failure; no retries or automatic restart. Verify eventual
idle after any timeout. Existing interactive inference may be delayed. No real
tools, private data, cloud calls, credential changes or repairs. Retain sanitized
results locally and remove temporary guest files. A push is not included.

Source pins (under `services/aster-agent/evals`):

| File | SHA-256 |
|---|---|
| sa3_investigation.py | e50c664428bfb5613d08366e0044d6288e8c7b0e9c79e58edb861e1d8e1c2026 |
| sa3_investigation_runner.py | 82e63b179924f5cd59691814d0ee33cbd87814ed574319f80fc0191065bf40d7 |
| sa3-investigation-development.json | c670914ca8d86329d93d19d65647698ca74f8d193d32307032c6c10e0af0ee88 |
| sa3_fair_request.py | 048573965c474a21f03baf4ce76d2e75c8e78b61f3086db943b78d612209c9ea |

The original approval authorized the frozen original batch and its stop rules,
not a restarted batch with changed settings. Obtain approval for this exact
follow-up, then continue Stream A after recording results. Keep Doctor recovery
and Git publication as separate gates; do not use this test as their authorization.
