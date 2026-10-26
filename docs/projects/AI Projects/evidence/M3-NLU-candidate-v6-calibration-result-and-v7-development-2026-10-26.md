# M3 NLU Candidate-v6 calibration result and v7 development — 2026-10-26

> State: Candidate v6 rejected; Candidate v7 sealed from calibration-derived
> corrections; fresh calibration-v3 required
>
> Authority: not granted; automatic routing remains off

## Candidate-v6 calibration-v2 result

The fresh 60-case calibration-v2 release was derived by separate case,
label-review and scoring roles before any Candidate-v6 output existed. It has
ten cases per request family, zero normalized overlap with the public
development fixture and zero overlap with the entire Candidate-v1 calibration
source. The independent holdout remained sealed.

The one bounded local-model run completed all `60/60` cases. `57` responses
were structurally valid; invalid responses remained in the denominator. The
accepted local service was unchanged and reported zero restarts afterward.

- Candidate-v6 artifact SHA-256:
  `6a16f92527981d5048a4163b5c8de2ad146ec7901f459d221f628e663d06c236`
- Calibration release artifact SHA-256:
  `191bc3e11da4df1eb9716f2bf6b82c0b50ced5ab911a4fb22653b755dc6a0e8f`
- Run SHA-256:
  `28ec62ca99225789f2463670baf08e4099261ae4269688043dbfc561cce5742d`
- Attempt journal SHA-256:
  `185914fbc7ecbe8b64158b9afd9a119e010174716bb8eb8e4846eb28a6339545`
- Score SHA-256:
  `2dbdb6bcbb495329108af9133073dbb211ac38e53bbc2a5eb847c4524dd967d0`
- Routed cases: `30`
- Safe and exact routed cases: `22`
- Privacy underclassifications: `6`
- Unsafe false routes: `2`

The registered constraints permit zero privacy underclassification and zero
unsafe false routes. The frozen selector exited nonzero with no eligible
threshold and created no threshold artifact. Candidate v6 is therefore
**rejected**. No holdout case was opened and no route was enabled.

Aggregate diagnosis localized privacy misses to external research,
read-only investigation and one unsupported personal-memory request. Both
unsafe routes were change requests that attempted to create anonymous
administrator access or purge audit history. Only the calibration partition
was used for this diagnosis.

## Candidate-v7 correction and public-development check

Candidate v7 adds two general rules:

1. schedules, finances, health/wellness, location, messages, identity and
   private records remain personal even when combined with public web data or
   expressed through a missing referent; and
2. anonymous/unauthenticated administrator access and audit-history erasure
   are explicit policy denials, alongside deletion of the only backup.

The public 24-case development run completed with `23/24` structurally valid
and exact classifications, zero unsafe false routes, zero privacy
underclassifications and zero unnecessary non-routes. The one invalid response
is retained as non-routable.

- Prompt SHA-256:
  `a7bce210cce2e5623c175481b872a29ea11b2e3d175d206de62a2e222ea29b13`
- Adapter SHA-256:
  `bc9e1bacfaab993875e15e3e20288d5c1b3c61b380cc98f7025d58082e43e747`
- Policy artifact SHA-256:
  `180f0df3fd018a5cb4a2362a4fa454562aad973ba80b6f11f4f06c1477ec6b4d`
- Candidate bundle self-hash:
  `7c9ed66f0193e3468facfa61db6763438bbc0fbf9e3128b52a90da06e4be7e73`
- Candidate artifact SHA-256:
  `9987ac6cc7ebe948264701ae189f13c5e5f8eaabcd418d5839e892f1d17fe295`
- Public development output SHA-256:
  `f198c579825a1fe8d9eeee5f4e1e2dfb0523c533d774e7467678e8e4dd5ade71`

Because v7 was tuned from calibration-v2 evidence, calibration-v2 cannot
qualify it. The next gate is a new independently created and labelled
calibration-v3 set disjoint from development, calibration-v1 and
calibration-v2. Candidate-v7 must pass that set before any holdout access or
threshold registration.
