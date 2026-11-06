# SA4 transaction inactive-install result — 2026-11-05

## Result

The separately approved seven-file inactive installation completed and passed
independent validation. Result SHA-256 is
`d0e2fbcddc02aa5636fcb7f267826e31040885c0435756eb4e770c5e97df0c9d`.

- Four operation/observer producers were created exclusively on LXC 104.
- The independent postcheck validator and ledger reconciler were replaced
  atomically after their exact predecessors were retained root-only under
  `/var/lib/aster/sa4/source-checkpoints/transaction-rc1`.
- The bounded observer signer and its previously absent parent were created
  exclusively on Proxmox.
- All seven installed files are root:root mode 0644, single-link regular files
  with their packet-pinned SHA-256 values.
- All isolated imports passed. The four effect-capable source bindings remain
  exactly `unconfigured`.
- The signer passed only a fake-runner self-test. Its private key was not read
  or invoked and no signature was produced.

The canary remained at its pre-install drifted digest
`19b4e02d…df1a`. No repair checkpoint, ledger, grant, claim, receipt, temporary
target or SA4 process exists. LXC 104/110/116, Aster Agent, the accepted
llama.cpp/SYCL service, Speech, News timers, Lab Hours dispatcher/Doctor,
Proxmox schedulers and the accepted ongoing EPUB baseline remained unchanged.
No service was restarted, reloaded, stopped or started. Pre-existing historical
failed transient units were not altered or reclassified by this installation.

The canonical seven-row result passes the fail-closed verifier; the full source
suite passes **126/126**. Temporary Proxmox staging was removed after success,
while rollback bytes remain retained.

## Boundary

This installed source remains inactive. It authorizes no signature, grant,
checkpoint, target change, repair, rollback, route, service action or model
call. Next is the live zero-effect dry-preflight design and review. The first
real repair remains a separate exact immediate approval gate.
