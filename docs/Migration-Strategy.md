# Migration Strategy Moved

`Current-Network-Baseline.md` is the current source of truth for network
topology, VLAN placement and migration state.

This document was retired 2026-09-01 because it had fallen significantly out
of date (last updated 2026-08-08, still describing storage hosts as
"remaining on Trusted pending later migration windows" when they have long
since moved to Servers VLAN 20) and duplicated information that
`Current-Network-Baseline.md` maintains more accurately. Do not add
migration-status updates here; update `Current-Network-Baseline.md` instead.
The former content, including the phase-by-phase migration plan and
rollback philosophy, remains available in Git history.
