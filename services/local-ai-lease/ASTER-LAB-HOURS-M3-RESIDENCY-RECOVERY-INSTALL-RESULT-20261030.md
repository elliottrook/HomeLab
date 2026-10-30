# M3 residency and recovery install result — 2026-10-30

## Result

**PASS — corrected baseline installed inactive from `d6b2af2a`.** The spent
08:00 booking was not retried or rescheduled. The prior observer, recovery,
transaction, workload registry and release manifest are retained root-only at
`/var/lib/local-ai-lab/checkpoints/m3-residency-d6b2af2a`.

Before installation, the deadline guardian had completed the retained drain's
recovery. Independent checks found LXC104/110/116 running; Aster Agent,
accepted 9B/SYCL with authentication, Speech, News and EPUB healthy; the lease
ready; and no candidate mount/process, drain state/lock, lease state/lock or
operation lock. Doctor completed healthy with exit zero.

The five installed candidate hashes match the source card:

- observer `f5afa41a776a488a066daf4f92376061ab347dc02e0efa7ff69081b1cdbf7792`;
- recovery `992e7d4bbf8b0f62cc72546dae9ad2ab9622830deef78d096afc028c2b5eb3f4`;
- M3 transaction `5fe269becea9ac1bf4d1179bd81df2e64453a509a5070f373f435652a49cb272`;
- workload registry `c539956c3e04aa0fb2c2912e799e7b84c30c0b85cd92111f7fc4665a590d5880`;
- release manifest `ba030a7353fd066f63f46310df31100d427f42d5e3b00240f4594e6ab16357b6`.

All 32 installed manifest pins match. The clean target-side observer,
recovery, M3 transaction, guardian and runtime suite passes 28/28, including
bounded residency reasons, ordinary `/proc` race retry and collected-unit
recovery. Production and Doctor remain exact after installation.

No booking, service stop, restart, mount, model request, promotion, private-set
access or routing change occurred during installation.
