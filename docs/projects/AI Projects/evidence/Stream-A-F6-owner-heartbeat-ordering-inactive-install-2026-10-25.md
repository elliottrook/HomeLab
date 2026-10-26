# Stream A F6 owner-heartbeat ordering — inactive install

**Observed:** 2026-10-25 20:59 PDT

**Platform source:** `039089695fb8b4cd020f769a90c0b93156e93531`

**Platform result:** `13d30def`

**Decision:** **PASS — INSTALLED INACTIVE**

The approved one-file correction is installed on Proxmox at
`/etc/systemd/system/stream-a-evaluation-owner-heartbeat.service`. Its
independently reread SHA-256 is
`7bbb32a64a73b8797f34df934f9f06932c0706f93dc078b08bbc2c737d364f1e`,
with `root:root 0644` custody and one regular link. The unit now orders itself
after `stream-a-evaluation-owner.service` as well as requiring it, so future
arming cannot race the owner identity check at initial heartbeat startup.

The replaced unit is preserved in root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/f6-owner-heartbeat-ordering-03908969-20261025T2057`.
Its SHA-256 remains
`6c7777506df7aa2b58e62e3da7fb354859b6487e99441b4445c8a2a537df2ad5`.

Validation passed before and after replacement:

- `systemd-analyze verify` accepted the owner, heartbeat and watchdog set;
- focused source tests passed 4/4;
- all five F6 services/timers stayed disabled and inactive;
- the whole-host lease stayed `ready`, with no lease, lock, identity or
  evaluation state;
- the October 26 F2 prepare/final timers stayed enabled and active for 01:15
  and 01:20 PDT.

The first remote transaction invocation was an inert no-op. An immediate
independent hash/checkpoint read detected it before any status was claimed.
The same approved transaction was then run from a separately staged script and
the independent postchecks above passed.

This closes the owner-before-heartbeat installation defect only. It does not
arm F6, start a timer, acquire a lease, stop a consumer, run candidate H or M3,
invoke recovery, call a model, or advance F2–F5.
