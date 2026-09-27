# V5 exact approval gate

No action in this release packet is self-authorizing. A human approval must name
the frozen release-manifest SHA-256
`1ae0bdeda1e5043a98065b4de8515d4a75045d936271a79f6f77cd80059c8a8c`
and authorize the one mutation window described in `PREFLIGHT.md`.

Approval permits one stage/create/boot/capture/stop-and-retain sequence for VM122.
It does not permit a retry, a changed artifact, corpus/label tuning, network or
credential attachment, promotion, cleanup, mutation of VMs118–121, or Git push.
Any preflight drift stops the operation and consumes no authority to improvise.
