# D3 deployment preparation — native UI and narrow kill-switch read

## Verified current deployment facts

Read-only direct SSH on LXC 104 confirms:

- `aster` is UID 997, primary group `aster`, supplementary group
  `hlabroker-approvers`; it is not a member of `hlabroker-clients`.
- `/run/homelab-broker/approval.sock` is 0660, `hlabroker:hlabroker-approvers`.
  The general `mcp.sock` is 0660, `hlabroker:hlabroker-clients`.
- `homelab-broker-approval.service` is active and runs as `hlabroker`.
- Installed approval-service SHA-256 is
  `c0f2e5fa5585e3867fad760b9dfa4dd917d3116a80dbf7a9d5b420372ce1d6a4`,
  exactly matching the pre-change repository source.
- Installed Aster gateway SHA-256 remains
  `24bdc580f074003fe8fbb064c0f5effbded9f15a33e0a8ef07b37075d6511fb0`.

Do not widen Aster's groups or impersonate a human approver to read the global
kill switch. That is unnecessary authority for a boolean status check.

## Local implementation and validation

The approval service now has one candidate peer-authenticated read operation:
exact request `{"method":"automation.status"}` returns only `global_enabled`.
The existing kernel peer check still runs first. Extra fields cannot select the
new branch. Every existing management/approval method still requires its human
actor (and existing passkey/freshness where applicable). This is not a token
issuance or permission grant API.

The new local `BrokerGate` requests only that boolean through the existing
approval socket. It has no positive cache and denies on unavailable, malformed,
oversized or non-boolean responses. Wiring it as the worker identity verifier's
`permitted` callback remains part of the gateway assembly; it is not active yet.
The future worker treats loss of its control connection as uncertainty and
attempts interruption. That cannot guarantee instant cessation of remote compute.

Native Companion now has a build-disabled **Codex requests** view. It lists only
assigned owner jobs, displays the exact completed answer as literal text, polls
status while open and offers request-stop without claiming interruption. It
cannot create or retry jobs, approve work or gain tools. Answers are not written
to app preferences. The existing Authentik user-token path is reused. Candidate
gateway list routes disclose only the authenticated owner's IDs/states.

Validation: 147 delegation Python tests, all 84 broker tests (including 12 approval-service socket tests),
26 native Swift tests and five JS renderer scenarios pass. Swift build succeeded
using the existing toolchain with scratch output in `/private/tmp`; the installed
app was not replaced. No live visual interaction test is claimed. The initial
sandboxed Swift build could not invoke its nested sandbox; a platform-authorised
local build/test succeeded without dependency installation.

## Exact approval gate — deploy only the status-read addition

Approve updating **only** `/opt/homelab-broker/broker_approval_service.py` on
LXC 104 from the current baseline above to repository candidate SHA-256:

`eeefdf23fd08602f6d78a8499a81a7db04465ae78fa3ab3806f2d7f8a385f043`

Then restart **only** `homelab-broker-approval.service` and perform bounded
read-only/denial validation. This may briefly interrupt the Companion approval
inbox and approval actions. It does not restart Aster, the general broker,
OpenBao or Authentik, and does not toggle the global switch.

Execution procedure:

1. Recheck current code hash, active unit and socket ownership. Stop on drift.
   Confirm no approval action is in flight using non-secret broker metadata.
2. Create a fresh root-owned 0700 checkpoint directory
   `/var/lib/homelab-broker/checkpoints/aster-status-20261006`, preserving the
   original source's bytes, ownership and mode plus non-secret baseline hashes.
   Do not overwrite an existing checkpoint. No credential backup/dump is needed.
3. Stage exactly the reviewed source to a temporary file in the same installation
   directory, verify its SHA-256, compile without running it, preserve original
   ownership/mode, and atomically replace the target.
4. Restart the approval service once. Verify it is active and the socket retains
   its existing owner/group/mode. As the existing `aster` UID, query only
   `automation.status`; expect exactly one boolean. Verify the global setting
   matches its pre-change read-only value without toggling it.
5. Verify a non-Aster UID is denied. As Aster, verify actor-less
   `management.snapshot` and actor-less `management.global-enabled` are denied
   before any state change. Do not submit or approve a real privileged request.
6. Recheck Aster health/source hash and record only sanitized metadata. Existing
   human approval workflow gets local regression coverage; live human passkey
   approval is not silently simulated by constructing an actor identity.

Rollback on changed service behavior, failed health/denials or source mismatch:
restore the exact checkpoint source with its original metadata, restart only
the approval service and verify the original hash/active state/socket. If rollback
fails, stop and report the narrow outage; do not broaden permissions to recover.
Expected interruption is seconds, not an SLA. Keep the checkpoint and audit.

This approval does **not** authorize installing/enabling the new Companion view,
mounting delegation routes, creating credentials, changing broker registrations
or vault policy, toggling emergency stop, running a model or pushing Git.

## Integration impacts and next work

No new IP, DNS, certificate, firewall rule, port, hardware, recurring schedule or
Homepage tile. Existing LXC 104 backup scope covers the code; the specific source
checkpoint supports immediate rollback. Existing service monitoring remains the
health signal. Document successful deployment in broker operational references;
keep the native UI and delegation disabled until their own deployment gate.

Next, finish the permanent credential custody and gateway/worker configuration,
mount the existing routes behind a disabled feature flag, and prepare the first
native UI validation. The separate [credential registry candidate](D3-credential-registry-candidate.md)
records unresolved custody facts; they are not a reason to reuse human or Forgejo
credentials. The first live stop-reporting failure remains a residual issue even
though the subsequent approved run confirmed interruption.

Approval is required by repository AGENTS.md for the remote file update/restart.
The exact change, live baseline, regression checks and rollback are prepared;
await this bounded approval before deployment.
