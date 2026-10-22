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
