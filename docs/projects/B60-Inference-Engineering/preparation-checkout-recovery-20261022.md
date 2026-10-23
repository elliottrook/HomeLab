# Disposable preparation checkout recovery — 2026-10-22

The prior temporary checkout at
`/private/tmp/b60-nightly-20261017.L4SO8g/repo` unexpectedly reported 1,570
changed entries, predominantly deleted files, including AGENTS.md and the
B60 offline test modules. Its local HEAD still identified `3a1494a0`, but a
new shared clone could not read tree `adde3d45cdd7b0df2f519546cae650fbc98e3aa7`.
Therefore a surviving commit identifier is not proof of intact object storage.
The cause is unknown. No deleted file was staged, committed or restored over
the affected directory; no unrelated work was removed.

Recovered instead by independently cloning authoritative Forgejo branch
`codex/b60-adaptive-coordination`, without shared objects, into
`/private/tmp/b60-preparation-20261022.Q5eaCq/verified-repo`.
Base HEAD is `156ecc2d8ad3bd5080605f0bf7fb2b098e861afb`, matching the
read-only GitHub protection branch. Connectivity-only Git fsck succeeds and
81 B60 offline tests pass in the recovered checkout. The failed shared clone
is retained separately and must not be used for continuation.

The older unpublished October 21 note remains readable in the affected
checkout at `docs/projects/B60-Inference-Engineering/nightly-admission-20261021.md`.
Its substantive observation was a 06:22:50 PDT heartbeat / 06:23:17 execution,
outside the lab window, with unchanged owner refs and no live work. Retain
that observation without claiming its whole prior commit is recoverable or
publishing another identical owner request.

Fresh fetched owner refs remain Adaptive
`a2cae9e3e9354f20308f356e1487a0c0bc8be665`, platform
`6fb0207fec5190e0c34ed3bc72ea38e128f06127` and B60 base above.
No new F2 correction, recovery drill or full-path admission is published.
The main implementation checkout is clean at this observation; it was not
reset or modified. No production, GPU, model, credential, lease, timer,
service, mount or download action occurred.

Next continuation must use the new independent verified checkout, fetch all
three owner branches, and follow the existing F2 source-reconciliation request.
Do not deploy the old coordinator or infer readiness from local recovery.

## Nightly admission observation, 01:51 PDT

The nightly trigger timestamp was 08:50:55 UTC (01:50:55 PDT), and the
execution clock 08:51:06 UTC (01:51:06 PDT). Unlike the last two nightly
turns, this is before 04:15, but clock eligibility alone grants no admission.
Fresh fetches leave all three owner refs above unchanged; the published
Adaptive admission-card SHA-256 remains
`d0152400c4fc5bbf446490189dea8acb27970cc598cb34185dfb8e3d46a85b55`
and platform coordinator SHA-256 remains
`67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d`.
No source reconciliation, trusted receipt, independent live recovery or READY
benchmark card has been published. F3/F4's inactive stage is not that proof.
Eight offline peer-admission/recovery-margin tests and Git connectivity pass.
No fresh host/service health is claimed: this turn stayed local/repository-only
and did not acquire a lease, collect production preflight, invoke F2, stop
consumers or make a model call. The GitHub protection ref still matches the
published base. No push and no duplicate owner request; the existing F2
source-reconciliation request remains the next action.

## October 23 nightly continuation

The trigger carries 07:29:35 UTC (00:29:35 PDT), but the first execution
clock is 10:00:35 UTC (03:00:35 PDT): approximately 2h31m later. This is
an observed timestamp difference, not a diagnosis of scheduler or sleep cause.
The turn did not acquire a lease or execute GPU work. The same three owner
refs and admission/source hashes above remain current after a fresh fetch;
the additionally fetched compatibility branch is
`1dd38c762e7598646a94d49cc44188376d6952ea`, an already documented source-only
October 17 projection correction, not a new F2 success or live release.
A failed guessed-path lookup was corrected with the branch tree listing;
its empty-pipeline digest was discarded, not accepted as a receipt.
The protection branch still matches the published B60 base. Eight offline
admission/recovery-margin tests pass. No new owner READY evidence exists;
the F2 source-reconciliation request and independent recovery/A1 gates still
control continuation. No fresh production state is asserted, no missed scan
was retried, no model call ran, and no push occurred.
