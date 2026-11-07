# M5 K2 no-effect shadow reconciliation boundary — 2026-11-06

## Result

The prospective 60-case K2 no-effect shadow phase now has a source-only,
fail-closed reconciliation boundary introduced at Stream A source commit
`1fe7e285` and type-hardened at `5fc7b84d`.
It refuses to treat the scored shadow envelope as operational evidence unless
one exact Lab Hours terminal also proves:

- a complete registered `m5-k2-no-effect-shadow-v1` transaction;
- exactly 60 requests, zero retries and zero errors;
- an exact digest binding to the retained shadow envelope;
- `production_restored=true`;
- no route execution, provider egress or external cost; and
- the bounded date-specific K2 M5 booking identity.

On success it returns only content-free score fields plus the restoration and
no-effect proof. Authority remains `not-granted` and automatic routing remains
`off`. Unknown terminal fields, changed identities, incomplete or unrestored
state, count drift, a digest mismatch or any effect all fail closed. Exact
integer typing prevents Boolean values from masquerading as zero retries,
errors or cost.

## Verification

- source SHA-256:
  `a5745653ac547f8eceef625a83cda2e441f964dac11b808e6dbf32214d0a6290`
- test SHA-256:
  `cfcb5fc266af83b3665dda7a406d77a68faf1a8d96cd26d09c4db0c844ec36a0`
- focused reconciliation tests: 6/6 pass
- complete `test_nlu_k2*.py` discovery: 114/114 pass
- deterministic bundle-builder suite: 3/3 pass
- platform `test_m3_k2*.py` suite: 31/31 pass
- combined K2 source audit at this boundary: 148/148 pass

The first attempted extra bundle test invocation named a nonexistent module and
failed before executing a test. The correct existing module
`test_build_nlu_k2_sealed_runtime_bundle_v1.py` then passed 3/3; no source
change was needed.

## Boundary

This work did not create a fixture, booking, terminal or shadow result; call a
model; open sealed data; acquire a lease; execute a route; contact a provider;
install or start a service; or change production. The booked K2 development
transaction remains the earlier runtime gate. The later shadow effect still
requires its own registered workload, Lab Hours booking and reviewed effect
packet after all preceding gates pass.
