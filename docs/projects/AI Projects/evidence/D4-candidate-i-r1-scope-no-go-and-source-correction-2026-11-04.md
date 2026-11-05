# D4 candidate-i R1 scope NO-GO and source correction — 2026-11-04

## Measured result

Candidate-i R1 claimed exactly at 17:30:00 and reached a restored terminal
NO-GO at 17:33:07, 187 seconds later. The bounded terminal records
`first_failure_phase=owner-transaction`,
`failure_code=OWNER_TRANSACTION_FAILED_RESTORED` and
`production_restored=true`. The existing content-minimized adapter projection
identifies `fixed candidate-i invocation mismatch`.

No scoreable result exists, no blind packet can be generated and R1 cannot be
retried. The root-custodied attempt retains its terminal and 1,630-byte stderr;
shared evidence records only its SHA-256
`a7ccedf008f8d3a92ac32a4f980f0a74a0eda7e164f54ba8630e334864e3ad1c`
and bounded failure. No prompt, answer, case identity, response body or raw
exception text is copied here.

## Restoration

The lease is exactly ready; drain state, drain lock and shared operation lock
are absent; no candidate process or scope remains. LXC104/110/116 are running.
Aster Agent, the accepted 9B/SYCL `aster-llama.service`, Speech, pvescheduler,
pvestatd, Lab Hours dispatcher and Lab Hours Doctor are healthy. Production
was restored and the attempt wrote no result.

## Cause and correction

The host adapter reused candidate-g's generic scope constructor and supplied
`aster-llama-sa3-<token>.scope`. Candidate-i's guest wrapper correctly requires
`aster-llama-sa3-i-<token>.scope`, so its exact invocation check failed before
the candidate workload.

Platform source now defines the candidate-i scope constructor locally, checks
the lease identity and proves the host command equals the guest wrapper's
exact name. Corrected adapter SHA-256 is
`80e7491b3d9bd3c457bf362baae97ba3377ac260dde1169933ddbdbc97cc1ee6`;
updated 36-pin manifest SHA-256 is
`05e41525f08f52597128b6523b92c1ed7de3316cee09e3e79f95d347d31eb65d`.
The focused cross-module suite passes 48/48. A two-file reversible inactive
installer is source-ready at platform commit `5e2190f6`; two clean bundles are
byte-identical at SHA-256
`8508bd336b18d05dc1f84efc3322f20a55e4460645ccc6ae0b1dcc6d8a63ab40`.

The next gate is inactive installation with exact predecessor checks,
root-only rollback custody, installed cross-module proof and fresh production
postchecks. Only after that may a distinct ledger-clear R2 booking be
considered. R1 is spent; there is no retry, automatic promotion, route,
authority or model/backend change.

## Inactive installation result

That gate now passes. The exact two-file archive installed the corrected
adapter and 36-pin manifest at their hashes above, retained both exact
predecessors in a root-only mode-0700 checkpoint and passed the installed
manifest verifier. The host scope function, actual guest command argument and
guest wrapper independently produced the identical candidate-i scope name.

The lease remains ready, shared state and locks are absent, all three core
containers and production services are healthy, temporary staging is removed,
and no service was restarted. The next gate is a distinct R2 booking after an
authoritative full-window ledger check; it is not a retry of R1.
