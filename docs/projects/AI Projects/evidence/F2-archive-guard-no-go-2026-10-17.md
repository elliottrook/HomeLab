# F2 October 17 read-only guard — NO-GO without an archive result

**Evidence class:** one approved, supervised, read-only attempt; no retry.
**Decision:** F2 FAILED/UNKNOWN for this backup cycle. No three-archive
integrity/timing result was returned, so F3, the full-stop drill and A1 remain
blocked. This record does not infer which internal predicate failed.

The active Stream A heartbeat started at approximately 01:02 Vancouver.
Read-only preflight established:

| Check | Observed result |
| --- | --- |
| Fixed Proxmox job | `backup-49999802-1365` enabled, `00:30`, storage `backups`, whole-host `vzdump`; journal start 00:30:04 and successful finish 00:50:25 on October 17 |
| Guest completion logs | 104 at 00:35:34, 110 at 00:45:37, 116 at 00:49:02, all October 17 |
| Current archive inventory | 104: `backups:backup/vzdump-lxc-104-2026_10_17-00_34_35.tar.zst`, 1,996,765,839 bytes, inventory ctime 1792222475; 110: `backups:backup/vzdump-lxc-110-2026_10_17-00_39_39.tar.zst`, 43,595,548,989 bytes, ctime 1792222779; 116: `backups:backup/vzdump-lxc-116-2026_10_17-00_48_11.tar.zst`, 4,339,431,471 bytes, ctime 1792223291 |
| Archive paths | All three resolved via `pvesm path` under `/mnt/backups/dump`; observed file sizes matched inventory |
| TrueNAS task 1 | Initially RUNNING; subsequently SUCCESS, 01:00:01–01:06:56 on October 17, after the archives; tasks 1/3/2 remained enabled at 01:00/02:00/03:00 |
| Host gate before start | Lease `ready`; no lease/lock/retained receipt path; 104/110/116 running; News ingest and digest timers active/enabled; no matching busy process or running Proxmox task; one-minute load 1.41 at final preflight |
| Installed F2 custody | Manual controller, guard, producer, observer and three imported runtime files matched the exact release-card SHA-256 and root-owned modes |

At about 01:10:05 Vancouver, the operator invoked the installed
`f2_observer_runner_candidate.py --read-only-authorized` **once**. It exited
nonzero and returned only `{"error_class":"F2NoGo","state":"no_go"}` by the
first poll roughly 40 seconds later. The fixed guard intentionally suppresses
child stderr and collapses preflight and observer failures into this one
class. It retained **no** per-archive row, so the evidence cannot determine
whether an archive test began or which predicate failed. The operator did not
rerun the guard or invoke `zstd` separately.

Read-only postcheck found no matching `vzdump`, `zstd`, `rsync`, `pbs-client`
or `proxmox-backup` process; no lease/lock, archive-integrity or source-receipt
file; lease state `ready`; guests 104/110/116 running; the fixed Proxmox job
unchanged; and News timers active/enabled. A later diagnostic call to the
guard's **read-only** fixed-file, no-lease, quiet-host and TrueNAS-state
predicates passed. A later read-only replay of only the fixed inventory,
guest-log, whole-job and task-1 predicates returned three current artifacts
and `true` for all three completion checks; it used no archive probe or
receipt save. Those later observations do not reconstruct the failed
instant or turn the attempt into a successful scan.

No service was stopped, timer enabled, model called, lease acquired, receipt
written or backup schedule changed. The one-cycle approval is consumed. The
safe next action is an offline review of the guard's stage reporting and
source predicates, followed by a new exact run card and separate approval for
a **later** backup cycle. Do not retry an uncertain scan in this cycle. The
platform owner owns any future host release; Stream A owns this failure
record and downstream gate reconciliation.

A later source-only candidate at `codex/aster-lease-compat` commit `e5963762`
adds fixed `preflight` / `observer` / `result` failure phases for future scans.
The local suite passed 212 tests with four macOS root-custody skips. This
candidate is not installed and cannot recover the missing October 17 result.
