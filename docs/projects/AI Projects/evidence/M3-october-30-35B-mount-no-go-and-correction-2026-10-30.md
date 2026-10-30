# M3 October 30 35B mount NO-GO and correction — 2026-10-30

## Measured result

Booking `aster-stream-a-m3-35b-20261030-0500` claimed once at 05:00 PDT and
ended `NO_GO` at its 06:15 reconciliation boundary. It made **zero** 35B model
requests and produced no 24-case result. The retained first owner failure is
`M3_CANDIDATE_MOUNT_INVALID`; recovery then raised
`LXC110 mount state is foreign or uncertain`. The bounded terminal projection
records phase `owner-transaction`, code `SHARED_STATE_OR_LOCK_PRESENT` and
`production_restored=false`.

The remaining mount was not foreign. It had the exact transaction-owned host
source, guest target and `backup=0`/`ro=1` values. Proxmox canonicalized the
option order to `backup=0,ro=1`, while the observer required the source text
`ro=1,backup=0`. The same order-sensitive comparison therefore rejected both
the mount just created by the transaction and the automatic recovery attempt.

## Recovery

Independent checks found LXC110 stopped, Aster Agent and Speech drained, the
exact candidate mount present, no 35B process, and the full-drain state/lock
retained. After proving the mount's full semantic identity, the bounded
recovery removed that mount, restored root custody of the staged artifact,
started LXC110 and invoked the installed identity-bound rescue path.

Post-recovery evidence shows:

- LXC104/110/116 running;
- Aster Agent, accepted 9B/SYCL and its authentication probe, Speech, News
  timers and EPUB timer/worker healthy;
- dispatcher, Doctor, `pvescheduler` and `pvestatd` healthy;
- whole-host lease exactly `ready`;
- no candidate mount/process, lease state/lock, operation lock, drain state or
  drain lock.

The failed terminal record remains immutable; the later recovery evidence does
not rewrite it as success.

## Deterministic correction

Platform source commit `d411ca18` replaces raw-string mount comparison with an
exact source-plus-option-map comparison. It accepts reordered serialization
only; changed, duplicate, malformed or extra options still fail closed. The
Lab Hours discovery suite passes 31/31 and the focused observer/recovery/M3/
runtime suite passes 27/27. Platform result commit `76a7dd3c` records the
inactive three-file installation, 32/32 installed manifest pins and root-only
rollback checkpoint `/var/lib/local-ai-lab/checkpoints/m3-mount-d411ca18`.

This booking is spent and was not retried or rescheduled. M3 remains open at
the public gate; the holdout remains sealed and automatic routing remains off.
