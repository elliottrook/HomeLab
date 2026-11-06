# SA4 first signed zero-effect ceremony review — 2026-11-05

## Source candidate

The first SA4 repair release candidate is now fixed as a public, zero-effect
record with SHA-256
`ef2b153d35a697da3dfe9d410c82490c21d68903aefa366fedb28a6f72a6ab7f`.
It binds the single registered LXC 104 canary target, drifted SHA-256
`19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a`
and healthy artifact SHA-256
`4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065`.
It permits at most one supervised repair, no retry, no service restart and no
automatic routing, but currently authorizes no effect.

`sa4_first_signed_ceremony_v1.py` builds the exact canonical plan plus a
30-minute owner approval and 15-minute AI-PAM grant. It also builds detached
proof statements that bind each accepted signer and exact payload digest. The
source candidate deliberately contains no signature bytes and cannot access a
private key, invoke a signer, claim the one-use ledger, create a checkpoint or
change the canary.

## Production target resolution correction

Review found that the composed preflight resolved only the schema fixture even
when the plan named the registered production canary. The corrected source
resolves the production registry first and falls back to the schema fixture
only for the isolated synthetic tests. A regression requires
`sa4-lxc104-canary-adapter-v1` to resolve to host `lxc104`. The inactive-install
manifest now pins the corrected source SHA-256
`d96fcba0bda17ae48f2061a9c7977bbc70c67271a16d02ed11530b05d0a2ea06`.

The complete SA4 source suite passes **86/86** and `git diff --check` passes.
The corrected preflight source is not installed on LXC 104, and no signing
ceremony has run.

## Next gate

The next bounded host change is a reversible one-file inactive installation of
the corrected preflight composition, with exact old-byte checkpoint and
installed-path tests. Separately, bounded signer wrappers must expose only the
canonical signing operations for the already-created owner and AI-PAM keys.
Neither step authorizes a repair. The later signed ceremony remains zero-effect;
the first repair itself always requires a fresh exact immediate approval.

