# Aster Lab Hours SA3 candidate-i R1 card — 2026-11-04

## Booking

- ID: `aster-stream-a-sa3-candidate-i-20261104-1730-r1`
- Owner/workload: `aster-stream-a` /
  `sa3-evidence-envelope-candidate-i-quality-v1`
- Window: 17:30–18:30 host-local offset `-07:00`, comprising the fixed
  2,700-second transaction ceiling and 900-second recovery reserve
- Authoritative ledger at 17:02: clear, no booking IDs

R1 is candidate-i's first and only authorized attempt on its untouched packet.
Candidate-g R8 and its packet remain spent.

## Installed boundary

Installed candidate-i proof binds:

- workload registry / reserved runner / full runtime:
  `82902437…ab70` / `eab869da…7960` / `6c7767e5…98ad`;
- release manifest / host transaction / host adapter:
  `c2812b75…a5e` / `c1d40abe…2131` / `e16a2512…8c6`;
- guest packet / deterministic v2 / batch v2 / runner v2 / wrapper:
  `0b9bfb86…625d0` / `4ca154c6…1943` / `eaeddb10…70d4e` /
  `58b932a6…9188c` / `a3db03b8…9a74`.

Root-only host and guest checkpoints are retained. The lease is ready, shared
state/locks and candidate process/scope are absent, all fixed imports and 36
manifest pins pass, and production is healthy. No service was restarted.

## Runtime and terminal boundary

The dispatcher must recheck this exact reservation, installed pins, lease,
shared operation lock, candidate/listener absence, production health and
recovery reserve at claim. Accept success only for 20 cases, exactly 14 model
requests, six deterministic no-transport abstentions, zero retries/errors/
effects, result schema v2, candidate alias `candidate-i`, retained canonical
digest, exit zero, `production_restored=true`, no remaining candidate state,
scope, listener or lock, ready lease and healthy independent postchecks.

Any other state is terminal NO-GO without retry. Retain no prompt, answer,
case identity, response body, exception text or arbitrary output outside the
root-custodied result. This authorizes no model/backend change, repeated
attempt, route, tool grant, repair authority or automatic promotion.
