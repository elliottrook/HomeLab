# M1 Stage1 deployment — 2026-09-25

Status: Stage1 installed and verified; ten-minute observation passed. M1 remains open for Stage2.
Authority: Jason explicitly approved the two-file Stage1 scope after commit
`85d2e46`; AI-PAM task confirmed and held a maintenance window. No Git push approved.

## Scope and provenance

LXC104: replaced only `/opt/homelab-broker/broker_core.py` and
`/opt/homelab-broker/broker_service.py`; additive policy-hash schema migration.
Restarted only `homelab-broker` and `homelab-broker-approval`. No grant,
credential, gateway, unit, Authentik or Companion modification.

- Approved archive SHA256: `0d9632a3683a5efe740921a360cf65ca6e2644b6d7aee3a5b33d04c56b659d49`
- Manifest SHA256: `6336acc608c23bf2168e875adc652f43c45c8b5663884fe4171bb53323de2589`
- Installed core: `a7dbf6206e8643ccf3b52260a83f8da07597acd0cca2d74152aaab28418c60d0`
- Installed transport: `478638e4855d283d42c750a5c5662cc0386343cf502d024e97d5f09e71769498`
- Unchanged approval source: `a73625fa3b68fe3a5e65f8960b6c96d9fec8fbf4c9dbdc75fe4136a5625c50d8`

Archive digest matched on Mac, Proxmox and guest. Read-only preflight passed with
zero usable authorizations and database integrity `ok`. All 45 staged guest
tests passed; legacy Yellow/Red approval compatibility and stale/wrong-caller/
replay denials passed with zero external actions.

## Checkpoint, incident and recovery

Protected checkpoint:
`/var/lib/homelab-broker/rollback/m1-stage1-20260926T011710Z`
(UTC date differs from local date). SQLite backup and a second isolated restore
passed integrity/count validation before source replacement. No credential
material was copied. Production status counts remained consumed 11, denied 1,
expired 8, revoked 1; no pending/approved requests.

The installer reported Type=simple services active before sockets existed. Its
immediate health probe failed with FileNotFoundError; the trap stopped both
services as designed. Read-only diagnosis found SIGTERM from the stop, zero
restarts, no journal traceback/error/exception markers, and exact candidate hashes.
This was an installer readiness defect. A single bounded start of the same two
services waited up to 15 seconds for sockets, then asserted registered-peer health.
It succeeded at Unix1790385497, without changing sources or restoring the DB.

Broker unavailability was approximately 67 seconds, from maintenance entry at
Unix1790385430 to verified readiness at1790385497. This is observed rollout
duration, not a service SLO. The pinned installer must not be replayed; preserve
it as execution provenance and require readiness-aware checks for future releases.

Python3.13 emitted unclosed-database ResourceWarnings in test fixtures; tests
passed. Test connection cleanup remains a local follow-up, not a production fault
claim.

## Initial verification

- Both broker services active; PIDs 11450/11451; restart counters 0.
- Read/write gateway PIDs 7334/10613 unchanged; active, restart counters 0.
- Aster PID 6904 active, restart counter 0; no Aster restart requested.
- Both sockets mode 0660, owned by hlabroker with their existing client/approver groups.
- Database mode 0600, owned by hlabroker.
- Registered-peer health and capability catalogue succeed.
- hlabagent cannot connect to the approval socket (PermissionError).
- Unauthenticated Companion approvals HTTP returns 401.
- No live target action, write request or approval was generated as a smoke test.

## Observation and limits

Read-only bounded polling covers services/PIDs/restarts, registered-peer health,
SQLite integrity/counts, and source-local journal error markers. Raw journal
messages, request payloads, credentials and personal content are not retained.
Observation completed at Unix1790386098, 601 seconds after verified readiness.
All 13 periodic polls passed: stable PIDs, zero restarts, successful health,
integrity `ok`, unchanged counts and zero checked error markers. Initial readiness
and post-install checks preceded those periodic polls. The final source/schema/
checkpoint-count and HTTP denial recheck also passed. See the sanitized
[observation record](M1-stage1-observation.json).

This is only Stage1. Explicit approver entitlement/assurance controls in the new
approval service and Companion are not deployed. M1 remains open. M6 real-write
and rollback evidence belongs to the AI-PAM task; the preserved transport was
tested here with fake gateways, not a new real write.


## Integration disposition and next gate

Existing broker, gateway and Aster service monitoring remains in use; no new
collector, metric backend, scheduled job or duplicate alert was introduced.
The observation is a low-traffic operational check, not a measured contention
benchmark or a complete failure-injection exercise. No new endpoint, device,
address, firewall, DNS, certificate, identity, grant or Homepage entry needs a
NetBox/discovery update. The operational runbook and programme portfolio are
updated locally. Wiki/mirror graduation updates remain tied to the full M1 gate;
no private checkpoint or runtime dataset should be mirrored.

Retain the local-only Stage2 candidate and its tests. Next independent work may
cover offline M2 contracts; connected authority expansion remains blocked on
Stage2's verified identity/assurance design and separately approved deployment.
The approved bundle's manifest retains its pre-execution status as immutable
release provenance; this deployment record owns its subsequent live status.


## Completion and resumability

Stage1 is complete; the transient readiness failure and approximately67-second
interruption are retained above rather than hidden by the successful recovery.
Protected checkpoint directory mode0700 and backup/restore/verification files
mode0600 were rechecked. No Git push occurred. Full M1 is not graduated.

The manifest and installer are preserved unchanged as executed provenance.
A future release must fix readiness polling and rerun review/tests; do not use
this historical bundle as a repeatable deployment tool.
