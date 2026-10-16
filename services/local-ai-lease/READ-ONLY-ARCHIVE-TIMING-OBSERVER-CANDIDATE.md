# Fixed-source archive timing observer — source-only candidate

**Motivation:** the October 16 chat heartbeat arrived at 01:10 but left no
complete three-archive result before its 01:20 start cutoff. That cycle is
UNKNOWN / NO-GO. The cause of the missing execution record is unproved; a
scheduler firing is not evidence that a long-running scan completed.

`retained_archive_timing_observer.py` is a one-shot, read-only wrapper around
the existing fixed-source producer. It uses the producer's exact 00:30 job,
guest-log, 01:00 task-1, current-cycle inventory and deadline checks, and
passes a no-op save callback. It cannot create the root-owned admission
receipt. It refuses non-root execution and existing whole-host or application-B60
lease state/locks. On success
it prints only archive VMID, volid, size, ctime, test start/end, elapsed
milliseconds and exit code; on failure it prints a bounded error class with
no exception message or raw source output.

Source SHA-256:

- `retained_archive_timing_observer.py`:
  `857e2f39f389fea464f7852f19fe8f37df48c883db84ebd5b62f6fcf997bd62d`
- `test_retained_archive_timing_observer.py`:
  `9f44bbe67b7e92536a8e0f1676026eb617afbe5019a7301c1e877a8ce0e451ae`

Offline focused suite: 16/16 tests passed across the observer, producer and
retained-integrity modules. No backup archive, Proxmox, TrueNAS or model was
contacted. The observer is **not installed, enabled, scheduled or run**.

The source now rejects either lease's state or lock, including a broken
symlink. This closes a pre-start conflict gap; it does not prevent a lease or
backup from starting after the observation begins. An unattended release still
requires a tested host-side exclusion mechanism, explicit load and
competing-job checks, and an independent process deadline. Do not schedule
this candidate merely because its pre-start checks pass.

Before any future live timing observation, the platform owner must review
the source and dependency hashes, select an execution mechanism that reliably
starts after task 1 but before 01:20, set a whole-process deadline no later
than 01:40, retain the content-free result, prevent overlap with other leases
and backups, test the exact installed path on Linux, define rollback, and seek
the appropriate bounded host-change approval. A disabled candidate service
and timer may be considered, but neither is part of this source checkpoint.
Do not relabel this observer output as F3/F4 trusted admission evidence or
backfill an October 16 receipt.
