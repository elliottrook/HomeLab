# M3 K2 sealed two-host inactive install — conditional gate 2026-11-06

Status: source-only, conditional and non-authorizing. No archive or installer
was transferred and neither fixed runtime root was created.

## Exact source

| File | SHA-256 |
|---|---|
| `scripts/local-ai/m3_k2_sealed_two_host_install_gate.py` | `92d9d683f2600943c37ac5584797e6f60161e3848d0018ccd4574decb05822b1` |
| `scripts/local-ai/test_m3_k2_sealed_two_host_install_gate.py` | `a0f128bcfd38dacd309233a7817f7512a8124161dfe7d1b04b886b25d43f214e` |

The gate independently pins the exact archive and inactive-installer identities.
It accepts only the exact content-free K2 development reconciliation with
booking `aster-stream-a-m3-k2-20261106-2000-r1`, 192 requests, zero retries or
errors, a passing development gate and production restored.

## Conditional plan

Only after that proof exists does the gate emit a content-free plan ready for
a separate installation decision:

1. install the exact fourteen-file bundle inactive on the MacBook at
   `/private/tmp/aster-k2-sealed-runtime-v1` through the existing `macbook` SSH
   alias;
2. install the same exact bundle inactive on the Mac mini at
   `/private/tmp/aster-k2-sealed-coordinator-runtime-v1`;
3. retain distinct absent-state checkpoints beside both roots;
4. if rollback is required, validate and remove the Mac mini target first,
   then the MacBook target.

The plan requires no service restart, creates no access grant and attempts no
workload. It explicitly retains `effect_authorized=false` and
`authority=not-granted`.

## Verification

- focused tests: 4/4 passed;
- syntax compilation: passed;
- reject result, failed restoration, unknown/duplicate evidence and either
  changed source identity: fail closed;
- effect: none;
- next gate: observe and reconcile the already-booked development transaction.
  If it is not a restored pass, this gate cannot produce a plan.
