# M3 mount canonicalization install result — 2026-10-30

## Result

**PASS — corrected baseline installed inactive from `d411ca18`.** The spent
05:00 booking was not retried or rescheduled. The prior observer, workload
registry and release manifest are retained root-only at
`/var/lib/local-ai-lab/checkpoints/m3-mount-d411ca18`.

Before installation, the exact transaction-owned residual mount was removed,
LXC110 was restarted, and the installed rescue path restored the drained
production stack. Independent postchecks then found LXC104/110/116 running;
Aster Agent, accepted 9B/SYCL with authentication, Speech, News and EPUB
active; the whole-host lease ready; and no mount, 35B process, drain state,
drain lock, lease state or operation lock. A fresh Doctor run completed
healthy with exit zero.

The three installed candidate hashes are:

- observer `e30ed0e5faa2949f7734e4b61488092d8c0d178484db689b8b684eeac5449cff`;
- workload registry `ca25a6378b4dcd7501dbe4146544cd8813a08c64ae037302f9251c88a3793ddd`;
- release manifest `7813b11746144e2cafaf0502f71be4ef89002b4fe77f5c070d9599bc67454a22`.

All 32 installed manifest pins match. The clean target-side observer,
recovery, M3 transaction, M3 guardian and runtime suite passes 27/27,
including the real reordered mount spelling and joined synthetic completion.
The Lab Hours Doctor passes after installation and production remains exact.

No booking, model request, model promotion, threshold selection, private-set
access or automatic routing occurred. A future live gate requires a fresh
booking and must not reuse this failed reservation.
