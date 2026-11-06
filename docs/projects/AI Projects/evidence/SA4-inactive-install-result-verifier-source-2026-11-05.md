# SA4 inactive-install result verifier source — 2026-11-05

The seven-file inactive-install packet now has a fail-closed result verifier.
It requires each destination's exact host, path, predecessor state, installed
hash, ownership, mode, link count and regular-file status in fixed order. The
two replacements must have retained predecessors; the five creations must
prove absence before installation.

The verifier also requires all seven isolated imports, all transaction owners
still host-bound to `unconfigured`, a fake-runner-only signer self-test, no
private-key access or signer invocation, no grant/checkpoint/target touch, no
service action, exact rollback readiness and a fixed healthy production set.
It emits only an inactive, zero-effect validation summary.

Three focused mutation tests cover exact acceptance, hash/predecessor drift,
and every prohibited effect or unhealthy production claim. The full SA4 suite
passes **126/126**.

No installation or host mutation occurred. The next step is the separately
gated reversible inactive installation. Its success would still authorize no
signature, checkpoint, claim, repair, rollback or service action.
