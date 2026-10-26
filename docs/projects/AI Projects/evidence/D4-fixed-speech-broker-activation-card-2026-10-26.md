# D4 fixed Aster Speech — broker activation card

**Date:** 2026-10-26  
**Source route commit:** `f9b60e3e77ad3843cd417dbf8d9fd2f448ae397f`  
**State:** consumed and rolled back; do not retry

## Purpose

Activate the already installed, inactive fixed Speech read path. The result is
one deterministic read-only observation of the `aster.speech` check through a
dedicated caller, broker capability and private gateway. It grants no repair,
model, routing or general diagnostic authority.

## Static evidence

- complete local credential-broker suite: **128/128 passed**;
- isolated LXC104 target-Linux subset: **20/20 passed**;
- activation-manifest tests: **4/4 passed**;
- target-Linux staging and transfer paths removed;
- installed broker predecessors:
  - `broker_admin.py` `e90acd24…ef4aa`, root:root `0700`;
  - `broker_service.py` `c6217f49…b627e`, root:root `0644`;
- dependencies:
  - `broker_core.py` `2fdb8096…bf99`;
  - `homelab-broker.service` `8a65bb18…a1f3`;
- broker and Aster Agent active with zero restarts;
- fixed Speech capability, service, agent and grant rows absent;
- fixed inference capability remains enabled with its one grant; and
- both fixed Speech units are disabled/inactive and both sockets absent.

The exact packet is
`services/aster-agent/deploy/fixed-speech-broker-activation-manifest.json`.

## One bounded transaction

1. Recheck every predecessor, dependency, database and inactive-service gate.
2. Stop if another broker change or conflicting operation is present.
3. Copy the broker database and both predecessor files to a root-only rollback
   checkpoint.
4. Atomically replace only `broker_admin.py` and `broker_service.py` with the
   two pinned source files and their existing modes.
5. Syntax-check/import the installed files, then restart
   `homelab-broker.service` once.
6. Verify broker health and all existing fixed inference, Forgejo and Lab
   Operations route metadata before changing the database.
7. Run `enable-fixed-speech --agent-uid 975`, then verify exactly one observer,
   one Green non-probation capability and one grant, with no other grant.
8. Start, but do not enable, `aster-fixed-speech-gateway.service` and
   `aster-fixed-speech-caller.service`.
9. Make exactly one local Aster-user request to the dedicated caller. Accept
   only the exact fixed response shape with `authority: not-granted` and the
   `aster.speech` check identity.
10. Verify both units, broker and Aster Agent are healthy with zero unexpected
    restarts, all pre-existing broker routes remain present, and no model or
    repair path was reached.

## Failure and rollback

Any failed or uncertain gate stops the transaction. Stop the two candidate
units, restore the exact database checkpoint and both predecessor files,
restart the broker at most once, and verify the original fixed inference,
Forgejo and Lab Operations state. Preserve evidence and do not retry.

## Consumed result

The approved transaction was attempted once. Both candidate units entered
`active` and were then stopped by the failure trap before the canary. The
same-second journal ordering and absence of a unit error narrow the first
failure to the immediate socket-readiness section; the script had no bounded
wait between starting Type=simple units and asserting both socket paths.

Rollback restored the exact predecessor file hashes and database content. Its
first broker recovery start then failed because the script restored the
database as `root:root 0600` rather than its required
`hlabroker:hlabroker 0600`. Recovery corrected that ownership, reset the failed
unit state and started the original broker. Final postchecks show the broker,
Aster Agent and fixed inference gateway active; original fixed inference,
Forgejo and Lab Operations rows intact; zero fixed Speech rows; candidate
units disabled/inactive; and both candidate sockets absent. This packet is
spent and must not be retried.

## Explicit exclusions

No Aster Agent restart, host reboot, model call, repair, automatic routing,
other capability change, schedule change or Git push. The only expected user
visible effect is a brief broker restart; ordinary Aster inference and Speech
services remain running.
