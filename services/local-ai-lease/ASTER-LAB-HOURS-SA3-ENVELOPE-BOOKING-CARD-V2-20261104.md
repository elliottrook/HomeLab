# SA3 candidate-g fresh booking card v2 — 2026-11-04

Status: **static GO; exact service-stop/start decision pending**

- booking ID: `aster-stream-a-sa3-envelope-20261104-1230`
- owner/workload: `aster-stream-a` / `sa3-evidence-envelope-quality-v1`
- window: `2026-11-04T12:30:00-07:00` to `2026-11-04T14:00:00-07:00`
- attempts/retries/extensions: 1 / 0 / 0

At 11:15 host-local the authoritative ledger reported the complete window
clear. Reservation must repeat that check immediately before writing.

Unlike the spent 09:30 card, v2 requires the actual installed
`lab_hours_reserved_runner.load_manifest()` verifier before reservation. It now
accepts all 34 installed pins, including EPUB source `6103da31…13ad`, validator
`094d588b…bf31` and release manifest `4d8e7db2…2b92`. The target focused suite
passes 22/22 and the predecessor manifest remains in a root-only checkpoint.

Runtime still requires atomic claim, ready lease, absent shared locks/state,
current backup and healthy production. The one transaction may stop and restore
only the declared consumers and issue exactly 14 candidate-g requests. Any
failure is terminal without retry. No model/backend change, deployment,
routing promotion, tool grant or recurring schedule is included.
