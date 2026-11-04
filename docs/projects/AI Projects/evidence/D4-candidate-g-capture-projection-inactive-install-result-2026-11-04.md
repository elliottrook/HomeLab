# D4 candidate-g capture-projection inactive install result — 2026-11-04

## Decision

**PASS — installed inactive and production-validated.** This closes the
deterministic correction identified after spent attempt r5. It does not recover
or score r3, r4 or r5.

The exact platform source is mirrored at
`7a360b3b2d093f0110736294bfdd9e2899f07d34`; the reversible installer is
mirrored at `6d66683dc72f4e0e60170eb0d30f11f2c2960a40`. The deterministic
bundle SHA-256 is
`616ce57009fdcf579ac36e338862d3fb4e84bc4eb31b7be6c8e36e1cb8fed2ca`.

## Installed result

| File | SHA-256 | Custody |
|---|---|---|
| Host candidate-g adapter | `101ce58e6e103db22b9da9532528e44ac84171e178a5baeee0a4e196fe3e3c9f` | root:root 0644, one regular link |
| Release manifest | `1d18a86d756e6388a72794f74f3299611234be43937c12c32159f976556d9537` | root:root 0644, one regular link |

The predecessor bytes are retained root-only under
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-capture-projection-r1-20261104`.
The checkpoint directory is root:root 0700 and each predecessor is root:root
0600 with one regular link.

## Installed and production proof

- all 34 exact release pins load from the installed path;
- installed projection selects a bounded JSON code from either captured
  channel;
- otherwise-unhandled traceback output retains only the exception class;
- empty captured output retains only process exit status and channel byte
  counts;
- no raw traceback message, prompt, answer or case identity is retained;
- the whole-host lease is exactly ready, shared state/locks are absent and no
  port-11436 listener exists;
- Lab Hours Doctor is healthy with zero codes;
- dispatcher, Doctor and EPUB scheduler timers are active and waiting;
- LXC104/110/116, Aster Agent, accepted 9B/SYCL llama, Speech,
  `pvescheduler` and `pvestatd` are healthy; and
- the three core Aster services retain zero restart counts.

The exact host installation staging archive and directory were removed. No
booking, model call, service stop, restart or backend/model change occurred.

## Next gate

Candidate-g may now use one fresh registered booking after a new authoritative
full-window ledger check and fresh static/runtime preflight. The next attempt
must be a new transaction; r3–r5 remain spent. Failure must retain only the new
bounded telemetry and restore production. A complete result still requires 20
cases, exactly 14 requests, zero errors/retries/effects, production restoration
and later model-identity-blind review before any quality decision.
