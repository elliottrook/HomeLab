# M1 live approval-boundary recheck — 2026-10-11

**Decision: Stage2 remains HOLD.** This is read-only metadata and source-shape
reconciliation. No approval request, credential, socket call, service restart,
policy change, or permission change was made.

## Verified current state

Read-only commands through Proxmox into LXC 104 found:

| Item | Observed result |
|---|---|
| Approval socket | `/run/homelab-broker/approval.sock`, owner `hlabroker`, group `hlabroker-approvers`, mode `0660` |
| Socket parent | `/run/homelab-broker`, owner/group `hlabroker`, mode `0755` |
| `aster` account | UID 997, primary group `aster`, supplementary group `hlabroker-approvers` |
| Approval unit | Active; `User=hlabroker`, `Group=hlabroker`, supplementary group `hlabroker-approvers`; `StateDirectory=homelab-broker` |
| Deployed Companion approval bridge | SHA-256 `cf37fb1782c875622155b50d7b69f31b7c9acc2c30f7881f5da9b4a6538dd324`, matching `services/aster-agent/broker_approvals.py` in this branch |
| Deployed broker approval source | SHA-256 `eeefdf23fd08602f6d78a8499a81a7db04465ae78fa3ab3806f2d7f8a385f043`, **different** from repository `ops/credential-broker/broker_approval_service.py` (`4a9f8d0de622a06e7dd9fe32279b22d71a3dbe4f220a77891684c34e30756631`) |

A source-local AST digest comparison found the deployed and tracked
`ApprovalHandler.handle`, `_actor`, and `_fresh_actor` method source segments
identical. `dispatch` differs: the tracked candidate includes
`management.capability-revoke`, while the deployed method's string-literal
method set does not. This limited comparison does **not** prove the remaining
dispatch semantics or the full live service equal the candidate. No raw
configuration, token, subject hash, database row, or request content was read.

## Architectural implication

The socket mode and `aster` group membership make access by the Aster process
plausible; the tracked approval unit also names `aster` as its configured peer.
This is **not** a direct socket-connection test or proof that a forged approval
occurred. It confirms that the present deployment does not establish the
intended separation between AI-facing Aster and human approval authority.
The broker's subject allowlist and freshness checks remain useful controls,
but cannot independently authenticate who supplied actor metadata when the
allowed Aster process builds the socket request.

Before any Stage2 rollout or connected Codex tool, reconcile the exact live
broker dispatch and unit configuration, verify a session-derived passkey
assurance signal or explicit step-up, and test a separate ingress identity
whose UID alone may reach the approval socket. The plan must preserve human
break-glass and prove that ordinary Aster functions survive approval-ingress
failure. Do not remove `aster` from the current group in isolation: that would
break the existing Companion approval path before its replacement is ready.
