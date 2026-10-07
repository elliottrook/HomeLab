# D3 gateway assembly and custody checkpoint — 2026-10-06

**LOCAL CANDIDATE, NOT DEPLOYED.** This follows the completed
[broker status-read deployment](D3-broker-deployment-result-2026-10-06.md).

## Implemented locally

`services/aster-agent/delegation/gateway_assembly.py` composes the existing
gateway ledger, worker identity verifier, broker status callback and owner routes.
The production Aster application does not import or mount it yet.

- Default-disabled assembly registers no endpoints, opens no state and obtains
  no credentials. Enabling requires explicit boolean configuration, a fixed
  workload subject and a supplied custody callback. Those inputs are integration
  requirements, not permission grants.
- FastAPI router lifespan owns a private 0700 state directory, 0600 database and
  process lock. Insecure state or symlink paths are rejected; a second process
  cannot own the same ledger. Startup/shutdown never requeue accepted work or
  assert remote cancellation. Saved receipts are historical evidence, not liveness.
- Routes reuse the existing owner/worker checks. No public enqueue, approval,
  model launch, credential issuance or automatic dispatch endpoint was added.
- Worker authentication checks the broker before and after introspection. Socket
  and custody callbacks execute off the event loop; exceptions/non-boolean gate
  results deny access. This prevents these synchronous callbacks from blocking
  the household request loop, but does not prove overall production latency.
- Human job status remains readable when worker access is disabled. Disabling
  automation does not remove human visibility or recovery access.

## Validation and limits

152 delegation tests pass with the existing pinned Python 3.11 test environment.
New tests cover disabled startup, private permissions, exclusive ownership,
durable accepted receipts without replay, insecure/symlink state refusal, real
local Unix-socket status reads through composed HTTP routes, switch disable and
socket outage, plus callback exceptions/non-boolean denials. Authentik responses
and identities remain fixtures; this was not a new production authentication test.
No model inference, dependencies, production changes or push occurred.

Read-only `systemctl show` on OpenBao LXC 117 reports active/running. That proves
service health only. Repository operational evidence records revoked bootstrap
tokens and a human-held root-ceremony credential requiring two recovery shares.
No alternative current administrative identity is established by this evidence.
No credential store or recovery material was inspected.

## Remaining critical path

1. Prepare the exact credential provisioning/rotation implementation, using the
   [custody candidate](D3-credential-registry-candidate.md). Existing Forgejo roles
   and human Companion tokens must not be reused. Human participation in the
   approved vault recovery procedure may be necessary; never request shares in chat.
2. Supply reviewed custody adapters and mount the candidate through the existing
   gateway lifecycle, remaining disabled initially. Gateway runtime identity must
   be the existing Aster identity; no added broker client group is required.
3. Prepare Mac lifecycle/configuration and bounded assignment delivery. A native
   status view and worker primitives alone do not implement a usable assistant.
4. Request one concrete integration deployment approval covering exact files,
   identities, credentials, service restarts, validation and rollback. Existing
   approvals do not authorize this. No additional authentication-only or model
   experiment is required merely to postpone this integration work.

Residual issue: the first live stop-reporting failure remains unexplained. The
successful later stop and current local tests do not establish production stopping
reliability. Qualification requires honest uncertainty and no automatic resend.
