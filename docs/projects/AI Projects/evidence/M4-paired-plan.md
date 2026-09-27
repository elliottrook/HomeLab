# M4 paired evidence plan — frozen before execution, 2026-09-25

Compare the existing direct Aster source slice with its validated fixture adapter.
Use the four unchanged synthetic M2 cases, ten measured repetitions per role/case
and two discarded warmups. Alternate baseline/candidate order each repetition.
These are four authored families, not 40 independent quality examples. This is a
persistence and controlled-overhead guardrail exercise, not a harness adoption test.

Before running fixtures, retain dataset and experiment records, exact source hashes
and a paired-plan event. Register each measured run before execution. Each pair
references the baseline and candidate outcome events. Both timers cover payload
construction, serialization and Outcome creation; source loading, run registration,
ledger writes and aggregation are excluded. The frozen evaluator manifest binds
both wrapper code paths; the common harness hash binds the extracted Aster source.

Acceptance per case: both roles must match every expected completion/tool-count
label and fixture-conformance status; candidate p95 minus baseline p95 must be at
most 5 milliseconds. Nearest-rank p95 on ten observations equals the maximum.
Every case must have exactly ten pairs, with no reused or omitted outcome events.
A family passes only when every case in it passes. Verdict and family totals must
be derived from retained outcomes, not supplied independently. Finalization blocks
new measurements under the same experiment. No automatic review/adoption follows.

Retain the result even on guardrail failure, without tuning or overwriting it.
Restore the ledger against its final head. No model requests, private collection,
production readers, credentials or broker use. Network connections are blocked.
Output: `M4-paired/measurement-001.json`. Operational retention and authenticated
review are outside this offline exercise and remain open gates.
