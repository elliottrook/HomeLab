# M3 J2 training R1 NO-GO and R2 diagnostic correction — 2026-11-06

## R1 measured result

Jason approved one exact Mac-local J2 training transaction. Attempt `r1` passed
the hash, lock, process, memory and swap admission gates and ran for
approximately 42 minutes. It then failed closed at the transaction worker.

The retained create-only evidence is:

- result path:
  `/Users/jelliott/lab/private-benchmarks/aster-stream-a/j2-training-result-20261106-r1`;
- terminal file: mode-0600 `failure.json`;
- file SHA-256:
  `7aa7d7999d70d3b58476b4b57871a6135489535bff3507b309cff7ce44f2b932`;
- status: `no-go`;
- first failure phase: `training-worker`;
- failure class: `RuntimeError`;
- production changed: false;
- sealed evaluation access: false;
- authority: none; automatic routing: off; deployment: false.

No artifact, model route or production effect was accepted. The owner did not
retry and the `r1` directory remains preserved.

## Diagnostic defect and correction

The worker's first implementation deliberately suppressed child stderr, but it
also collapsed every post-training rejection to one generic `RuntimeError`.
That evidence cannot distinguish a legitimate failure to meet the frozen
validation threshold from an artifact/replay contract error. A blind rerun of
the same deterministic bytes would therefore be unjustified.

The R2 source keeps stderr suppression but handles the preregistered
no-threshold result as a first-class content-free terminal outcome. If all 40
epochs complete but no threshold can accept at least 116 exact validation
rows, it now retains:

- failure code `NO_ELIGIBLE_VALIDATION_THRESHOLD`;
- selected epoch and selected raw/guarded exact counts;
- maximum safe accepted coverage and its best threshold;
- the frozen minimum of 116;
- explicit false artifact, production, sealed-evaluation, authority, routing
  and deployment flags.

The transaction owner copies that exact failure record to the create-only
result path and returns a bounded `NO-GO`; the Mac owner accepts it only when
it is the sole output and all inert-state fields remain false. Unexpected
errors still fail closed.

## R2 readiness

- corrected transaction SHA-256:
  `52ad19a9eda92187779992b27cf0e1ae1c14349e367cf1ed136ac3e3626ddea8`;
- corrected Mac owner SHA-256:
  `4f9e07f789968cf8596c2414745a4a05292fb374617e06b09428155a6bdfd4c4`;
- full J2 tests: 122/122;
- exact input/workload pins: pass;
- fresh Mac available bytes: `4312973312`;
- fresh swap used bytes: `716827525`;
- competing fixed processes: zero;
- R2 output path absent: yes.

Jason separately authorized bounded reruns within the available time. R2 may
run once at the fresh create-only path. This does not authorize overwriting R1,
blind looping, sealed evaluation access, B60 use, service changes, deployment,
routing, tools or promotion.
