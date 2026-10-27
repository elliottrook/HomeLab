# Full-inference daytime two-pass qualification — 2026-10-27

Result: **PASS**

Jason authorized a disruptive daytime rehearsal using the completed October 27
Proxmox backup evidence. Stream A and the platform owner iterated on the installed
full-inference pilot until one unchanged candidate completed the entire transaction
twice.

The attempts identified and corrected exact deployed-path defects in lease-status
decoding, host-exclusion path selection, LXC runtime-mask observation, idempotent
restore replay, owner-scope fencing, guest-scope cleanup and the lab model alias.
The final packet passed 71 host tests and 5 LXC110 wrapper tests.

Accepted pass 1 ran from 08:47:31 to 08:49:20 PDT. Accepted pass 2 ran from
08:50:39 to 08:52:28 PDT. Each pass armed an independent guardian, acquired the
shared exclusion, masked and stopped Aster Agent, Speech, accepted llama.cpp/SYCL
and both News timers, proved the GPU boundary, ran exactly three authenticated
tool-free loopback requests, removed the lab scope, then restored and validated the
exact production stack.

The final independent postcheck found no drain state/lock, listener, lab process or
guardian. Aster Agent, accepted `aster-llama.service`, Speech and both News timers
were active; the timers were enabled. Production authentication succeeded. The only
render-node holder was the accepted b11429 llama server in LXC110's production
service cgroup. Model, binary and unit hashes remained `cd76ec20…2a13`,
`0404f751…e6c5` and `a4c75169…4cb3`.

This proves the daytime lab-hours isolation/workload/restoration transaction twice.
It used real current-cycle backup evidence but does not create or replace F2/F3
archive receipts. The October 28 F2 prepare/final timers remain active and enabled
for 01:15/01:20 PDT.
