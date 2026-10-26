# M3 NLU 27B semantic development run card

**Date:** 2026-10-26  
**State:** source validated; live restart/run requires approval

## Why this is the next candidate

The accepted 9B runtime completed the two-stage public development run safely
but reached only 9/24 exact interpretations. Its embedding endpoint returned
HTTP `501`, and `/v1/models` exposed only the active 9B model. LXC110 already
retains the materially stronger Qwen3.8-27B IQ4_XS model and its former accepted
Vulkan runtime, so this comparison requires no download or new credential.

The semantic/policy split remains unchanged: the model can propose only six
non-authorizing semantic slots. Deterministic policy owns privacy floors,
deny/abstain/clarify, capability allowlisting and route eligibility. The run
uses only the 24 public synthetic development cases. It cannot access a private
calibration or holdout and cannot enable routing.

## Exact transaction

The controller SHA-256 is
`ce87d1c7aaf60149bc6fcdf4f7fa78b8e0f2dfdd62116bcfdae13179ab7d5012`.
It fails closed unless:

- `local-ai-lease status` is exactly ready;
- LXC110 and the accepted 9B service are healthy;
- the accepted unit is
  `a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`;
- the accepted SYCL binary is
  `0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5`;
- the retained 27B Vulkan binary is
  `47692a3806ad5615c218e347f3bd55870436f07117c041cea7bf880b3b978693`;
- both exact model paths are readable;
- the transient candidate unit is inactive; and
- the fresh result path is absent.

Recovery is armed before the first stop. The transaction stops only
`aster-llama.service`, waits 30 seconds, starts the retained 27B candidate as a
transient unit, waits up to 450 seconds for health, runs the 24 public cases
once, stops the candidate and starts the exact accepted 9B service. The exit
trap performs restoration on success, failure, signal or timeout and validates
the accepted unit, binary, model readability and endpoint health.

The run changes no persistent unit, timer, schedule, key, model file, broker
grant, route or application. It does not restart the host or any container.
Aster/News inference requests can be unavailable during the bounded model
switch. News can catch up on its next scheduled pass under Jason's standing
authorization.

## Validation and decision

Shell syntax, six semantic-policy tests, three runner tests and three controller
tests pass. The public development gate remains at least 23/24 exact, zero
unsafe false routes and zero routed privacy underclassification. A failure
rejects the 27B semantic candidate without retry, calibration, holdout access
or promotion. A pass permits only exposed six-set cross-validation; it does
not authorize a new independent calibration or automatic routing.
