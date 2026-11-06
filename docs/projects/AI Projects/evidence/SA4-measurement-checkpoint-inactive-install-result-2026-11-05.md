# SA4 measurement/checkpoint inactive install result — 2026-11-05

## Result

The approved two-file inactive installation completed on LXC 104. The
measurement owner now has SHA-256
`16644ee6dd42997bd07993ce0a850fc6620208e27b3c81ba03069f8ea91e5e2e`
and the checkpoint owner has SHA-256
`b0d8dff3bf7714cfc48e1dc5ea6e5e40db8ff815410c631e036880d79b307614`.
Both are root:root mode 0644.

The exact prior sources are retained mode 0600 under root-owned mode-0700
checkpoint `/var/lib/aster/sa4/source-checkpoints/measurement-owner-v1` at
their predecessor hashes `aa6ebfb2…e70f` and `fe8f6385…c45f`.

## Live read-only proof

The installed measurement owner ran once against plan SHA-256
`596417038ccef2ad49b689417437877820b2e918968dfd8a0eb97485c7eb6956`.
It opened only the compiled canary through
`O_RDONLY|O_NOFOLLOW|O_CLOEXEC`, proved stable path/descriptor identity and
measured the expected drifted bytes SHA-256
`19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`.
The canonical retained measurement evidence has SHA-256
`8566e1f93eb598e10b480c2b468b9018578b1dbbf33908a4f1e0746fade7821d`.

The result explicitly records `checkpoint_created=false`,
`grant_claimed=false`, `repair_effects=0`, `preflight_eligible=false` and no
authority. The checkpoint owner was not invoked. The repair checkpoint
directory remains empty and claim/receipt paths remain absent.

LXC 104/110/116, Aster Agent, accepted llama.cpp/SYCL, Aster Speech,
`pvescheduler` and `pvestatd` remain healthy. No service, model, route, signer
or private key changed or ran.

## Next step

The remaining release-candidate work is the controlled transaction rehearsal:
create the exclusive checkpoint from a fresh measurement, initialize and claim
one fresh signed grant, perform one atomic canary replacement, independently
observe the three fixed postchecks, reconcile the terminal receipt, and prove
rollback on a separate synthetic/failure branch. None of those effects is
authorized by this read-only result. The first live repair remains an exact
immediate approval gate.

