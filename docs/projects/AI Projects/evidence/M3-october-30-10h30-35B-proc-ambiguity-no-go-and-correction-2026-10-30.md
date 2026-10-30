# M3 October 30 10:30 35B proc-ambiguity NO-GO and correction — 2026-10-30

Booking `aster-stream-a-m3-35b-20261030-1030` claimed once at 10:30 PDT and
ended `NO_GO` at 10:35:08. Admission, drain, mount, candidate startup and
recovery passed, but the run stopped before the 24 public requests with the
exact bounded owner error `M3_CANDIDATE_RESIDENCY_PROC_AMBIGUOUS`.

The terminal evidence correctly records phase `owner-transaction`, code
`OWNER_TRANSACTION_FAILED_RESTORED` and `production_restored=true`. Direct
postchecks confirm the whole-host lease ready; no mount, candidate process,
drain state/lock, lease state/lock or operation lock; and healthy accepted
9B/SYCL, Aster Agent, Speech, News, EPUB, dispatcher, Doctor and Proxmox
daemons. No public quality result exists.

The earlier race correction invalidated a complete host scan whenever any
unrelated process closed any descriptor. On the busy Proxmox host, three scans
could all be ambiguous even though the GPU-holder identity was stable.
Platform source commit `ddc6536b` now ignores only processes and descriptors
that have already disappeared, fails closed on every other read ambiguity,
and requires two identical exact GPU-holder snapshots within three reads.
The fixed one-holder, executable, cgroup, MainPID and RSS requirements remain.

Platform result `3632b7bc` records the inactive installation, 29/29 target
focused tests, all 32 manifest pins and root-only rollback checkpoint
`/var/lib/local-ai-lab/checkpoints/m3-gpu-holder-ddc6536b`. The spent booking
was not reused. M3 remains open at the public gate, calibration/holdout remain
closed and automatic routing remains off.
