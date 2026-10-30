# M3 GPU-holder stability correction — 2026-10-30

Status: **SOURCE CORRECTED; SPENT BOOKING NOT RETRIED**

Booking `aster-stream-a-m3-35b-20261030-1030` passed admission, drain, mount,
candidate startup and recovery, but stopped before public-case requests with
the newly bounded owner error `M3_CANDIDATE_RESIDENCY_PROC_AMBIGUOUS`. Its
terminal result is `OWNER_TRANSACTION_FAILED_RESTORED` with
`production_restored=true`.

The first race correction was still host-wide: it invalidated an entire
snapshot when any unrelated process closed any file descriptor during the
scan. On a normal busy Proxmox host, three complete snapshots could therefore
all be ambiguous even though the candidate's GPU-holder identity was stable.

The observer now ignores only processes or descriptor entries that have
already disappeared, because they cannot remain GPU competitors. Permission,
encoding or other I/O ambiguity still fails closed. It then requires two
identical exact GPU-holder snapshots within three reads before evaluating the
fixed one-holder count, executable, LXC110 cgroup, MainPID and RSS checks. A
changing or unreadable holder set remains `proc_ambiguous`.

The Lab Hours discovery suite passes 31/31. The focused observer, recovery,
M3 transaction, guardian and runtime suite passes 29/29. Corrected pins are:

- observer `277fa96f411737e265f3fcfb3169d00a3dfb0289d5b075150f677b04469ce340`;
- workload registry `b7004ae90e5e15864430361208f2759d250e92082a3688363ac5a2f0270b6fd4`;
- release manifest `e00c4c0f0ad177ff541e2effe533fef8de2b2d9eb38068f4fbea52fe748b2701`.

This correction does not schedule another booking, call a model, open private
data or enable routing.
