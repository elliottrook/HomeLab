# AI-PAM M7 Doctor integration candidate

> Status: local candidate only — not authorized or deployed
>
> Date: 2026-09-25 | Parent: [HomeLab Credential Broker](homelab-credential-broker.md)

## Decision

Use the already deployed Lab Operations Doctor path for the first M7 pair:

- **Green `lab.doctor.latest`:** read the latest sanitized Doctor job result
  without expiring, reconciling or otherwise changing the job database.
- **Yellow `lab.doctor.run`:** after exact Aster approval, enqueue one `doctor`
  job with purpose `user_request` or `task_diagnosis`. The broker request ID is
  the durable idempotency key.

Do not expose backup targets, worker claim/completion, raw SQLite, logs, shell,
paths, hosts, target selection or credentials. The gateway runs as `aster`, has
only Unix-socket ingress, and shares a dedicated `aster-lab-broker` group with
the broker. It reads the existing owner hash and job-state path but does not load
the worker bearer credential.

## Authority and data flow

`agent-hermes → AI-PAM request → Green immediate / Yellow human approval → broker
→ dedicated Unix socket → Aster Lab Operations Store → existing Mac worker`

The AI-PAM broker owns request identity, risk class, payload binding, TTL,
approval and one-use consumption. Lab Operations remains authoritative for
worker heartbeat, cooldown, concurrency, daily limit, durable job state and
result verification. A completed Doctor run is diagnostic evidence, not
authorization for a repair.

## Risk and recovery

The Yellow effect consumes bounded Mac/lab diagnostic resources and writes one
durable job/result; it changes no infrastructure configuration. Existing worker
offline, cooldown, active/unknown job and daily-rate gates remain stricter than
the broker. Unknown outcomes are not replayed automatically.

Revoke by disabling either broker capability or the `lab-operations` broker
service, then stop the private gateway. The existing Companion Lab Operations
path and human Doctor command remain independent. Rollback removes the two broker
registrations/routing and the gateway unit; never delete the job database or an
in-flight record.

## Required validation before deployment approval

- Exact capability registration and grant manifest; existing agents remain in
  their current state.
- Gateway peer-UID, schema, method, target, purpose and output-shape denials.
- Green read proves database state unchanged, including stale queued/running
  records.
- Yellow pending/wrong caller/demotion/changed payload/replay never reaches the
  gateway; approved request queues at most one Doctor job.
- Worker-offline, cooldown, active job, uncertain job and daily-limit denials.
- No backup target or credential-bearing field reaches the broker response.
- Restart/unknown reconciliation and emergency service/capability disable.
- Two real approved runs with independently verified sanitized results, followed
  by target-side and broker-side revocation tests.

## Integration impacts

No new address, DNS, certificate, firewall, NetBox record, Homepage entry or
backup scope is proposed. Deployment would add one local group, one confined
systemd service/socket and two broker capabilities on LXC104. Doctor/monitoring
should check gateway reachability and stale jobs only after activation. Native
Companion parity remains required by M8.

## Current evidence

The local candidate adds a broker-private adapter, unit, routing and synthetic
tests. It does not register capabilities, create the group/environment file,
restart a service, access the live job database, run Doctor or modify production.

The deployment bundle now includes a preflighted installer and explicit rollback
script. The installer refuses active or uncertain Lab Operations work, requires
`agent-hermes` to remain an operator, copies the broker database and replaced
files into a timestamped root-only checkpoint, derives only the existing owner
hash (never the worker key), and starts the private gateway before restarting
the broker. Deployment remains unauthorized until the operator approves it.

## Initial production deployment — 2026-09-25

Jason authorized the bounded deployment from commit `2a81a78`. LXC 104 created
root-only checkpoint
`/var/lib/homelab-broker/m7-doctor-rollback-20260925-191251`, installed the
peer-bound gateway, registered and granted the Green/Yellow Doctor capabilities,
and restarted only the broker. Both services remained active.

The first Green request returned the existing sanitized successful Doctor result.
A non-broker peer received only the generic denial. A Yellow validation request
remained pending, created no Lab Operations job, and was revoked without approval.
The job database still had zero queued/running/unknown records and seven historic
Doctor records. The installer initially reached its one-shot socket assertion
before the new service had created the socket; production became ready moments
later, and the source installer now uses a bounded readiness loop. Two real
approved Yellow runs and revocation checks remain before M7 graduation.
