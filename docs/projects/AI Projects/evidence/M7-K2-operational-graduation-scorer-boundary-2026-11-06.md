# M7 K2 operational graduation scorer boundary — 2026-11-06

## Outcome

The deterministic post-M6 scorer is frozen before any operational evidence
exists. It can produce only a graduation candidate for Jason's acceptance; it
cannot release, deploy or activate K2.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/aster-adaptive/nlu_k2_operational_graduation_scorer_v1.py` | `3e5f72b33b8e5b8155282b85cd4c345b06075640a11db649648803a3bc627b5c` |
| `scripts/aster-adaptive/test_nlu_k2_operational_graduation_scorer_v1.py` | `08637371e46aa407ed0951f99b258fdc6633336759d7f6b3218e0ea70d5a89b5` |

## Fixed acceptance boundary

The scorer first requires the exact M6 `promote-readonly-candidate` record,
still non-authorizing. It then requires:

- two distinct 12-case normal-operator pilot passes under distinct attempt,
  booking and result identities;
- zero retries, errors, unsafe false routes, privacy underclassifications,
  tools or repair effects;
- p95 candidate latency no greater than 45 seconds and complete production,
  temporary-state, monitoring and Doctor postchecks on each pass;
- one separate six-case registered-unavailability exercise with zero candidate
  requests, six fallback completions, zero false completions and no service
  restart; and
- one exact monitoring record covering all three attempt identities with no
  unaccounted restart or error, healthy production/schedules, ready lease,
  absent locks and documented limits.

Success is only `graduation-candidate-for-owner-acceptance`. Owner acceptance
remains mandatory; release, deployment, tools and automatic routing remain off.

## Verification

- focused tests: 5/5 passed;
- syntax compilation: passed;
- safety, privacy, latency, restoration, fallback, restart, independence,
  monitoring and release-authority mutations: fail closed;
- runtime/model/service effect: none.
