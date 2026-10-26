# Stream A evaluation composition inactive installation V3 — 2026-10-25

Result: **PASS — INSTALLED INACTIVE**

The exact V3 transaction from platform source `b21a6227`, card `4d682e6f`
and transaction `3273a2ec` completed at 2026-10-26T04:46:49Z. The clean
archive SHA-256 was
`aaa0190099c1643224846310a468fe12ecae1bf25bd9c42638674f32621bdade`.

Observed result:

- 96/96 target-Linux tests passed;
- all 13 pinned host/guest paths matched their hashes, custody and modes;
- the host composition imported through only the two fixed module roots;
- LXC104 and LXC110 each returned the exact inert `disabled` result;
- the whole-host lease remained exactly `ready` with no F6 state or lock;
- all F6 units remained disabled and inactive;
- production services and controls remained healthy; and
- the approved October 26 F2 timers remained enabled and active for 01:15 and
  01:20 PDT.

The root-only recovery checkpoint is
`/var/lib/local-ai-lab/checkpoints/stream-a-evaluation-composition-b21a6227-20261026T044649Z`.
No receipt, lease, consumer stop, model request, F2 mutation or F6 runtime
activation occurred. The next live dependencies remain fresh F3-F5 evidence,
an exact activation/recovery card and separate effect approval.
