# D4 candidate-g r8 complete and blind handoff — 2026-11-04

## Complete transaction

R8 claimed exactly at 16:15:00 and completed at 16:18:55 after 235 seconds.
The authoritative booking is `complete` / `COMPLETE`; the exact terminal binds
20 cases, registered workload `sa3-evidence-envelope-quality-v1` and
`production_restored=true`.

The root-custodied result is a root:root mode-0600 one-link regular file of
10,225 bytes with SHA-256
`c108cca3b29b3523bc9d23341ed55f767e8c5bbf973d11cfd4f652798dd8809b`.
The fail-closed reconciliation accepts exactly 20 frozen cases, 14 model
requests, zero retries, zero errors/effects, the fixed candidate/workload
identities, and no authority or automatic routing.

## Restoration

The lease is exactly ready; Doctor is healthy with zero codes; drain state,
drain lock, operation lock, candidate listener and candidate processes are
absent. Dispatcher, Doctor, EPUB and Proxmox services/timers are healthy;
LXC104/110/116 are running; Aster Agent, accepted 9B/SYCL llama and Speech are
active. Core and Lab Hours restart counts remain zero.

## Blind handoff

The reconciliation CLI created exact model-identity-blind packet SHA-256
`9fe494b93a0595714fe5f6e27b9ff4a3a5fbac08bfc0ea064eaa0436557aedac`
under private mode-0600 custody. Its content-free summary remains
`quality_decision=pending-independent-review`. Three independent reviewers are
assigned the same exact packet without model identity, answer keys, result
envelope or access to each other's judgments.

Transaction completion is not a semantic quality pass. No routing, repair,
tool grant, model/backend change or promotion follows unless the separate
blind-review decision passes its frozen boundary.
