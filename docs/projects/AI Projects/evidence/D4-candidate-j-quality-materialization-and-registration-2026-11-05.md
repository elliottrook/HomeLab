# D4 Candidate-J quality materialization and registration — 2026-11-05

## Result

The strengthened untouched Candidate-J packet and its answer keys are now
materialized as separate canonical JSON artifacts. Their bytes reproduce the
frozen builder exactly:

- packet: 26,833 bytes,
  `53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132`;
- answer keys: 3,513 bytes,
  `cab2790dbb6e84b0bbe269c876dee8c4b116abfb4fa6fc2a119782e4b7fcd526`.

A new regression test compares both materialized byte streams to the builder's
canonical output. The complete Candidate-J source suite passes 40/40.

Platform commit `77abd40c5e5205c6c3d0d88151e6503d9ed5c2d8` registers the distinct inert
workload `sa3-evidence-matrix-candidate-j-quality-v1`. It pins only the packet,
shared deterministic contract, bounded selection runner and key-free quality
runtime. The answer keys, key-bearing source freeze, scorer, blind-review code
and decision code are excluded. Platform registry tests pass 10/10.

## Inert boundary

The new runner kind is deliberately absent from the reserved-runner admission
set. Nothing has been installed on Proxmox or LXC110, no Lab Hours window was
queried or reserved, and no model call, service stop, restart, route, authority
or promotion occurred. Registration cannot execute the workload.

Platform commit `20490b65e85a9afd35b0673f7018c72278051668` now completes
the fixed transaction, bounded host listener, key-free guest wrapper and
reserved-runner integration source. Release v16 pins the joined path and 57/57
focused platform tests pass. Nothing is installed.

Next is a deterministic reversible inactive installer and target proof. A live
attempt remains downstream of installation proof, an
authoritative conflict-free Lab Hours booking and fresh lease/lock admission.
