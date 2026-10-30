# M3 GPU-holder stability install result — 2026-10-30

**PASS — installed inactive from `ddc6536b`.** The spent 10:30 booking was
not retried. The prior observer, workload registry and release manifest are
retained root-only at
`/var/lib/local-ai-lab/checkpoints/m3-gpu-holder-ddc6536b`.

Installed hashes match the reviewed source:

- observer `277fa96f411737e265f3fcfb3169d00a3dfb0289d5b075150f677b04469ce340`;
- workload registry `b7004ae90e5e15864430361208f2759d250e92082a3688363ac5a2f0270b6fd4`;
- release manifest `e00c4c0f0ad177ff541e2effe533fef8de2b2d9eb38068f4fbea52fe748b2701`.

All 32 installed manifest pins match and the clean target-side focused suite
passes 29/29. Production remained exact: accepted 9B/SYCL, Aster Agent,
Speech, News, EPUB, dispatcher, Doctor and Proxmox daemons are healthy; lease,
mount, candidate process and drain/operation state are absent.

No booking, stop, restart, mount, model request, promotion, private-set access
or routing change occurred during installation.
