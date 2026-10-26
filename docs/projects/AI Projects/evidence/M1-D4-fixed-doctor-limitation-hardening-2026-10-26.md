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

This is offline hardening only. It is not installed, does not replace the
accepted result, does not call a model and grants no tool or routing authority.
A future evaluation must use a newly frozen packet or a clearly labelled
development regression; the original blind result must not be rewritten.
