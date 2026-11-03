# D4 candidate-g runner activation review — 2026-11-03

**Decision: source boundary accepted; inactive installation pending.**

Platform commit `3fd65261` adds the missing reserved-runner binding for the
already installed candidate-g transaction. The runtime admits only exact
profile `sa3-evidence-envelope-quality-v1`; the reserved runner admits only
registered kind `sa3-evidence-envelope-quality` and requires the complete
content-free receipt: 20 cases, exactly 14 model requests, zero errors, a
lowercase 64-character result digest and confirmed production restoration.

The replacement does not add a unit, booking, timer, retry, tool, authority or
automatic route. It reuses the existing full-drain controller, listener and GPU
absence checks, guardian path and unconditional production restoration.

The fixed installer replaces exactly the runtime, reserved runner and release
manifest. It checks their currently installed predecessors, all candidate
hashes and modes, rejects any active lease/drain state or any reserved, claimed
or running booking, retains a root-only checkpoint and rolls back all three
files if import/manifest validation fails. Exact candidate identities are:

- runtime `b4fc31b0…4da9`;
- reserved runner `63c7a116…aba`;
- release manifest `c970bd70…9886`;
- installer `41a487c6…3c7`;
- deterministic bundle `ce6242bc…794f`.

All Lab Hours tests passed 39/39. Runtime, transaction, listener and installer
tests passed 27/27. Two independent bundle builds matched. This closes the
source-only runner-activation design gate. It does not itself authorize or
prove installation or a model run.

Next: verify the target has the exact three predecessor hashes and no active
booking/state, apply the reversible inactive replacement, then repeat imports,
manifest validation, absence checks and production health checks. Only after
that proof may Stream A query the authoritative ledger and reserve a bounded
candidate-g run.
