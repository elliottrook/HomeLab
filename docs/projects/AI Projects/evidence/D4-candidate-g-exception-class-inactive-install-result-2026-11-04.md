# D4 candidate-g exception-class inactive install result — 2026-11-04

## Result

**PASS.** The class-only guest exception fallback is installed inactive from
mirrored platform commit `fb32f402bc5e448ed47f3823d58aa53c78a2f3d5` and
bundle SHA-256
`6aec85a19b69c102cf4304abf91006db17923102934b50e5a81080d95e5cb2cb`.

The LXC110 wrapper is root:root 0644, one link, exact SHA-256
`626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe`.
Its predecessor is retained root-only at
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-exception-class-r1-20261104`.

Independent installed proof forced a synthetic otherwise-unhandled `KeyError`:
the wrapper emitted only `candidate-g guest exception-class:KeyError`, with the
private exception message absent. Lease, locks, listener, Doctor, production
services and restart-count postchecks passed. No booking, model call, workload
effect or restart occurred. The installed result is mirrored at platform commit
`7ccbd132c5bf58a96fa3d85d80359d2f18f5932f`.

## Consequence

The evidence-loss gate found by r4 is closed. R4 remains spent and unscoreable.
One future attempt may proceed only under a new authoritative conflict-free
booking and fresh installed-pin, lease, lock, health and restoration gates. Any
otherwise-unhandled ordinary exception must now retain its bounded class; no
exception message, case content or answer may enter shared evidence.

This installation grants no model/backend change, restart, blind review,
routing change, tool grant or promotion.
