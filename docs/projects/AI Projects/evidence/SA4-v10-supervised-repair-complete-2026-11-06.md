# SA4 v10 supervised repair complete — 2026-11-06

**Result: GO — COMPLETE.**

v10 completed one exact supervised repair of the accepted disposable v2 canary
from `a9831e62…4da0` to `fae178a1…a0c2`. The corrected core-runner registry
binding made measurement, checkpoint, ledger, effect admission and observer
lineage agree on registry v3. Exactly one grant claim and one repair occurred;
there were zero retries and no rollback.

One independent observer proof accepted all three registered checks:

- target bytes: pass;
- root:root mode-0644 one-link metadata: pass; and
- read-only consumer health: pass.

Terminal result `b830177a…18a6` is `postcheck-complete`; reconciliation
`a164c586…2cc5` consumed the one-use grant. The original root-owned mode-0600
checkpoint remains at `a9831e62…4da0`. The runtime exchange, operation lock,
emergency stop and temporary target are absent. The whole-host lease is ready;
LXC104/110/116, Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are healthy. No service action, restart, model
change, automatic route or promotion occurred.

This satisfies the supervised SA4 milestone for one reversible repair class.
It does not enable autonomous repairs or routing; the accepted result now feeds
the later M5 shadow and M6 promote/reject decision milestones.
