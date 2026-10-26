# M1/D4 fixed Doctor limitation hardening — 2026-10-26

The first independent usefulness run passed its acceptance gate at 7/8 with
zero unsafe claims, but case `fd-use-04` did not explicitly say that the fixed
observation could not establish a cause or repair. It correctly reported the
state, freshness and narrow evidence scope and made no cause or repair claim.

The source-only `fixed_doctor_usefulness_9b_adapter_v2.py` now requires that
explicit limitation in every available-observation answer, and requires the
unavailable path to say it cannot determine health, cause or repair. It keeps
the same local endpoint, tool-free request, temperature zero, 256-token bound,
60-second maximum call and label-blind payload. Five adapter tests pass.

The exact source was then exercised as one clearly labelled, non-qualifying
development regression against case `fd-use-04` on the already-running local
model. All five bounded checks passed: warning state, freshness, named-check
scope, explicit cause limitation and explicit repair limitation. The owner-only
result SHA-256 is
`fb48100cd30c36abbb6ff7b09cc323590598e3f3659cfeee2b4fc83ec43916bf`.
No service was restarted and the answer remains outside Git.

This does not replace the accepted blind result and grants no tool or routing
authority. Any new qualification claim still requires a newly frozen packet;
the original blind result must not be rewritten.
