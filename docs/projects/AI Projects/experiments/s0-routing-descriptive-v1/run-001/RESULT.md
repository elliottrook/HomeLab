# Run 001 — failed closed before mutation

2026-09-26. The coordinating task executed the authorized one-shot once from
`6715a05`. The preserved five-record journal verifies its SHA256 chain: unit and
path preflights completed; health returned child-failed; final stage preflight,
mutation_attempted=false, manual_recovery_required=false. There is no create/run
intent, ownership receipt or remote stop. No accepted corpus was evaluated.
The original journal is untouched; this directory contains exact non-secret copies
and a separate evidence manifest. Never reuse/delete/alter the original journal.

The journal retains output hashes, not raw stderr. Consequently the exact failed
health assertion cannot be proved from it alone. The coordinating task's subsequent
read-only diagnosis reports an additional `code-server-pre-authentik` container and
in-guest memory.max=`max`. Both violate assumptions in the first collector: an
exact nine-name inventory and a finite integer guest-root cgroup memory limit.
These are evidence of invalid collector assumptions, not household service failure.

Reported actual guest state is running; LXCFS MemTotal is 4 GiB. Host-side
`pct status 100 --verbose` reports maxmem=4294967296, memory approximately739872768,
maxswap=536870912 and swap=0. MemAvailable was approximately3504251 KiB. These are
coordinator-provided observations, not fresh queries made by this preparation task.

Outcome: inconclusive confinement feasibility, safe read-only abort. No canary or
unit cleanup was required because mutation was never attempted. A second attempt
requires a new candidate, exclusive journal/approval identity, absent-unit/path
preflight and new explicit approval. The original authorization does not permit an
automatic retry. No SSH/DNS/LXC action or remote Git write was made while recording
this evidence.
