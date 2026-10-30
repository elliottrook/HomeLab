# M3 October 30 35B booking and static preflight — 2026-10-29

The authoritative Lab Hours ledger reported the complete 05:00–06:15 PDT
execution-and-recovery window clear after the overnight backup/pull chain and
the separate protected B60 booking. Exact workload
`m3-joint-semantic-35b-public-v1` is booked as
`aster-stream-a-m3-35b-20261030-0500` from 05:00 to 06:00 with the registered
900-second recovery reserve through 06:15.

Static preflight matched the five corrected installed hashes from platform
commit `309ce983`, resolved the exact workload through the joined admission
path, and proved a consistent 2,700-second transaction/preflight/guardian
budget plus 3,600-second minimum booking. Dispatcher, Doctor, Proxmox daemons,
lease readiness and absence of operation lock, drain state and drain lock pass.

This is conditional GO only. At claim time the runner must independently
recheck the ledger, exact release manifest, whole-host lease, shared lock,
production health, schedules and competing processes. Any drift or uncertainty
must fail closed. The run cannot promote a model or enable routing. A one-time
06:15 reconciliation is active and will not retry or reschedule the workload.
