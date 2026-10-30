# M3 evaluator diagnostic correction — 2026-10-30

Status: **SOURCE CORRECTED; SPENT BOOKING NOT RETRIED**

Booking `aster-stream-a-m3-35b-20261030-1100` proved the corrected admission,
drain, exact candidate mount, 35B startup and stable sole-holder residency
boundaries. The fixed guest evaluator was invoked, returned nonzero, and exact
production restoration passed. The owner nevertheless reduced the result to
`M3_FIXED_COMMAND_FAILED`; the terminal therefore retained only
`OWNER_TRANSACTION_FAILED_RESTORED` and no safe evaluator failure class.

The source correction keeps answers, prompts, credentials and response bodies
out of evidence while making a later failure actionable:

- the public runner distinguishes bounded `http_4xx`, `http_5xx`,
  `engine_error` and `invalid_response` classes;
- the guest workload emits only its fixed failure schema, attempted/valid
  counts and first bounded record class;
- the host transaction validates that exact schema, restores production, then
  emits one bounded transaction failure projection; and
- the booked runner accepts only that fixed projection after its independent
  production postcheck and promotes it to the terminal failure code. Arbitrary
  owner output still falls back to `OWNER_TRANSACTION_FAILED_RESTORED`.

The new and changed focused tests pass 18/18. The wider registry, booked-runner,
M3 transaction/guardian and full-runtime selection passes 40/40. All 32 release
manifest pins match the current source bytes. Full local-AI discovery executes
674 tests: 651 pass, eight skip and 23 pre-existing stale-card/SA3-packet tests
fail outside this correction; none names a changed M3 diagnostic file.

This source candidate does not schedule or run a workload, mount the 35B
artifact, stop a service, read a credential, change a model or enable routing.
The spent 11:00 booking is not reusable. Inactive target installation and a
fresh booking remain separate steps.
