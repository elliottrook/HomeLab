# SA4 v4 effect-controller preflight NO-GO — 2026-11-05

Jason approved the exact v4 canary repair. Fresh pre-effect checks confirmed
all five installed source hashes, the unchanged drifted canary, absent ledger,
absent operation lock and emergency stop, a ready whole-host lease, running
LXC 104/110/116 and healthy bounded core services.

The first failed gate was transaction ownership across the independent
observer pause. The installed root transaction owner is a stateful library. No
reviewed one-shot controller exists to preserve its in-memory phase graph while
the independent receipt is signed on Proxmox and then returned to LXC 104.
Ad-hoc shell or inline-Python orchestration would create a new, unreviewed
effect path outside release packet `f08027af…53a0`.

The run therefore stopped before authority creation. No private key, signer,
signature, grant, ledger, checkpoint, runtime control, repair, rollback,
service action or restart occurred. The canary remains
`19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.

This approval is spent by the pre-effect NO-GO. The safe next action is a
fixed, hash-pinned worker/controller pair with a bounded receipt-proof protocol,
joined disposable success/rollback/uncertainty tests and a reversible inactive
installation review. Only then can a fresh exact repair approval be requested.
