# Stream A candidate-H F6 static card review

**Date:** 2026-10-25
**Decision:** static card **GO**; live execution remains **HOLD**

Platform commits `2c87fb95` and `281ff282` revise the candidate-H plus M3 F6
card around the measured installed system. It now freezes the full controller,
adapter, admission, owner, heartbeat, watchdog, recovery-observer, trusted-
observer and LXC110 authentication-helper paths and hashes; fixed runtime and
checkpoint paths; timer arm order; lease phase interface; real candidate-H and
M3 commands; deadlines; restoration reserve; and uncertain-recovery behavior.

The first independent review found one omission: the trusted observer and its
LXC110 metadata-auth helper were not pinned. Commit `281ff282` adds those exact
identities and the required no-auth `401`, fixed-invalid-bearer `401`, then
valid-key `200` contract without an inference request. The expanded source and
card suite passes 96/96.

The platform owner independently re-reviewed `281ff282` and returned **GO for
the static F6 card**, with no remaining static-card defect. It also confirmed
the timer dependency order: the heartbeat service dependency-starts the owner,
the matching-heartbeat gate prevents premature continuation, and the watchdog
timer remains inert until durable lease state exists.

This does not authorize or perform an effect. The card remains
`SOURCE-ONLY FUTURE RUN CARD; HOLD`. A single reviewed orchestrator must still
derive the dynamic lease identity, epochs and same-cycle evidence digests,
write exact root-custodied intents, execute the frozen serial phases, and own
rollback/reconciliation. Fresh F2–F5 evidence and separate live approval remain
mandatory.
