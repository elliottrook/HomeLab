# SA3 EPUB admission correction card — 2026-11-03

## Decision

Source correction is **PASS / inactive-install ready**. Installation, activation
and a fresh booking remain separate effects.

## Observed failure

Booking `aster-stream-a-sa3-envelope-20261103-1300` claimed once and failed
closed before drain or model work. The fixed source used `systemctl is-active`
on `epub-narration-worker.timer`; the legitimate ongoing transcription state
was timer `inactive`, worker `activating`. `is-active` returned nonzero, so the
generic command wrapper raised before the bounded EPUB message. The owner made
zero model requests and began no drain.

The reserved runner's postcheck repeated the same incorrect timer-only rule and
therefore recorded `PRODUCTION_RESTORATION_INVALID`, although current bounded
checks found Aster Agent, accepted llama/SYCL, Speech and Proxmox daemons active,
the EPUB worker still activating, and no candidate process, lease or shared
operation lock.

## Exact source correction

Only the source producer and final validator change. Both now accept the EPUB
consumer when either its timer is active or its worker is active/activating,
and always reject a failed worker or the absence of both. Timer enablement is
not treated as health: the EPUB project deliberately disables the timer while
one multi-day worker owns the queue.

Installed predecessors:

- `full_inference_lab_sources.py` — `920d2ed1…0d48`;
- `full_inference_lab_validator.py` — `0c4a21d7…6858`.

Candidate identities:

- `full_inference_lab_sources.py` — `6103da31…13ad`;
- `full_inference_lab_validator.py` — `094d588b…bf31`;
- `test_full_inference_lab_sources.py` — `bd4940b7…318b`;
- `test_full_inference_lab_validator.py` — `36f307a6…5275`.
- inactive installer — `11b8abd9…9ffa`;
- installer tests — `5025e736…fef2`.

## Proof

- focused source/validator/runtime/reserved-runner suite: 39/39 local and 39/39
  target Linux;
- correction plus installer focused suite: 42/42 local;
- complete `test_full_inference_lab_*` family: 74/74 local;
- reserved-runner suite: 12/12 local;
- read-only target probe against the actual timer-inactive/worker-activating
  state: `epub_candidate_healthy=true`;
- no candidate source was installed and no service, timer, model, lease or
  booking was changed by these proofs.

## Bounded next effect

A source-only installer now checkpoints the exact two installed predecessors,
requires a ready lease and absent shared state/locks, replaces only those files
under root custody, validates imports and exact post-install hashes, and rolls
back both files on any mismatch. It is inert without `--apply`. A later
inactive installation must also run the focused and target probe checks. It must not
activate or retry the spent booking, stop the EPUB worker, restart a service,
call a model, or create another booking. A new run requires a fresh Lab Hours
reservation after installation proof.
