# D4 candidate-j R3 transaction pass / postcheck NO-GO — 2026-11-05

## Candidate-J transaction

Distinct booking `aster-stream-a-sa3-candidate-j-20261105-0415-r3` claimed
exactly at 04:15:00 PST and completed at 04:18:44 after 224 seconds. The
authoritative ledger is `complete` / `COMPLETE`; its root-custodied terminal
binds the exact workload, six requests and `production_restored=true`.

Independent reconciliation accepted the retained result as a root:root
mode-0600, one-link regular file of 3,838 bytes with SHA-256
`ae5b10d72006bb3ffe7684440b7362828e9419bc6892ef97024c51b8b7c279c6`.
The frozen scorer accepted exactly 6/6 cases, two model requests, four
deterministic abstentions, zero retries, zero errors, zero effects, authority
`none` and automatic routing `off`. No model identity or case content entered
this evidence record.

## Restoration and first failed postcheck

The whole-host lease is exactly ready; drain state, drain lock and shared
operation lock are absent; no Candidate-J process remains. LXC104/110/114/116
are running. Aster Agent, accepted llama.cpp/SYCL, Speech, both News timers,
the Lab Hours dispatcher and Doctor, `pvescheduler` and `pvestatd` are healthy.

The complete exact-cycle gate is nevertheless **NO-GO** because the required
EPUB timer/worker postcheck fails. `epub-narration-scheduler.timer` is
disabled/inactive and its service is failed with exit 75. This state predates
R3: the last scheduler failure was 19:47:34 PST and the timer stopped at
19:48:58 on November 4. The separately booked 01:00 EPUB resource ladder then
failed at 01:03:07 with bounded cause `worker-not-active`, `restored=true` and
zero stages. Candidate-J did not cause the EPUB failure and its own production
transaction restored cleanly, but the predeclared success condition permits no
exception for a pre-existing failed postcheck.

R3 is spent and is not retried. The clean result remains retained but does not
advance to an untouched evaluation freeze under this run. The next corrective
action belongs to the EPUB project: reconcile and restore the scheduler/worker
with retained evidence. Stream A may then decide whether a new distinct public
transaction is justified; no automatic retry, blind evaluation, route,
authority or promotion follows.
