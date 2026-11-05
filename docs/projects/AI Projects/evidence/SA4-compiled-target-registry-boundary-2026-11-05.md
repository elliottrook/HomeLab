# SA4 compiled target registry boundary — 2026-11-05

## Result

The next source-only SA4 increment separates schema fixtures from effect-capable
production targets. `sa4_target_registry_v1.py` exposes fixed resolvers with no
registry, host, path, command, key or postcheck override. The production tuple
is deliberately empty; every production lookup therefore fails closed. The
single synthetic fixture can be resolved only through the schema-fixture API.

Each immutable registration pins host and path, custody, mode, size ceiling,
checkpoint parent, temporary path, fixed postcheck IDs and program digests,
rollback digest, owner-review digest, no-follow/one-link requirements, no
restart and no retry. Registry validation rejects duplicate identities or
locations, path aliases, unsafe production paths, changed custody, symlink or
hardlink allowance, restart requirements and caller-shaped checks.

The synthetic registration digest is now cross-bound into the filesystem
evidence, one-use ledger and composed preflight result. The plan signature
format is unchanged; the composition independently resolves the compiled
registration and requires both retained records to match it.

The SA4 suite passes **36/36**. No production target, key, measurement owner,
checkpoint, effect, restart, deployment, route or authority was created.
Every existing composed result remains `maximum_effects=0` and
`preflight_eligible=false`.

## Source identities

- target registry: `dc2141682c071ae0ca0ad5b2244cb61c960bbc97fd96fa30c9714a5f0ba6222a`
- plan contract: `2bc93d6c80cb7779d706c3efac34f5f5efe5bd51b6de5a14742c3523ef9d912f`
- filesystem evidence: `6ea2b5da108b46be8ff0682f4d3dd2c66316530cb9f09316347f2cfd85f7cbc0`
- one-use ledger: `4babcb5bd08d13788c4f0fb52447ad35e892fb2264b7b7bcadddabfd88e738b0`
- composition gate: `a45335dcb6ab209433e71bd486345904d4e0748f5ae03bc85f24a7863926b569`

## Remaining gate

The next autonomous source increment is the separately authenticated
independent-observer receipt layer. A real target can enter the production
tuple only through a later owner-reviewed source change. Installation of an
inactive measurement owner, real separately controlled keys and the first
repair effect remain separate gates; the first effect still requires Jason's
exact immediate approval.
