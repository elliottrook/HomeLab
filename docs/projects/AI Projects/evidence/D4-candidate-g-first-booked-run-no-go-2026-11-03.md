# D4 candidate-g first booked run NO-GO — 2026-11-03

## Terminal result

**TIMED TEST: NO-GO. Do not retry the spent booking.**

Booking `aster-stream-a-sa3-envelope-20261103-1300` claimed once at its exact
start and failed after 72 seconds. Root-custodied terminal evidence records:

- state `no_go`;
- first failure phase `owner-transaction`;
- failure code `PRODUCTION_RESTORATION_INVALID`;
- terminal `production_restored=false`;
- owner stdout empty;
- owner stderr SHA-256 `003bf691…be3e`.

The traceback places the actual first failure earlier, in fixed-source
preflight: `systemctl is-active epub-narration-worker.timer` returned nonzero
while the legitimate multi-day EPUB worker was `activating`. The generic probe
wrapper raised before the drain controller or candidate transaction began.
The reserved-runner postcheck repeated the same timer-only rule, which explains
the terminal restoration flag; it does not mean a drain occurred.

## Practical impact and recovery proof

No model request, listener, drain, lease or candidate result was created. The
attempt directory contains only attempt/terminal and owner stdout/stderr. The
lease is exactly `ready`; drain state, drain lock and shared operation lock are
absent; no candidate process remains. Aster Agent, accepted llama/SYCL, Speech,
`pvescheduler` and `pvestatd` are active. The accepted llama service has zero
restarts. The EPUB worker remains in its ongoing `activating/start` state.

The booking is failed and terminal. It is not eligible for a manual start or
same-booking retry.

## Deterministic correction

Platform commit `3a27c235` changes only the fixed source and final validator.
Both now accept either the timer waiting or the worker active/activating, while
rejecting a failed worker or the absence of both. Timer enablement is not a
health requirement because the EPUB project deliberately disables its timer
while one multi-day worker owns the queue.

Proof is 74/74 local full-inference tests, 12/12 local reserved-runner tests,
39/39 focused target-Linux tests and a read-only probe of the live state returning
`epub_candidate_healthy=true`. Candidate source hashes and rollback boundaries
are frozen in the platform correction card. Nothing was installed or activated.

Platform commit `03ed07fc` adds the exact inert installer. It checkpoints both
predecessors, requires a ready lease and absent shared state/locks, replaces
only the two corrected files, validates hashes/imports and rolls both back on
any uncertainty. The combined correction/installer suite passes 42/42. The
installer is inert without `--apply` and has not been invoked.

The next effect is an inactive two-file installation with exact predecessor
checkpoint and rollback. Only after that target proof may a fresh Lab Hours
booking be considered. The correction does not authorize a retry, service
restart, EPUB interruption, model call, routing or promotion.
