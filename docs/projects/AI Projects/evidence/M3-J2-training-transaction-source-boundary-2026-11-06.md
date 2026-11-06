# M3 J2 training transaction source boundary — 2026-11-06

## Outcome

The J2 training transaction is source-complete but remains inert. No training
worker, local-AI workload, service action, booking, lease, sealed-evaluation
read, route, tool, deployment or model promotion occurred.

The exact retained content-free admission result is now a first-class input
contract. It accepts only canonical bytes matching the reviewed custody chain:

- training admission SHA-256:
  `9994f4a2941503c5608ae85095bd0985d3292855c09bec0b6dfcb9e2aca00fd1`;
- corpus SHA-256:
  `9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a`;
- corpus-release file SHA-256:
  `1f0e7d3777746e23472b0daa85dc7d103da0ac7ce09fe192e1c0f44dd0abe710`;
- training-recipe SHA-256:
  `419a42c166d08e92084178ac897d3f011dc565ca1474ae8a4fba8be68c9aa0e9`;
- validation-truth SHA-256:
  `cfb58d9bb29667a762b01c246f3e52e0d5a9d29158aab21f22831bde573c2eab`.

The real admitted input preflight reconstructs the exact 768-row training and
192-row validation split without opening or naming the sealed evaluation
content.

## Transaction properties

`nlu_j2_training_transaction_v1.py` now composes the frozen primitives into one
fail-closed owner:

1. validate the exact admission, corpus, release and recipe identities;
2. run 40 complete, unshuffled 24-batch CPU epochs with one AdamW update per
   complete batch and an after-epoch checkpoint;
3. calculate all 40 validation summaries and select the checkpoint by the
   preregistered order;
4. quantize the selected checkpoint to ten decimal places, choose the maximum
   exact-coverage threshold and emit the bound selection receipt;
5. build and self-validate the inert artifact;
6. recompute each clean replay in a separate isolated interpreter and require
   byte equality with the retained replay;
7. retain the six exact output files with create-only mode-0600 writes.

Workers receive a minimal deterministic environment, single-thread controls,
no stdin and an audit hook rejecting socket/SSL activity. The owner refuses an
existing output directory. A failed or uncertain phase retains a bounded
content-free `failure.json` naming only the first phase and exception class;
it does not remove partial evidence or permit an in-place retry.

## Validation

- exact real admitted-input preflight: pass, 768 training / 192 validation;
- focused admission and transaction tests: 10/10;
- complete `test_nlu_j2_*.py` suite: 113/113;
- transaction source SHA-256:
  `e9f8821b4316197b25cfac3c33a949128317002249da9f6b2cc4e0169e0435c8`;
- `git diff --check`: pass.

## Remaining effect gate

This source record does not authorize training. The next packet must review and
pin the transaction owner, select the execution host, measure resource
headroom, establish a bounded runtime and recovery plan, and determine whether
the chosen host/workload requires an Aster Lab Hours reservation plus the
whole-host lease and shared operation lock. It must also freeze exact input and
output paths and the no-retry reconciliation procedure. Only a later explicit
training-effect decision may start the worker.
