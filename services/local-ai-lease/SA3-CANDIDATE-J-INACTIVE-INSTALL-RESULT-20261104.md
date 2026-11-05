# SA3 candidate-j inactive installation result — PASS — 2026-11-04

The exact inactive candidate-j package installed successfully without a
booking, model call, service stop or restart. Bundle `124f56b3…a746` bound
platform commit `1e953c1b`, Stream A commit `272d4e55` and 14 source entries
plus its canonical manifest.

The installer replaced four exact host baseline files, added three candidate-j
host modules, and added the five-file self-contained runtime plus wrapper to
LXC110. It retained root-only host/guest checkpoints and independently proved
all 39 installed release pins. The result was:

- `state=installed-inactive`;
- `host_replaced=4`, `host_added=3`, `guest.added=6`;
- `service_restart=false`, `workload_effect=not-attempted`;
- `booking=absent`, checkpoint retained.

Post-install reads matched every candidate-j hash. The lease was exactly
`ready`; shared state and locks were absent; no candidate-j unit, process or
scope existed. LXC104/110/114/116 were running; Aster Agent, accepted 9B/SYCL
llama, Speech, pvescheduler and pvestatd were active. News ingest/digest timers
in LXC114 had valid last/next times. The two guessed host-side News unit names
were inactive because News is correctly hosted in LXC114, not because its
schedules failed.

The disposable Proxmox stage and transferred archive were removed after proof;
the deterministic source bundle remains reproducible and the rollback
checkpoints remain retained. Candidate-j is installed but inert. A live public
run still requires a conflict-free authoritative Lab Hours window, its own
exact booking, fresh lease/shared-lock admission and a bounded activation
packet. No route, authority or promotion follows from installation.
