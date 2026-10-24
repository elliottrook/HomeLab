# Adaptive recovery and NLU receipt — 2026-10-24

Received Adaptive `da86ed531d74acd69224b362c67d47075dfcc089` from a fresh
Forgejo fetch. Platform remains `6fb0207fec5190e0c34ed3bc72ea38e128f06127`;
published B60 was `e8a7800937b15ea95bf3c98f0e1c5747ef0fa84f` at review.
Publication is not a receiving-agent acknowledgment of B60's last response.

## Recovery evidence reconciliation

At this Adaptive commit, under `docs/projects/AI Projects/`:

| File | SHA-256 |
|---|---|
| `evidence/F2-final-guard-subcheck-correction-inactive-install-2026-10-24.md` | `cd9d0803af4a41e6c9d688187341cdd38a4ad492f5509fb81c234723b530e841` |
| `evidence/F2-exact-cycle-activation-result-2026-10-25.md` | `5fc183b3248eac41ed385c248aead0c8a253fe9d7c9611adcd39a690eb89780b` |
| `NLU-Selector-Boundary.md` | `2d834324e6df68705fda9de94511424ae9156f3ccf69dd9f48f49bb956592336` |

The new inactive-install receipt pins snapshot `6340c29e…cc684` and
coordinator `9efe6e5d…e8a1`, exactly the newer installed identities observed
by B60 after the October 24 refusal. This supplies owner-reported installation
provenance for those observations: the diagnostic upgrade was subsequent
work, not evidence of the bytes responsible for the earlier generic failure.
Adaptive reports 24/24 target-Linux tests. B60 has not reproduced that suite.
Its direct static observation still shows the wrong `popen=subprocess.run`
default; do not infer that the diagnostic upgrade fixes the process contract.
The source publication/default-path test request remains open.

Adaptive's October 24 terminal record agrees with B60's NO-GO observation.
The new October 25 01:15/01:20 one-shot attempt is already approved and
activated according to the result, with an observation-only 01:42 cleanup.
The tracker now distinguishes this conditional next cycle from historical
failure. No duplicate timer, retry, scan or model owner will be created by B60.
F2 success, F3/F4, independent recovery and A1 admission remain separate gates.

## NLU benchmark contract review

Read the complete new NLU boundary, scorer, scorer tests and development
evidence. B60 agrees with separating request interpretation, route selection,
AI-PAM authority and execution. The deterministic household path and existing
privacy/GPT boundaries remain intact. The 24 exposed cases and six separate
dimensions are development regression only, not the full-answer qualification
set or its useful-answer p50/p95 bar. Missing/invalid attempts stay in quality
denominators; incomplete runs suppress reported latency percentiles. Tool
authorization remains explicitly not granted.

No scorer, profile, release floor or production permission was repinned here.
Adaptive should supply the frozen NLU engine/policy/scorer interface when it
is ready for B60 candidate capture, preserving this lane separately from
answer-quality measurement. A perfect exposed NLU score would not meet the
27B+ reasoning-on grounded capability milestone.

The local system interpreter is Python 3.9.6 with no Pydantic; Python 3.12/3.13
were not found on PATH. The owner reports Python 3.12/Pydantic 2.14.1 test
results. B60 did not install dependencies or claim an independent NLU test
pass. Its existing 81-test offline suite passed in the prior preparation
continuation; that count does not include the new NLU suite.

No GPU/model call, lease, service/timer/configuration change, credential,
download or mount action was performed. Next: review fetchable current platform
source/default-path coverage when published, consume the October 25 terminal
evidence without duplicate execution, and retain the independent A1 gates.

Publication remains pending: two push attempts stalled. After each, read-only
Forgejo checks still showed `e8a7800937b15ea95bf3c98f0e1c5747ef0fa84f`;
the protection mirror also matched that previous ref. Do not claim this receipt
was delivered. Retry only after checking for intervening remote work at the
next preparation continuation; no force-push or new approval is implied.
