# D3 — Local vertical handoff fixture, 2026-10-06

## Result and limits

VERIFIED LOCAL: 110 Python tests and five Companion renderer scenarios pass.
Eight new integration cases connect immutable gateway delivery, worker admission,
private runtime dispatch state, Session events, authenticated-snapshot recovery
and owner-bound final-answer delivery. The provider exchange is simulated; this
is not a live Companion-to-Codex test or sysadmin qualification.

`execute_admitted` is disabled by default. A first durable admission may prepare
one turn; repeated delivery can only reconcile. Transport failure after dispatch
retains uncertainty. A missing turn acknowledgement is never guessed from a
snapshot. Tests cover acknowledgement loss, terminal-event loss, runtime restart,
gateway restart, wrong owner/worker, altered answer and incomplete exchange.

The gateway accepts final text only after a completed receipt with matching
SHA-256, worker and delivery identity. It returns text verbatim to the recorded
owner. Text is held in bounded process memory, not SQLite. Reads purge entries
older than 15 minutes; this is logical expiry, not guaranteed timed memory erasure.
A gateway restart loses text but retains the completion digest; authenticated
recovery restores it without another model turn. Duplicate-suppression records
are retained. Provider-side conversation retention is separate and unchanged.

No router mounted, daemon installed, credential issued, new inference run,
production service changed or Git remote written.

## Identity findings and candidate boundary

REPOSITORY INTENT / IMPLEMENTATION EVIDENCE, not fresh deployment verification:

- [AI-PAM operational reference](../../../reference/AI-PAM-Operational-Reference.md)
  and `ops/credential-broker/README.md` describe kernel-peer-bound Unix sockets,
  probation, payload-bound approvals and fail-closed issuance. That local caller
  identity cannot directly identify a remote Mac worker.
- `services/authentik-blueprints/aster-companion-provider-app.yaml` defines a
  public user client with authorization-code/refresh grants and a Jason policy
  binding. It is not a machine credential and must not be repurposed as one.
- The prior live gateway checks remain dated evidence. No current machine
  authentication deployment is established by these repository files.

PROPOSAL: a distinct probationary identity `aster-codex-worker-mac`, eligible
only for its assigned offers, correlated receipts and digest-bound result
delivery. It cannot create jobs, impersonate owners, approve requests, alter
policy, obtain target credentials or enumerate other workers' work. Authenticated
transport identity must be supplied by verification, never request JSON.

The gateway remains on LXC 104; the worker connects outward from the Mac.
Codex subscription custody remains with the existing Mac login. The worker's
gateway credential is separate. Exact authentication mechanism, issuer,
audience, custody identifier, rotation and revocation propagation remain UNKNOWN
until implementation/deployment metadata is checked. Do not invent an OpenBao
path or issue a broad token merely to close this gap.

## Next bounded work and deployment gate

1. Inspect non-secret deployed Authentik/AI-PAM capability metadata and select a
   supported workload authentication mechanism. Complete the existing AI-PAM
   registry template with exact custody, scope, revocation and outage behavior.
2. Wire the existing outbound worker transport and gateway result/status paths
   around this tested integration seam. Verify thread scope/model before calling
   it; the injected exchange does not independently validate provider isolation.
3. Cover authenticated denial, revocation, timeout, private ledger ownership and
   owner-result retrieval using local transport fixtures. Do not introduce a
   second harness or reopen the local-Qwen qualification trial.
4. Present one concrete deployment/canary proposal: exact changed files and
   identity, one fictional request, model/reasoning setting, no tools, bounded
   duration, stop procedure, rollback and success criteria. Existing approval
   covered the historical D2 turn only; deployment and a new cloud turn require
   their own explicit authorization under the governing project.

The useful next milestone is one answer visible in Aster through a verified
worker connection. Further isolated abstractions alone do not complete D3.
