# M3 October 30 08:00 35B residency NO-GO and correction — 2026-10-30

## Measured result

Booking `aster-stream-a-m3-35b-20261030-0800` claimed once at 08:00 PDT and
ended `NO_GO` at 08:48:01. The corrected mount path passed and the transient
35B service reached its health endpoint, but the run stopped before all 24
public-case requests with owner error `M3_CANDIDATE_RESIDENCY_INVALID`.

Recovery stopped and collected the transient unit, then its unconditional
`reset-failed` command returned nonzero because the unit was no longer loaded.
The booked terminal projection consequently records phase `owner-transaction`,
code `COMPETING_PROCESS:m3_joint_semantic_35b` and
`production_restored=false`. No public result exists and the quality gate was
not measured.

## Actual recovery state

The independent deadline guardian retained ownership and restored the drained
stack at the transaction boundary. Direct postchecks show LXC104/110/116,
Aster Agent, accepted 9B/SYCL with authentication, Speech, News, EPUB,
dispatcher, Doctor, `pvescheduler` and `pvestatd` healthy. The lease is exactly
ready and no candidate mount/process, lease state/lock, operation lock, drain
state or drain lock remains. The immutable terminal record is not rewritten;
the later evidence establishes recovery only.

## Deterministic correction

The observer's `/proc` GPU-holder scan treated any disappearing file
descriptor from any process as a failed residency proof. The same ordinary
race was reproduced read-only on the target. Platform source commit
`d6b2af2a` now retries up to three complete snapshots while preserving the
exact one-holder, executable, LXC cgroup, MainPID and RSS requirements. It also
returns a bounded content-free reason for any later residency failure.

Recovery now calls `reset-failed` only if the candidate remains after `stop`;
an already collected transient unit proceeds to the mandatory absence proof.
The Lab Hours discovery suite passes 31/31 and the focused observer/recovery/
M3/runtime suite passes 28/28. Platform result commit `124db886` records the
inactive five-file installation, 32/32 installed manifest pins and rollback
checkpoint `/var/lib/local-ai-lab/checkpoints/m3-residency-d6b2af2a`.

The spent booking was not retried or rescheduled. M3 remains open at the
24-case public gate; calibration and holdout remain closed and automatic
routing remains off.
