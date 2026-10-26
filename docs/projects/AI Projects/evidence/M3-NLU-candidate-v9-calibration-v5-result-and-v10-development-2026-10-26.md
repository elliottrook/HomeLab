# M3 NLU Candidate-v9 calibration-v5 result and Candidate-v10 development — 2026-10-26

## Decision

**REJECT Candidate-v9.** The one bounded calibration-v5 run completed all 60
attempts with zero unsafe false routes and zero privacy underclassification,
but no registered threshold met both the minimum coverage and maximum
selective-error constraints. The selector exited `2`, wrote no threshold and
did not open the independent holdout.

## Frozen calibration-v5 inputs

- Candidate-v9 artifact SHA-256:
  `1941b4754c5195e11b623479f63cb368cacfea64a7adc3223bf22794e3b825f5`
- Source SHA-256:
  `50b6a36b64e8942eb83dd8769f52c52b6fa4a0e7a1d42adeebd7be2c5157c676`
- Blind labels SHA-256:
  `5cf947586cac331efe08f375a4a22aceca0ea0f9b1bea92ae466a0fec2a811ae`
- Custody manifest SHA-256:
  `87e1a39de0fe7f6ef6585f51727f131251df6ad665108b843c4d9ab2db544e8b`
- Normalized text-set SHA-256:
  `be93e28afa6de2a5a6c525c1659563292196c05a84bcff1412b38795d39d2423`
- Release artifact SHA-256:
  `a407bf3e7939e685ae69a80b2d74bafb89b4d4719652281a87b04d572a548896`
- Release canonical self-hash:
  `0bc91001202360b76661c0a50e914e7fee948e7d3a4c06768eab52378830e11f`
- Registered policy SHA-256:
  `604912e9e476644b5baddbdfcb944269d051fa00e72284291328f81ded20f945`

The 60-case fictional source has ten cases per family and zero normalized
overlap with public development or calibrations v1 through v4. Custody, blind
label review and release derivation remained separate.

## Calibration-v5 result

- Run SHA-256:
  `8ee1b935d004ddb08c11433681796c27f58331738b122a1049a1f8362e44975b`
- Attempt-journal SHA-256:
  `583690ee3daddc8a69a96ef48c49474adb8614b362f476614362382cab6a3161`
- Score SHA-256:
  `ea9ffe2b32977d1a2230f89386c0748a7b38c7dc32b9ae61bc058f9ae5cbabfd`
- Attempts: `60/60`
- Structurally valid: `56/60`
- Routed: `35/60`
- Safe and exactly correct routed rows: `27/60`
- Privacy underclassifications: `0`
- Unsafe false routes: `0`

At route score `1`, coverage was only 58.3% and eight routed rows were not
exact, so the registered 60% coverage and 10% selective-error limits could not
both pass. Aggregate mismatches concentrated on capability overassignment,
timer versus schedule wording, retrieval versus user-supplied context,
research versus publication, and one unnecessary clarification.

## Candidate-v10

Candidate-v10 tightens capability assignment to the action actually requested,
distinguishes explicit deletion, timer operations, retrieval, local joining
and external publication, and restates the safe abstention and general-answer
rules. It remains local-only, tool-disabled, case-data-free and
`authority=not-granted`.

- Adapter SHA-256:
  `39759586606266d30042fbeb4d9979a7a4d9aaadc7cf116e14f6fec823777f57`
- Policy artifact SHA-256:
  `8763186780060f6602db6d8632fa4723a1173d82a3c738a211c22f6d7ebe4b8d`
- Candidate canonical bundle hash:
  `f5971a4718b3f2839014182db43cb23e432bdcc5244a602fb4de96f89d813931`
- Candidate artifact SHA-256:
  `ad01b3883a65125b1e37335b66d62a65d65103b98c8577ecd2a337833a2bcb39`

Its public development run completed 24/24 with 23 structurally valid, 22
exact, zero privacy underclassification and zero unsafe false routes. The two
remaining rows were one invalid ambiguous-change response and one mixed
personal-research capability mismatch. Result SHA-256:
`a8aaf9fb0ebefec9f7ff3e64988a9bc554bc816cecb34e8c95ab3041738b5ddd`.

## Next gate

Candidate-v10 requires a new calibration-v6, independently created and
blind-labelled and disjoint from development and calibrations v1 through v5.
No threshold, holdout access, route or tool authority exists.
