# M1/D4 fixed Doctor — activation, one grant and one-read card

**Date:** 2026-10-25
**Status:** review candidate; no live effect authorized

**Script:** `scripts/deploy/activate_fixed_doctor_capability.sh`, SHA-256 `a040e0eeb5674664183f2c81a376b1883eb68620fbedc4f99f9ab9c788592533`

## Purpose

Complete the next D4 authority gate after the reconciled broker cutover:
activate the already installed dedicated gateway/caller, enroll only the
dedicated caller UID as an observer with one Green capability, and prove one
typed read of the fixed `aster.agent_inference` evidence.

## Exact live action

The pinned activation script requires the accepted broker, caller, gateway,
capability and unit hashes; UID 978; the dedicated group memberships; active
broker/Aster services; disabled/inactive fixed services; absent fixed sockets;
safe report custody; SQLite integrity; and zero pre-existing fixed rows.

It then:

1. creates a root-only consistent SQLite checkpoint;
2. runs only `enable-fixed-doctor --agent-uid 978`;
3. verifies observer state and exactly one Green, non-probationary grant;
4. enables/starts the gateway, then the caller, and waits for their sockets;
5. sends exactly one fixed request as Unix user `aster` through the dedicated
   caller socket;
6. accepts only schema 1, the fixed capability/source, typed state `ok`, the
   single allowlisted check ID and bounded age;
7. requires exactly one consumed fixed request, healthy SQLite, active/enabled
   fixed services with no restart loop, and healthy normal broker/Aster.

Success leaves the one observer/grant and both dedicated services active and
enabled. It does not route ordinary Aster questions through this capability.

## Rollback

On any failure after enrollment begins, disable/stop both fixed services,
remove their runtime sockets, stop only the normal broker, restore the root-
only pre-enrollment database checkpoint as `hlabroker:hlabroker` mode `0600`,
start the broker and require a successful registered-client health response.
The reconciled broker sources remain installed.

## Exclusions

No model call, prompt or arbitrary Doctor text crosses the boundary. No
Forgejo write, project-document change, Companion change, credential access,
schedule change, host/B60 lease, F2/F6 action, production inference restart or
Git push is included. Service enablement is limited to the two dedicated fixed
Doctor units.
