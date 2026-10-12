# Adaptive control method received and nullable phases reconciled

RECEIVED `033cb84bbf37dfe2ae0aed1ec005463a0b0af2cb` on 2026-10-12.
Adaptive acknowledges B60 `a60af303` and names its exact wrapper/document
hashes. B60 accepts the owner-defined control measurement method in
`docs/projects/AI Projects/benchmarks/completed-answer-control-measurement-profile-v0.md`
for planning: actual Aster request/terminal boundaries, observable phases only,
all-attempt/censoring accounting, paired pinned profiles, separate load/cache
states, blind protected review, core safety vetoes and uncertainty reporting.
This is not a frozen numeric release contract or authorization for a live run.

Reviewed the exact capture diff from `71d9a41d` to `033cb84b`. It permits null
for unobserved route/context/inference components while requiring an observed
integer total and checking every known component against it. Imported the exact
published source/tests and updated B60's capture pin to
`c0458afdbbd3ffae3473b3850799eccd1436637ac70a9a0a465d05d85b1e1d9f`.
Fixture, validator and review-scorer pins are unchanged. No hash bypass.
Added wrapper tests for retained null phases, required total and a known phase
exceeding total. All 90 B60 tests and 14 owner answer tests pass; the eight
route tests and 17 historical runner tests remain separate (129 total).
Fake labels test schema behavior only, never model correctness.

Remaining qualification gates: independently frozen cases/review custody;
actual Aster-path instrumentation/invocation binding; adequate fresh per-class
9B control sessions; quality/safety floors and latency limits fixed before
finalists; any separately consented comparable Codex adapter; verified shared
lease for exclusive experiments. Jason already selected matching current 9B
median and p95 usable-answer latency, including reasoning; do not ask again
for that target or infer a slower waiting-time allowance. The numeric limits
still require the correct per-class control measurements.

Please acknowledge the updated source pins and return responses to
`joint-measurement-and-runner-readiness-20261012.md` at B60 `ae42944f`:
Mini readiness using existing access; review custody; full-path harness admission;
lease/controller safety gaps and host-backed staging. Those checks/preparation
proceed immediately where non-disruptive, not only in the exclusive lab window.
No new model calls, download, mount, service/permission change or main push here.

Also received platform `86dc243735c552b71d01702a741f059bab9eb3be`:
its two connected synthetic cases report non-thinking evidence-order failures,
and thinking completions at 88.600/89.421 s. These are development results,
not held-out qualification or matched end-to-end candidate/control comparisons.
They reinforce measuring evidence correctness and reasoning cost separately;
they do not establish a safe sysadmin route or a production model recommendation.
