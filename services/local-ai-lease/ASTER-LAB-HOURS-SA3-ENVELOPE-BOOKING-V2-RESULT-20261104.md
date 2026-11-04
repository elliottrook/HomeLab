# SA3 candidate-g booking v2 result — 2026-11-04

Status: **GO — scheduled / conditional**

Under Jason's standing Stream A candidate authorization, booking
`aster-stream-a-sa3-envelope-20261104-1230` is authoritative and scheduled for
12:30–14:00 host-local with a 900-second restoration buffer.

Immediately before reservation, the ledger returned clear, the lease was
ready, shared state/locks were absent and the actual installed reserved-runner
manifest verifier accepted all 34 pins. This closes the deterministic defect
that stopped the 09:30 booking.

Runtime still requires atomic claim and fresh backup, pin, lease, lock, health
and conflict checks. One transaction, zero retries/extensions and unconditional
restoration remain fixed. No model/backend change, deployment, routing
promotion, tool grant or recurring schedule is included.
