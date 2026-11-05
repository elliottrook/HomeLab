# SA3 candidate-j reserved-runner integration source — 2026-11-04

Candidate-j's fixed runner kind is admitted in source and joined to the
existing exact reservation/full-drain lifecycle. The reserved runner accepts
only the registered workload, a six-case receipt, exactly two model requests,
zero errors, a complete result digest and `production_restored=true`. Its
bounded effect string is distinct from candidate-g and candidate-i.

The full runtime dispatches that profile only to the candidate-j transaction
and listener adapter, uses the registered 1,800-second effect deadline, and
retains the existing exact-start, lease, shared-lock, cleanup and accepted-GPU
postchecks. Quiet-host detection now includes candidate-j processes. Joined
tests cover the reservation-to-terminal receipt path and the distinct
1,800-second runtime path.

Release manifest `sa3-candidate-j-runner-source-v14` pins the changed reserved
runner/runtime and all candidate-j transaction modules. Focused candidate-j,
reserved-runner, runtime and release-integrity tests pass.

This is source integration only. Installed production still lacks the changed
runner/runtime/manifest, candidate-j host modules and five guest runtime files,
so candidate-j cannot run. No booking, model call, service stop or restart,
route, authority or promotion is created. A deterministic inactive installer
with rollback and exact target proof is the next milestone.
