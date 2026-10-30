# M3 residency and recovery correction — 2026-10-30

Status: **SOURCE CORRECTED; SPENT BOOKING NOT RETRIED**

Booking `aster-stream-a-m3-35b-20261030-0800` passed the corrected mount
boundary and brought the transient 35B service to its health endpoint. It then
stopped before every public-case request with owner error
`M3_CANDIDATE_RESIDENCY_INVALID`. Recovery stopped and collected the transient
unit, then treated the expected nonzero `reset-failed` result for that absent
unit as `M3_FIXED_COMMAND_FAILED`. The guardian subsequently restored the
drained stack at the transaction deadline. No 24-case result exists.

Two deterministic source defects were observed:

1. The host GPU-holder scan returned false on any disappearing `/proc/<pid>/fd`
   entry, even for an unrelated process. The same ordinary file-descriptor race
   was reproduced read-only on the target after the run.
2. Recovery unconditionally called `reset-failed` after `stop`; a collected
   transient unit is no longer loaded, and systemd correctly returns nonzero.

The observer now retries up to three complete `/proc` snapshots on ordinary
process/descriptor disappearance, while every stable snapshot still requires
exactly one render holder with the fixed executable, fixed LXC110 cgroup,
valid container MainPID and bounded RSS. It exposes a content-free bounded
residency state so any later failure identifies holder count, executable,
cgroup, PID, RSS or persistent observation ambiguity rather than collapsing
them into one boolean. The transaction retains that bounded state in its owner
error.

Recovery now runs `reset-failed` only when the candidate is still present
after `stop`. An already collected transient unit therefore proceeds directly
to the mandatory candidate-absence proof; a remaining candidate still fails
closed.

The Lab Hours discovery suite passes 31/31. The focused observer, recovery,
M3 transaction, guardian and runtime suite passes 28/28. The corrected pins
are:

- observer `f5afa41a776a488a066daf4f92376061ab347dc02e0efa7ff69081b1cdbf7792`;
- recovery `992e7d4bbf8b0f62cc72546dae9ad2ab9622830deef78d096afc028c2b5eb3f4`;
- M3 transaction `5fe269becea9ac1bf4d1179bd81df2e64453a509a5070f373f435652a49cb272`;
- workload registry `c539956c3e04aa0fb2c2912e799e7b84c30c0b85cd92111f7fc4665a590d5880`;
- release manifest `ba030a7353fd066f63f46310df31100d427f42d5e3b00240f4594e6ab16357b6`.

This correction schedules no booking, performs no model request and grants no
routing, calibration, holdout or promotion authority.
