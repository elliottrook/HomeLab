# D4 candidate-i R2 booking review — 2026-11-04

## Decision

**CONDITIONAL GO; RESERVATION SCHEDULED.**

R2 is a distinct candidate-i attempt proposed for 18:30–19:30 PST. The
authoritative Lab Hours ledger reports the complete transaction plus recovery
window clear. R1 remains spent and retained; this proposal does not retry or
overwrite it.

The ledger was rechecked clear immediately before effect. The authoritative R2
record is now `scheduled`, created at epoch `1793839489`, with start/end epochs
`1793842200` / `1793845800` and restore buffer `900`. The dispatcher owns its
one claim at 18:30.

The deterministic R1 defect is closed at the installed boundary. The corrected
host adapter is
`80e7491b3d9bd3c457bf362baae97ba3377ac260dde1169933ddbdbc97cc1ee6`
and the accepted 36-pin release manifest is
`05e41525f08f52597128b6523b92c1ed7de3316cee09e3e79f95d347d31eb65d`.
The exact predecessors are root-only rollback-custodied. Installed proof shows
the host scope constructor, actual guest command and guest wrapper produce the
same candidate-i-specific scope identity.

The lease is ready, drain/operation locks are absent, LXC104/110/116 and their
core production services are healthy, and no restart occurred. Claim-time
booking, lease, lock, pin, competing-process and production gates remain fresh
and fail closed.

Accept only a complete restored transaction with 20 rows, 14 model requests,
six no-transport abstentions, zero retries/errors/effects, exact v2 identities,
one retained digest and complete independent postchecks. A failed or uncertain
attempt is terminal NO-GO without retry. Completion alone advances only to the
already frozen model-blind review boundary and grants no route, repair,
authority, model/backend change or promotion.
