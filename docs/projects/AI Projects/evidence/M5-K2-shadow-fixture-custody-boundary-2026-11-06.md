# M5 K2 shadow-fixture custody boundary — 2026-11-06

## Result

The private-fixture custody validator required after K2's earlier runtime gates
is now source-ready. It binds the frozen 60-case preregistration digest
`4f96d441256f07e9d87d709aac20ee8e1f3af50f82c7de15064f0d4b71fb9108`
and accepts only:

- exactly 60 unique `synthetic-sanitized-S0` cases;
- ten cases for each of the six request families;
- valid frozen whole-label identities;
- distinct fixture-custodian and blind-label-reviewer roles; and
- zero case-ID or request-digest overlap with the supplied development and
  sealed-evaluation identity sets.

It emits only a content-free receipt containing fixture, case-set, request-set
and label-set digests. Raw request text is not exported. The receipt explicitly
keeps effects unauthorized, authority ungranted and automatic routing off.

## Verification

- source SHA-256:
  `0b0d0df9995d9a56aa9756b4a28111f70be9eb914210606bdda0fae9e526e163`
- test SHA-256:
  `4d1dac9d011adf1a5b9fc84b66ee18b7fe18f012b112765973e35f39852f22e9`
- focused custody tests: 5/5 pass
- complete `test_nlu_k2*.py` discovery: 98/98 pass

No fixture was created, labelled, opened or transferred. No model, provider,
route, booking, lease, service, tool or deployment was invoked. Actual fixture
custody remains conditional on the development and sealed-evaluation gates.
