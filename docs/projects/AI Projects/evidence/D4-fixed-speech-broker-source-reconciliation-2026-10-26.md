# D4 fixed Aster Speech — broker source reconciliation

**Date:** 2026-10-26  
**State:** source complete; live broker unchanged

## Change

The broker source now supports one distinct fixed Speech route while preserving
the existing fixed inference, Forgejo and Lab Operations routes.

- agent: `agent-aster-fixed-speech`
- service: `aster-fixed-speech`
- capability: `diagnostic.aster-speech.latest`
- risk: Green; probation disallowed
- gateway socket: `/run/aster-fixed-speech/gateway.sock`
- gateway method: `doctor.aster-speech.latest`
- payload: exactly `{}`

`enable-fixed-speech --agent-uid UID` is idempotent only for the exact observer
identity, service metadata and single capability. It rejects an existing
conflicting identity, service, capability or any other grant.
`disable-fixed-speech` disables the service, removes the sole grant and
suspends the observer.

The request transport rejects any nonempty payload before consumption and
uses a dedicated five-second Unix-socket path. It accepts only the exact
`{"ok":true,"result":...}` response shape and returns a bounded denial if the
gateway is unavailable or rejects the request.

## Validation

The complete credential-broker suite passes **128/128** after adding the
fixed Speech enrollment, reversal, conflict and transport cases. No production
file, database row, grant, unit or socket changed during these tests.

## Remaining effect gate

Before live use, freeze the exact two-file broker replacement, validate it on
target Linux against the installed predecessor hashes, and prepare one rollback
transaction. Applying it requires replacing the two broker files, restarting
the broker once, enrolling the single capability, starting only the two
dedicated fixed Speech units and running one bounded read-only canary. That
restart and activation remain unapproved effects.
