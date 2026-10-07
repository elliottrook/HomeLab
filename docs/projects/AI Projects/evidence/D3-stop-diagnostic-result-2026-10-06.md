# D3 diagnostic stop repetition — passed, first failure unresolved

Jason approved manifest `341df1d732973b5cbdb6842108c7f4feb0e03ed6c91493934aa831c653b07b11`.
One run from commit `9e28225` completed with **interrupted**, cancellation
requested and confirmed, no answer and no diagnostic exception. Worker elapsed
time was 0.077 seconds. Usage was unknown; do not report zero usage or cost.

The [run result](D3-stop-diagnostic-result-2026-10-06.json) is retained unchanged.
A separate read-only app-server connection [verified](D3-stop-diagnostic-recovery-2026-10-06.json)
one durable dispatch, exactly one matching provider turn, interrupted in both
worker ledger and provider state, only a userMessage item and no final answer.
It issued no new inference. The approval is consumed; no repeat is authorised.

This particular run passed the defined live stop criterion. It does **not**
identify or resolve the first live run's reporting failure. Keep that failure and
its unknown cause visible in the evidence history. Two attempts are not enough
to estimate a cancellation reliability rate or claim production readiness.

## Subsequent local guard and evidence boundary

Review identified a separate reproducible ordering hazard: `Transport.call`
delivers notifications while waiting for an interrupt RPC response. If that
callback already records a terminal event, the worker previously performed one
more event read before reevaluating its loop condition. An unrelated subsequent
read error could then make the outward worker result unknown despite the stored
terminal record.

Added an immediate state check before another event read. The regression fixture
delivers interrupted inside the interrupt callback and fails if the worker tries
to read again. It verifies both dispatch ledger and gateway end at interrupted.
144 Python tests and five renderer scenarios pass. The new guard was added
**after** the successful live test and is locally tested only. It is not proven
to explain the first failure, whose ledger was unknown. No claim of root-cause
resolution or additional live validation follows from this guard.

## Current boundary and resume

The finite worker now has live evidence for answer delivery, provider usage and
one owner-requested confirmed stop; Authentik issuance/revocation and the Mac TLS
path were separately verified. The HTTP gateway/owner in model tests remain
local fixtures. No production worker credentials, gateway deployment, native
Companion display integration or live sysadmin authority has been established.

Stop adding authentication-only or repetitive model experiments. The next work
is a concrete deployment package with the current single-worker boundary:

1. Complete the AI-PAM registry and supported custody/admin path for the two
   distinct credentials, without reusing Forgejo roles or human identity.
2. Bind the real global kill switch, define revocation/outage handling and
   verify private state ownership in the actual service arrangement.
3. Mount the existing routes behind a disabled feature flag and wire the native
   Companion surface, with current-owner enforcement and honest unknown states.
4. Prepare exact host/file/unit changes, baseline checks, backups, rollback and
   one bounded deployment validation for explicit approval. Include the first
   stop reporting failure as a residual risk; no autonomous sysadmin promotion.

Read-only investigation/local preparation remains Stream A. Permanent credential
issuance, policy/role changes, deployment, new cloud turns and Git publication
remain separately authorised operations. No such operation occurred here.
