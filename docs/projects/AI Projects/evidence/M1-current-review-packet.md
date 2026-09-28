# M1 current review packet and reconciliation — 2026-09-25

Status: current baseline reconciled; Stage1 is deployed; Stage2 remains open.
Owner: Jason. This is a review handoff and local verification record, not independent
approval or permission to repeat a completed rollout.

## Corrected baseline

At resumption, this checkout was clean at `af2cc4f`. Earlier notes described a dirty
AI-PAM candidate and undeployed M1 work. Read-only inspection found AI-PAM clean at
`f25df1812b7ef339acb9cb59339c704a4032ea26`, also the live Forgejo main ref. That merge
includes the completed M6 pilot and separately approved two-file Stage1 rollout.
The old `a5e8b22` design was explicitly superseded; its applicable tests were ported.
See [supersession map](M1-a5e-supersession.md) and
[executed Stage1 record](M1-stage1-deployment.md).

Merged that exact verified Forgejo commit locally, preserving this branch's M4
review work. Only the programme status header required manual conflict resolution:
retain deployed Stage1 and incomplete Stage2/M4. No other checkout was edited, no
runtime changed and no remote write occurred. A final status recheck found new
uncommitted M7/Doctor and Lab Operations gateway work in AI-PAM, including transport
and unit edits. Those concurrent changes are outside the pinned baseline and were
left untouched; recheck them before any later integration. This is not a new security deployment.

A separate main checkout has unpublished continuation `1a8fa680908eac8e0b7bb76845a0b1b061e593d7`
with `services/aster-adaptive`, `schemas/aster` and a Stage2 design. Its preceding
commits are `30f79ea` and `026e5e9`. They are not part of the verified Forgejo baseline
or this merge and were not cherry-picked. The two offline contract implementations
must be mapped before connected adoption; neither should silently replace the other.
Do not launch duplicate changes in shared broker/approval files from stale notes.

## Live read-only verification

Source hashing on LXC104 matched the Stage1 execution record exactly:

| File | SHA-256 |
|---|---|
| `/opt/homelab-broker/broker_core.py` | `a7dbf6206e8643ccf3b52260a83f8da07597acd0cca2d74152aaab28418c60d0` |
| `/opt/homelab-broker/broker_service.py` | `478638e4855d283d42c750a5c5662cc0386343cf502d024e97d5f09e71769498` |
| `/opt/homelab-broker/broker_approval_service.py` | `a73625fa3b68fe3a5e65f8960b6c96d9fec8fbf4c9dbdc75fe4136a5625c50d8` |

`homelab-broker`, `homelab-broker-approval`, both Forgejo gateways and `aster-agent`
reported active. No private database, request content, subject hashes, credentials,
raw session/token material or logs were inspected. This status/hash check does not
repeat the recorded ten-minute observation or prove all production workflows.

The local approval/Companion candidate intentionally differs from live Stage1.
Its explicit configured subject allowlist and ACR mapping are Stage2 code, not
installed enforcement. Do not treat passing local tests as deployed entitlement.
The historical Stage1 installer had a readiness race and must not be replayed.

## Review coverage and disposition

| Boundary | Current evidence | Remaining question |
|---|---|---|
| Originating agent and exact payload | Stage1 kernel-derived caller binding, core mandatory identity, wrong-caller/payload/replay tests | Preserve through future transport changes; never trust client JSON identity |
| Policy lifetime | Versioned policy digest; atomic consume; supported state/service changes revoke; restart/concurrency tests | Raw grant/capability edits can restore an old digest; unsupported edits are not a safe management API. Future mutators need atomic revocation and tests |
| M6 compatibility | Integrated safe-branch transport/gateway candidate retained; 76 broker tests pass | No new real write or rollback attempted; existing M6 execution evidence owns those claims |
| Human entitlement | Local Stage2 explicit allowlists default to deny; 10 bridge tests pass | Verify actual intended subject through human-controlled identity path; do not derive authorization from an actor string |
| Passkey assurance | Local exact ACR allowlist and freshness checks; generic MFA does not qualify | Installed issuer's actual signed session claim must be established without exposing tokens; a fresh real session requires human participation |
| Process trust | Approval socket limits peer identity but receives actor/assurance from Aster | Explicitly accept the bounded process trust or design/review a separate identity-verifying ingress; allowlists alone do not solve compromised Aster |
| Recovery | Stage1 protected backup/restore and observation documented; fail-closed candidate behavior | New release needs readiness-aware checks and restrictive recovery; do not restore old usable approvals or permissive enforcement |

This inspection establishes reconciliation and regression evidence, not a completed
independent Stage2 security review. The authoring/review roles are not newly separated
by this packet. The Stage2 design at unpublished `1a8fa68` is useful context but does
not authorize a provider-flow change, identity provisioning or deployment.

## Reproduced tests

- `python3 -m unittest discover -s ops/credential-broker -p 'test_*.py'`: 76 pass.
- Existing Python 3.12 environment, `services/aster-agent/test_broker_*.py`: 10 pass.
- Same environment, `scripts/aster-adaptive/test_*.py`: 56 pass.

The bridge run emitted the existing Starlette/httpx deprecation warning; no dependency
was installed or upgraded. These checks ran on local synthetic state. Historical
M2/M3 source hashes and timings remain dated evidence and must not be relabeled as
measurements of this newer integrated source. The [manifest](M1-reconciliation-manifest.json)
pins the inspected source and test counts.

## Next safe action and gated action

Next local work: map the two offline contract candidates and their distinct schema,
source-engine and eligibility guarantees, using pinned snapshots and synthetic
conformance. Preserve both histories and the other continuation's work. This can
advance independently of unresolved Stage2 human authentication.

For Stage2, prepare a narrowly scoped, source-local assurance-verification procedure
with the owning continuation; the actual fresh login and any provider test-flow
mutation need explicit scope and human participation. Do not ask for deployment
approval until mapping, trust decision, compatible bundle and recovery impact are
concrete. M1 and connected pilot gates remain open. This turn creates no new service,
network, inventory, monitoring or credential fact requiring operational updates.
Local reconciliation/publication remains pending explicit push authorization.
