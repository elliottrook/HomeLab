# M3 J2 training R2 terminal rejection — 2026-11-06

## Decision

J2 is **rejected**. Corrected attempt `r2` completed all forty deterministic
training epochs and reached the preregistered validation threshold gate, where
it produced a content-free terminal `NO-GO` rather than a generic worker
failure.

The failure is candidate quality, not infrastructure. Repeating the same
deterministic corpus, recipe, initialization and source would reproduce the
same result and is therefore closed even though Jason authorized bounded
reruns where a correction justified them.

## Retained measured result

- result path:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-training-result-20261106-r2`;
- terminal file: mode-0600 `failure.json`;
- terminal file SHA-256:
  `e1500d6fa104e91994e40e534b0dfc818c47c37ba5b16a4756db5cef651f3f72`;
- status: `no-go`;
- first failure phase: `threshold-selection`;
- failure class: `CANDIDATE_REJECTED`;
- failure code: `NO_ELIGIBLE_VALIDATION_THRESHOLD`;
- epochs completed: 40;
- selected epoch: 37;
- selected raw exact: 94/192;
- selected guarded exact: 94/192;
- frozen minimum required: 116/192;
- maximum zero-error accepted coverage: 17/192;
- best safe threshold: 0.795;
- artifact written: false.

## Host and safety result

- Mac resource observations: 584;
- minimum available bytes: `4271570944`;
- maximum swap used bytes: `716827525`, unchanged from preflight;
- services stopped: zero;
- production changed: false;
- B60 used: false;
- B60 booking required: false;
- sealed evaluation accessed: false;
- authority: none;
- automatic routing: off;
- deployment: false.

R1 and R2 remain separate create-only evidence directories. Neither may be
overwritten or reinterpreted as an artifact.

## M3 next action

J2's 48.96% exact validation accuracy is below the 60.42% minimum before
confidence thresholding is even considered. Threshold calibration cannot
repair it. The next autonomous M3 work is offline development of a materially
distinct candidate against only the admitted 768-row train and 192-row
validation split. The sealed 32-case evaluation remains inaccessible.

Any successor must receive a new preregistration and exact source/data
bindings. Development results cannot promote a model. A later release
candidate still requires custody, owner training-effect review, clean replay
and independently sealed evaluation before any routing decision.
