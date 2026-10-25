# D4 candidate-G lease preflight NO-GO — 2026-10-25

Status: approved model run not started; exact candidate remains unspent.

## Approved scope

Jason approved the candidate-G tool-free run at digest
`03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`
and a fresh blind review only after 12/12 structural admission. The dry run
recomputed that exact digest without reading a key. The B60 host, Aster Agent,
accepted llama.cpp/SYCL service and Speech were healthy and idle.

## Failed prerequisite

Stream A requires a verified live lease before using the B60. Read-only
platform reconciliation found no currently qualified lease that can protect
this run while retaining the accepted llama endpoint:

- legacy `local-ai-lease acquire --light` drains the endpoint the run needs;
- the application-only entry point exists, but its trusted source-bound
  `prelease.json` is absent and its live gate remains blocked; and
- the cooperative full-inference runtime is installed with matching source
  hashes but has no qualified live lease/state/timer and requires separate
  effect authorization and recovery proof. It is the still-unproven lab-hours
  controller, not an available shortcut.

No lease was acquired, no service was stopped or restarted, no key was read,
no model request ran and no journal was created. Candidate-G remains exact and
unspent; its approval can be consumed after a compatible lease is qualified.

## Next action

Complete the scheduled F2 archive timing gate and the downstream retained
receipt/watchdog/recovery chain for lab hours. Once a compatible lease is live,
rerun the same preflight, execute candidate-G once, require 12/12 structural
admission, and only then prepare the model-blind packet.
