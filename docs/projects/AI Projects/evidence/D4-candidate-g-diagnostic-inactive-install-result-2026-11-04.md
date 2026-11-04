# D4 candidate-g diagnostic inactive install result — 2026-11-04

## Result

**PASS.** The correction that preserves a bounded candidate-g guest failure
class is installed inactive. It made no model request, created no booking, and
restarted no service.

Installed source is bound to mirrored platform commit
`b92a551b1e225af8399b0c1fcafdb356c519def9` and its committed deterministic
bundle SHA-256
`9ba99e5819384f0fe62b76292b68c81731a7f51755cd5ae8f1b44484c3704510`.

## Exact installed state

- Host listener adapter: `fecb32cb…c74600c`, root:root 0644, one link.
- Host release manifest: `6fa56d9c…a157f71`, root:root 0644, one link.
- LXC110 wrapper: `1d01c8c…3a4fc2`, root:root 0644, one link.
- Host and guest rollback checkpoint:
  `/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-diagnostic-r1-20261104`,
  root:root 0700 with root:root 0600 predecessor files.

Installed-path proof passed for the last bounded JSON-code selection, malformed
fallback, and bounded sorted guest error classes. All 34 release pins load. The
aggregate Doctor returned healthy with no codes; lease was exactly ready; no
drain/shared lock or port-11436 listener remained. LXC104/110/116 and Aster,
accepted 9B/SYCL, Speech, News, EPUB and Proxmox services were healthy. Aster,
llama, Speech, `pvescheduler` and `pvestatd` reported zero restarts.

The committed platform result is mirrored at `5b083701d9276249d2ff013e0429a888a1e8eb33`.

## Consequence

This closes the deterministic diagnostic installation gate. It does not score
or recover r3. One fresh candidate-g attempt may proceed only after an
authoritative conflict-free Lab Hours booking plus fresh lease, lock, health,
installed-pin and recovery preflight. Any future failure must retain its exact
bounded class or be treated as uncertain/NO-GO.
