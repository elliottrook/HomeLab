# SA3 Candidate-J quality inactive installer source — 2026-11-05

The deterministic reversible installer for Candidate-J untouched quality is
source-complete and not applied. It binds the newly observed live host
baselines, refuses baseline drift, existing target units, shared state/locks,
a non-ready lease, existing targets or an existing checkpoint.

The exact boundary replaces four pinned host control files, adds the three
quality transaction components, and adds five files to LXC110: the packet,
contract, selection runner, key-free quality runtime and guest wrapper. Answer
keys, scorer, source freeze and blind-review/decision code are excluded.

Before mutation it creates root-custodied mode-0700 host and guest checkpoints.
Every installed byte is reread against its pinned hash. Rollback removes only
new files whose bytes still match and restores only checkpointed host files;
uncertain drift fails closed. No unit is created or enabled.

The deterministic bundle binds platform source commit `20490b65` and Stream-A
commit `4929237a`; two independent builds have identical hashes in tests. The
joined installer/runtime/manifest suite passes 61/61.

This milestone performs no installation, booking, model call, service stop,
restart, route, authority or promotion. Applying the inactive installer is a
separate deployment gate.
