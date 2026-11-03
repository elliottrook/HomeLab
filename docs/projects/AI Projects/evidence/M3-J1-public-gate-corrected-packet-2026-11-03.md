# M3 J1 corrected public-gate packet — 2026-11-03

## Decision

**SOURCE READY; FRESH EFFECT DECISION REQUIRED.**

The v2 release manifest names the actual digest-pinned 24-case fixture
`scripts/aster-adaptive/fixtures/nlu-development-v1.json` and explicitly marks
the first zero-projection attempt as spent. The runner, artifact, execution
receipt, guard, acceptance rule and no-network/no-model/no-holdout boundary are
unchanged.

The focused suite now passes 7/7 and, unlike v1, verifies the repository file at
the packet's exact fixture path against digest `1565a21c…3785`. No real public
case was projected while correcting or testing the packet.

A future execution is one fresh attempt with zero retries. It needs a new
explicit effect decision because the previous approval was consumed by the
input-identity failure. It cannot deploy, enable routing, grant authority or
open the sealed holdout.
