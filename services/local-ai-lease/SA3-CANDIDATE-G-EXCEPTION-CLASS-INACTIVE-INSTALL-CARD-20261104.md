# SA3 candidate-g exception-class inactive install card — 2026-11-04

## Exact effect

Replace only LXC110
`aster_llama_sa3_evidence_envelope_wrapper.py`, from
`1d01c8c5bda942ddb42386eb56066c4858bf8032db39c136a4c9efbb933a4fc2`
to `626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`.

Create the root-only predecessor checkpoint
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-exception-class-r1-20261104`
before replacement. Refuse baseline drift, an existing checkpoint, non-regular
custody, non-ready lease, shared drain/operation state, source drift, failed
installed proof, or rollback uncertainty.

## Required proof

- installer is inert without `--apply`;
- local focused platform suite and target-Python wrapper suite pass;
- deterministic bundle reproduces;
- installed file is root:root 0644, one link, exact new SHA-256;
- a synthetic otherwise-unhandled `KeyError` emits only
  `candidate-g guest exception-class:KeyError` and excludes its private message;
- lease, locks, Doctor, production health, restart counts and listener absence
  remain unchanged.

## Exclusions

No booking, candidate invocation, model request, service restart, backend/model
change, retry, blind review, route, tool grant or promotion is authorized by
this inactive one-file installation.
