# Stream A evaluation-lease effect-entrypoint review — 2026-10-25

> Decision: **REJECTED BEFORE INSTALLATION OR EFFECT**

## Reviewed source

- platform implementation: `c3b316ab27b770e3703cf6967e5b8665f489172c`;
- metadata pin follow-up: `d56084a5`;
- entrypoint SHA-256:
  `d42963fb84730aa3a6f9a8206c1626b1b526ec2b9ee4ac5456716ed7b4be8b97`;
- wrapper SHA-256:
  `962100b591493b2ae8f62814fa6f66a1875463dd5ca613bb321169764c56c276`;
- card SHA-256:
  `7c07d33316bfefb30e722a384ad5fd1e833674a676762c41bfff54db8f78135f`.

A clean commit archive passed 30/30 evaluation-lease tests and compiled all
four Python modules. The disabled wrapper behavior and reported hashes
reproduced. Those checks did not cover four release-blocking cases.

## Failed boundaries

1. `evaluation_lease.py` still pins superseded M3 stage-manifest digest
   `357b4e3d…124a00`. The corrected packet installed in LXC110 is
   `69ffc589…72165`; an otherwise valid M3 outcome would fail the lease contract.
2. The deployment card requires the destination root and every target absent,
   then permits rollback removal of that root. The accepted four-file inactive
   library baseline already occupies that exact root. A correct upgrade must
   require those four exact files, add only the entrypoint and wrapper, and
   preserve the four files on rollback.
3. Only `acquire` enforces an exact intent key set. A direct regression probe
   showed `heartbeat` accepting an unexpected field. `restore` also accepted
   an unexpected field and converted the string `"false"` into recovery mode
   through `bool()`. Every phase needs an exact schema and literal types.
4. The intent loader accepted a regular mode-`0644` file. Effectful root input
   must be a root-owned, mode-`0600`, regular non-symlink file. The state path
   must also be fixed or allowlisted so the independent watchdog and recovery
   operator inspect the same durable state.

The platform owner received these exact findings and regression requirements.
No file was installed, no entrypoint was invoked on Proxmox, no lease or state
was created, no consumer changed and no model request ran. The accepted inert
four-file library installation remains unchanged.

## Second candidate review

Platform commits `e55e9eff52fe7cf4a171a290324ec4985f189a2f` and
`5b48f86933463c8abcaf57b50fb7ae5b37b93d76` corrected the M3 digest, exact
per-phase schemas, literal booleans, intent custody, fixed state path and
add-only wording. Their clean archive passed 32/32 tests. Two follow-on gaps
still prevent installation:

1. Correcting the M3 digest necessarily changed `evaluation_lease.py` to
   SHA-256
   `675ebb566de298334f7c612cae9af2637067930f40c0ad2c23a22e1b7e248f1b`.
   The card still pins the installed old hash `38a986e9…6312` and prohibits
   replacing any existing library. That would leave the live contract bound to
   the superseded M3 packet. The transaction must checkpoint and replace this
   one file while preserving the other three installed libraries, then add the
   entrypoint and wrapper.
2. `main` evaluates `load_intent(args.intent)` before `_main_effectful` checks
   the fixed state path. The test for an arbitrary state passes because its
   absent intent raises first; it does not prove the intent was unread. The
   state-path check must precede intent loading and a mock must prove the loader
   was not called.

The platform owner received these two exact corrections. The second candidate
is also rejected before installation or effect.

## Final corrected candidate

Platform implementation `ae56046bc5f361e84c88e72b5af11b4f933c94c4`
and metadata/card commit `d2a32785e1d7a12fa7582e708f2b46e9b7efd529`
close both follow-on gaps:

- arbitrary state paths are rejected before the intent loader is called, with
  a mock assertion covering that order;
- the card requires installed `evaluation_lease.py` at old hash
  `38a986e9…6312`, checkpoints and atomically replaces only that file with new
  hash `675ebb56…f1b`, adds only the entrypoint and wrapper, and preserves the
  other three libraries on install and rollback; and
- final card SHA-256 is
  `bb3b4f9552898fcbe10d0067a71e7438be719bf407a5c529f34a72876c546e4e`.

Stream A reproduced 32/32 tests from a clean archive, compiled the four Python
modules with an isolated cache and matched the source hashes. Read-only target
preflight found the exact old four-file baseline, root `0755`, files `0644`,
the new entrypoint and wrapper absent, fixed state and operation lock absent,
and the legacy controller `ready`. The three-file install packet is 24,250
bytes at SHA-256
`f69dde0c6e7dc9c04e0943e18777abc816d9c39a8287dbe0384c66dde983ef8f`;
the eight-file target validation packet is 87,676 bytes at SHA-256
`274298d9f56696480f28f22b7bc750b6e23d3482a59422c6e8538841325ad837`.

The source and inactive upgrade are now **accepted for one exact installation
decision**. Acceptance does not authorize installation, an effectful phase,
watchdog activation, a lease, consumer change, model call, D4/M3 execution,
F2 change or Git push.
