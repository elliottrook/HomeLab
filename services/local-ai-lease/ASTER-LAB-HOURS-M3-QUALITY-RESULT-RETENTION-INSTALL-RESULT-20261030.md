# M3 quality-result retention install result — 2026-10-30

## Decision

Installed inactive and validated. No model request, booking, lease acquisition,
guest restart or production-service restart was part of this installation.

## Result

- Source commit: `c1916f96`.
- Installed release manifest SHA-256:
  `d853b0f05382d1cebfd6c6d9a1d30068e3d6295a918f62ac41bea6ff1e2a0951`.
- Installed runner SHA-256:
  `ee4ab4c389e7c9cffd3cbcdd2ea7f7dbf882ccfc49312af04a3d52dd666f5abf`.
- Installed workload registry SHA-256:
  `94d70bbd5c1b791b70c76f6c78a9ce55d81922958520c9f1f68de4ee4013bedf`.
- Installed transaction SHA-256:
  `dc92e35ee11ed12cd5d842282027adbcbf4c24611ba6b4be64a820fa951f0677`.
- 29/29 target-Linux focused tests pass and all 32 release pins match.

The first two target-test invocations failed before acceptance because the
packet initially used absolute unittest paths and then omitted the public
fixture. Both attempts triggered the installer trap, restored every prior byte
from a new root-only checkpoint and re-enabled the dispatcher. The corrected
packet included the fixture and completed. All three checkpoints are retained.

## Postcheck

The lease is `ready`; drain state, drain lock and shared operation lock are
absent; LXC110 has no candidate mount; LXC104/110/116 and Aster Agent, accepted
9B, Speech, Proxmox daemons, dispatcher and Doctor are healthy. No M3 or 35B
process remains.

The next public booking may now distinguish a genuine quality rejection from
an invalid result and retain the exact public result under root custody. It
still grants no automatic routing, calibration, holdout or promotion authority.
