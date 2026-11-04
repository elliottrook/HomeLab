# D4 candidate-g fresh booking result — 2026-11-04

## Decision

**TIMED TEST: GO — SCHEDULED / CONDITIONAL.**

Jason approved the exact service-stop/start boundary. Booking
`aster-stream-a-sa3-envelope-20261104-0930` is recorded in the authoritative
Lab Hours ledger as `scheduled` for 09:30–11:00 host-local with workload
`sa3-evidence-envelope-quality-v1` and a 900-second restoration buffer.

The immediately preceding ledger check was clear. All five installed hashes,
the ready lease, absent shared state/locks, active dispatcher/Doctor/Proxmox
daemons, running LXC 104/110/116, active Aster Agent/accepted llama/Speech and
the corrected EPUB timer-inactive/worker-activating state passed static
preflight.

Runtime remains fail closed. The runner must atomically claim the exact booking
and recheck backup, pins, lease, locks, health and conflicts before any stop.
It permits one 14-request candidate-g transaction, unconditional restoration
and zero retry or extension. No model/backend change, deployment, routing
promotion, tool authority or recurring schedule is included.
