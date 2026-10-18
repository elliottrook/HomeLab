# F2 recurring daily supervised read-only scan protocol

**Status: DAILY PROTOCOL APPROVED / NO HOST INVOCATION IN THIS CARD.** This
card defines a bounded recurring daily protocol. Each cycle still requires
fresh gates; approval does not carry forward a failed or uncertain result and
does not authorize a lease, receipt, service stop, timer, drill or model call.

## Exact bounded operation

For each completed backup cycle, an operator present on the Proxmox host may
invoke the installed diagnostic guard at most once with
`--read-only-authorized` between **01:10 and 01:19 America/Vancouver**, after
that cycle's fresh gates pass. There is never more than one attempt per
completed cycle.
The outer process-group deadline is the earlier of 20 minutes from child start
or **01:40 Vancouver**. The operator must not manually start a backup, TrueNAS
pull, lease, maintenance task or competing scan during the operation.

The guard is the installed diagnostic candidate at:

`/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py`

Required installed guard hash is
`6d18f9c88067edb11a04eae84d7c5fb3f0d3f4eb518b359f57277205539f3a2f`,
root:root mode `0644`. The following dependency hashes must be rechecked
immediately before invocation:

| Path | Required SHA-256 |
|---|---|
| `/usr/local/sbin/local-ai-lease` | `67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c` |
| `/usr/local/libexec/local-ai-lease/retained_archive_timing_observer.py` | `f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363` |
| `/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py` | `5cfe1a53578250590ee656c7b5a808b6b94a60650255efa4857d1fdd94507acb` |
| `/usr/local/libexec/local-ai-lease/host_exclusion.py` | `f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563` |
| `/usr/local/libexec/local-ai-lease/retained_archive_integrity.py` | `11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5` |
| `/usr/local/libexec/local-ai-lease/fixed_source_adapters.py` | `8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9` |

All files must be regular, single-link, root:root, with the documented modes.
Any drift is a hard stop before invocation.

## Fresh-cycle gates

Immediately before the bounded operation, record only sanitized metadata:

1. The fixed Proxmox whole backup job `backup-49999802-1365` completed
   successfully at 00:30 for the named cycle, with no task error.
2. Guest 104, 110 and 116 completion records are from that same cycle.
3. The exact current-cycle archive identities, sizes and ctimes resolve to
   `backups:backup/vzdump-lxc-{104,110,116}-YYYY_MM_DD-HH_MM_SS.tar.zst`.
4. TrueNAS task 1 completed successfully after the backup; fixed tasks 1/3/2
   remain enabled at 01:00/02:00/03:00 with the pinned string schedule values.
5. The Proxmox host is quiet: suitable one-minute load, no `vzdump`, `zstd`,
   `rsync`, `pbs-client` or `proxmox-backup` process, and no running TrueNAS
   rsync task.
6. `local-ai-lease status` is `ready`; neither whole-host nor application
   lease/lock/receipt path exists.
7. LXC104/110/116 and News services/timers are running as expected; backup and
   News schedules are unchanged; diagnostic/watchdog effects remain disabled.
8. The operator confirms no manual backup, pull, lease, maintenance or scan
   overlaps the operation.

Any missing, late, contradictory or uncertain gate means **skip**. Do not
invoke the guard or retry that cycle. Competing work or operator absence also
means skip.

## Result and failure recording

On success, retain only the complete three-row result with bounded archive
identity, size, ctime, test start/finish, elapsed time and exit `0`. A complete
three-row result is required; partial output is not a pass.

On failure, record the guard's content-free `state=no_go`, `error_class` and
phase (`preflight`, `observer` or `result`), plus the bounded pre/postcheck
metadata. A phase is diagnostic only and does not identify the failed
predicate. Never expose child output, archive contents, paths beyond the
approved identity fields or secrets.

Afterward verify no scanner child, lease, lock, receipt or changed schedule
remains. Any uncertain postcheck is **NO-GO** and requires operator
reconciliation; do not rerun in the same cycle.

The daily automation must pause after the first complete three-row exit-zero
result, or immediately when installed/source drift, a safety failure,
uncertain postcheck, competing work, or any condition requiring review is
detected. Resumption requires review of the card and a fresh explicit decision.

This card produces no trusted F3/F4 receipt, does not arm F6, does not stop a
service, does not run the full-stop recovery drill, and does not authorize or
promote an A1 model benchmark.
