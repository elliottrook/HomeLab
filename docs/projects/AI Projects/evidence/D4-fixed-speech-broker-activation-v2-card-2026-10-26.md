# D4 fixed Aster Speech — corrected broker activation v2

**Date:** 2026-10-26  
**State:** corrected candidate; requires fresh approval

## Corrections

The v2 packet keeps the same tested broker sources, capability, grant, units
and one-call canary. It changes only the transaction runner:

- poll each candidate socket for at most five seconds after the Type=simple
  units enter active state;
- precheck the live database as `hlabroker:hlabroker 0600`;
- restore the database explicitly as `hlabroker:hlabroker 0600` on failure;
- use the new root-only checkpoint
  `/var/lib/homelab-broker/fixed-speech-pre-activation-20261026-r1`; and
- preserve the one-attempt, no-retry rule.

The exact runner SHA-256 is
`7c8c6a99f2dd8e1ef1459bd984432a2396e440192b4b0155c510576ff3f6d861`.
The schema-1 manifest identifies the new candidate as
`d4-fixed-speech-broker-v2` and binds the runner, two source replacements,
predecessors, dependencies, database custody, one broker restart, one grant,
two non-enabled unit starts, one canary and rollback.

## Current recovered baseline

- broker files are back at `e90acd24…ef4aa` and `c6217f49…b627e`;
- broker database is `hlabroker:hlabroker 0600`;
- broker and Aster Agent are active;
- fixed inference, Forgejo and Lab Operations metadata remains intact;
- fixed Speech has zero agent, service, capability and grant rows;
- candidate units are disabled/inactive and sockets absent; and
- failed-attempt staging is removed.

## Exact v2 effect

The effect remains the bounded transaction in the consumed v1 card: checkpoint,
replace two files, restart only the broker once, enroll only UID 975's Green
fixed Speech observer capability, start the two dedicated units without
enabling them, and make one read-only canary. No Aster restart, reboot, model
call, repair, automatic routing, schedule change, other capability change or
Git push is included.
