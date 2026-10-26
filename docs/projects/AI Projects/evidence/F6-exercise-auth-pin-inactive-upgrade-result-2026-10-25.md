# F6 exercise auth-helper pin inactive upgrade

**Date:** 2026-10-25

**Decision:** inactive installation **PASS**; F6 effects remain **NO-GO**

Jason approved the one-file replacement from platform source commit
`d4473311` and upgrade card commit `6222003c`. The installed prepare-only
runner now has SHA-256 `29429e7f…eaa1e`, is a root-owned mode-`0644` regular
one-link file and recognizes the corrected LXC110 metadata-auth helper at
`93e78f8a…82582`. The old runner is retained in root-only checkpoint
`/var/lib/local-ai-lab/checkpoints/f6-exercise-auth-pin-d4473311-20261025`.

The complete target fixture passed 94/94 tests. Installed-path import passed,
and inert invocation returned only `effects: disabled` and `state:
source-only`. The lease stayed ready; no lease, lock, runtime state, receipt,
F6 process, service command or model request occurred. F6 units remained
absent/inactive, while both October 26 F2 date-specific timers remained
enabled and active and the recurring F2 timers remained disabled/inactive.

An initial remote test bundle omitted repository wrapper fixtures and produced
seven missing-path errors; a complete bundle immediately passed 94/94. A
direct execution attempt also correctly met the runner's non-executable mode;
the required Python invocation returned the exact inert result. Neither
validation-harness correction produced a runtime effect.

This removes the stale helper pin from future F6 preflight. It does not arm
F6, create F4/F5 evidence, acquire a lease, stop production or authorize a
model call. The critical path remains the October 26 F2 result, conditional F3
conversion, then fresh-cycle F4/F5 and a separately reviewed live F6 card.
