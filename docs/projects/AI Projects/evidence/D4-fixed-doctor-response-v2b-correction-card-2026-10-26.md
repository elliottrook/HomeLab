# D4 fixed Doctor response v2b correction card — 2026-10-26

## Defect and bounded correction

The first v2 canary exposed a freshness-contract mismatch. The upstream Doctor
adapter accepts an observation for 36 hours, but the deterministic presentation
module rejected it after ten minutes. The corrected module uses the adapter's
single `MAX_AGE` definition and retains all schema, source, state, fact and
timezone checks.

The corrected response SHA-256 is
`4ca8721b1076815de3220dc51a1e499fd6822f3a9a1085bfc561804bea065298`.
The unchanged schema-2 caller SHA-256 is
`d1b567a8c7f0f205a6bd3fdc4d397ba03355f695995de74337fc4848e0cf9e48`.

## Installation and effect boundary

Stage both files in the new inactive directory
`/opt/aster-agent/candidates/fixed-doctor-response-v2b`. Target-Linux tests must
pass before a live attempt. Inactive staging restarts no service.

A subsequent live cutover may replace only those two live Python files and
restart only `aster-fixed-doctor-caller.service`. It must reuse and verify the
predecessor checkpoint made by the first attempt, call the socket once as the
existing `aster` identity, and automatically restore the predecessor and remove
the response module on any failure.

No Aster Agent, inference, Speech, News, gateway or broker restart is included.
No route, authority, model, credential, firewall or OpenBao change is included.

