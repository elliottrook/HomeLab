# Aster Lab Hours SA3 envelope booking r4 card — 2026-11-04

## Authoritative booking

- Booking: `aster-stream-a-sa3-envelope-20261104-1400-r4`
- Owner: `aster-stream-a`
- Registered workload: `sa3-evidence-envelope-quality-v1`
- Window: 2026-11-04 14:00–15:30 America/Vancouver
- Recovery buffer: 900 seconds
- Ledger state after reservation: `scheduled`

The authoritative ledger returned `state=clear`, `booking_ids=[]` for the
complete execution/recovery window before this booking was created.

## Corrected installed boundary

- Host adapter: `fecb32cb29b2981aeab769efff7450e93c9853b30f79ca2131acb4015c74600c`
- Guest wrapper: `1d01c8c5bda942ddb42386eb56066c4858bf8032db39c136a4c9efbb933a4fc2`
- Release manifest: `6fa56d9c98817e84875966fb5addb6006fa14e9f07edb4cf3acbebc50a157f71`
- Manifest pins: 34
- Rollback checkpoint: retained root-only on host and LXC110
- Platform source/install result: mirrored `5b083701d9276249d2ff013e0429a888a1e8eb33`

Before booking, installed host and guest diagnostic proofs passed, the aggregate
Doctor returned healthy with no codes, the lease was exactly ready, production
services were healthy and no shared lock or port-11436 listener remained.

## One-attempt transaction

The dispatcher may claim only this registered booking. It must recheck the
authoritative booking, installed release, lease, shared lock, production
sources/services and restoration capacity immediately before effects. A failed
or uncertain check is terminal NO-GO without a model call.

After a claim, accept a complete result only for:

- exactly 20 cases and 14 model requests;
- zero result errors;
- the frozen packet/profile/model identities and control boundary;
- a retained bounded result digest and exit zero;
- `production_restored=true`;
- no remaining candidate listener/process/state/lock;
- lease exactly ready and all production postchecks healthy.

A non-zero guest exit must now retain either the final bounded JSON code or the
conservative `unclassified guest failure`. A bounded result-error code may
contain only error count and sorted error-class names—never prompts, answers,
case identifiers, or arbitrary exception messages.

## Terminal handling

R4 is one attempt. Do not retry, extend, reschedule, or infer success from a
claimed booking or model journal. Preserve terminal and attempt evidence. Only
a fully validated complete result may proceed to the frozen model-blind review;
any other state is NO-GO with its exact first bounded failure and independent
production-restoration result.

This booking authorizes no model/backend change, service restart, routing
change, tool grant, automatic promotion, or reuse of the spent r3 booking.
