# M4 outcome lineage exercise — frozen before execution, 2026-09-25

Purpose: validate persisted linkage for fresh measured fixture outcomes. This is
not a new harness adoption comparison. Reuse the four public synthetic M2 cases,
with one execution per case, no warmup or tuning. Register their input/expected
hashes and family IDs, then freeze the experiment and implementation digests before
any fixture runs. Each run must precede its outcome and identify its dataset case,
experiment, source artifact and unique run ID. No model or network access.

Acceptance: four completed outcomes with the expected tool counts; ten events
(dataset, experiment, four runs and four linked outcomes); backup restored against
the original final head. Retain failures without tuning or overwriting the result.
Elapsed milliseconds are observational metadata, not a comparative speed claim.
Baseline and candidate source hashes are intentionally identical: this exercise
has no baseline measurement, aggregate evaluation, promotion or reviewer decision.

Artifact: `M4-lineage/measurement-001.json`. The implementation set in that artifact
pins the evaluator wrapper as well as the Aster source bound by each run. Fixtures
are authored synthetic examples with no independent quality review. Existing M3
results remain separate and are not retrospectively imported as preregistration.
