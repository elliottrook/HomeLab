# SA4 approved target source packet — 2026-11-05

## Result

Jason accepted the exact inert LXC 104 canary and three-way key-custody design.
The canonical acceptance record has SHA-256
`5a47af308226e66ce7c1d5b5c6450d3c846ee175152448a85be5e766b663fe3d`
and limits this milestone to source registration, fixed validators and empty
key slots.

The compiled production registry now contains exactly one target:
`sa4-lxc104-canary-adapter-v1` at
`/var/lib/aster/sa4/canary-adapter.json`. It fixes root:root mode-0644
one-link custody, a 4096-byte ceiling, root-only checkpoint/temporary paths,
three exact postchecks, the rollback checker and the owner-acceptance digest.
It forbids service restart and automatic retry. The plan validator now resolves
this exact compiled production target while retaining the separate synthetic
fixture for schema tests; unknown IDs and caller-supplied paths still fail
closed.

Four fixed no-effect programs accept only:

- exact healthy canary bytes;
- exact root-owned mode-0644, one-link, 82-byte metadata;
- the canonical inert consumer contract; and
- exact retained drifted checkpoint bytes for future rollback verification.

All emit content-free state/digests and zero effects. They accept no path,
host, command, network target or key input.

Three compiled custody slots now identify the human owner device, AI-PAM
broker and independent Proxmox observer as distinct domains. Every slot is
`empty`, has no public-key digest, forbids private-key export and runtime key
nomination, and leaves the actual authority/observer trust registries empty.
No key was generated, read, exported or installed.

The expanded SA4 suite passes **63/63**, including exact program/acceptance
hash binding and production-plan resolution. A fresh read-only target check
still finds the LXC 104 SA4 directory, target and checkpoint directory absent.
No live target, checkpoint, key, grant, service, restart, repair, route or
deployment was created.

## Source identities

- compiled target registry: `0091a90f…3b9d83`
- production-aware plan contract: `c260e6d8…bb9467`
- target-byte check: `f8f544ca…dd00a1`
- target-metadata check: `e61bb89b…9a041`
- consumer-health check: `1214189f…c72da`
- rollback check: `15f924f5…1ffdb`
- empty key-custody slots: `6e45ecad…e04816`
- authority registry binding: `cbc97617…6be6ee`
- observer registry binding: `a1e99c3a…145b9d`
- source-packet tests: `745813de…b14841`

## Next gate

Prepare a reversible inactive-install packet for the target directory, drifted
fixture, validators and source-only owners. Key creation/custody installation
is a separate credential packet and is not implied. The inactive install must
create no booking, timer, service restart, grant, checkpoint or repair effect.
The first repair still requires its own exact immediate approval after all
installed hashes, custody and absence gates pass.
