# Model R1 pre-claim NO-GO and distinct R2 correction

The real11:12 owner exited before admission, checkpoint, claim, guardian,
isolation, model mount or GPU/model call. Exact source failure was
FRESH_BACKUP_SOURCE_TASK_CHAIN_FAILED at epoch1793988721. Production stayed
available; all shared markers were absent and owner/guardian had zero tasks.
R1 must never be replayed or counted as a model trial or unattended pass.

Authenticated read-only TrueNAS source inspection found all tasks successful.
The original ordered same-cycle jobs were61113(task1,01:00),61255(task3,02:00),
61395(task2,03:00). A later successful task1 rerun62427 began10:29:01 and
finished10:29:45, replacing the latest-job cache after B60's10:28:44 integrity
completion. Its initiator is not inferred. The existing latest-only validator
correctly rejected that new out-of-order view. No task, schedule or backup was
rerun by B60 to manufacture a green gate.

The correction is a distinct pinned source producer, not a weakened archive,
ordering or latest-task-success check. Using the existing verified admin SSH
path, an exact metadata-only collector ran on TrueNAS, queried current tasks
before/after historical core job metadata, required stability/all-success and
created only a new root-private evidence receipt. No credential, access
control or observer allowlist changed. The exact receipt was returned over
that authenticated transport and pinned for root-custodied upload/card binding;
no author-supplied provenance or chat statement substitutes for the live read.
Receipt SHA256d52d58ba411df6bcc32ab4cdbf35e2f91511372a808d54182a717a8eac24a96c,
producer SHA25650c628222d6c122f5e7fca026eb3586911d00c1fb690b257d925e11d6ceae84a.
The source receipt itself remains root-private on TrueNAS; retained sanitized
metadata contains only job/task IDs, status, schedule and timestamps.

R2's separate six-source package explicitly selects and records historical job
IDs. It reuses the unchanged strict date/order/01:00–04:15 validator against
those genuine selected jobs, all later than actual current archive timestamps.
At admission the ordinary forced read-only observer must independently return
current task metadata exactly equal to the pinned capture and all-success;
new, failed, running or changed jobs refuse. Producer identity, exact receipt
hash, same cycle and<=7200s observation age are mandatory. Current Proxmox
inventory, exact LXC110 mirror, retained real zstd identities/age, whole all-guest
Proxmox job, current consumer, model, resource, health and recovery gates remain.
No fallback to unverified success or renewal of the actual scan time exists.
The guardian needs no remote history query to restore production.

151 offline tests pass, including seven historical-chain positive/adversarial
cases: late redundant success, current job drift/failure, missing or failed
predecessors, schedule/date/chronology drift, stale/future/wrong-producer receipts
and newer archives. A backup-only source rehearsal before arming must pass on
actual host sources; it is not model admission or a claimed model result.

Under existing explicit Stream A approval, cancel only the verified unclaimed
R1 reservation while preserving its immutable failure/owner evidence, install
R2 separately, reserve distinct clear capacity and fresh five entry plans, bind
the exact authenticated history and retained real scan, and arm one new future
model clock. R1 source/card/timers stay historical and are not reinstalled.
No model code, GPU/driver/package/boot, backup, credentials or permissions are
changed by this source correction. Continue through actual model result and
restoration; no new conversational approval is missing.
